use agentbench::agent::{claude_args_with, AgentKind};
use agentbench::config::Config;
use agentbench::proxy::Proxy;
use agentbench::report;
use agentbench::results;
use agentbench::runner::{run_attempt, validate_task, RunOpts};
use agentbench::task::load_tasks;
use anyhow::{bail, Context, Result};
use clap::{Parser, Subcommand};
use std::path::{Path, PathBuf};
use std::time::Duration;

#[derive(Parser)]
#[command(name = "agentbench", about = "Benchmark harness for coding agents")]
struct Cli {
    #[command(subcommand)]
    cmd: Cmd,
}

#[derive(Subcommand)]
enum Cmd {
    /// List the tasks.
    List {
        #[arg(long, default_value = "bench.toml")]
        config: PathBuf,
    },
    /// Check every task: the fixture must fail its check, the reference solution must pass.
    Validate {
        #[arg(long, default_value = "bench.toml")]
        config: PathBuf,
    },
    /// Run arms x tasks x samples, appending one JSON line per attempt.
    Run {
        #[arg(long, default_value = "bench.toml")]
        config: PathBuf,
        /// Comma-separated arm names (default: all). Run one arm at a time when
        /// each arm needs its own tierline instance.
        #[arg(long, value_delimiter = ',')]
        arms: Vec<String>,
        /// Comma-separated task ids (default: all).
        #[arg(long, value_delimiter = ',')]
        tasks: Vec<String>,
        /// Only tasks carrying this tag in task.toml (e.g. hard-v2).
        #[arg(long)]
        tag: Option<String>,
        #[arg(long)]
        samples: Option<u32>,
        /// claude | fake-solve | fake-noop
        #[arg(long, default_value = "claude")]
        agent: String,
        #[arg(long, default_value = "results/results.jsonl")]
        out: PathBuf,
        /// Required for `--agent claude`, which spends real money.
        #[arg(long)]
        yes: bool,
    },
    /// Summarize a results file: success rate with CI, cost, cost per success.
    Report {
        #[arg(long, default_value = "bench.toml")]
        config: PathBuf,
        #[arg(long, default_value = "results/results.jsonl")]
        results: PathBuf,
        #[arg(long, default_value = "report")]
        out: PathBuf,
        #[arg(long, default_value_t = 10_000)]
        resamples: usize,
        #[arg(long, default_value_t = 42)]
        seed: u64,
    },
}

fn base_dir(config: &Path) -> PathBuf {
    config
        .parent()
        .filter(|p| !p.as_os_str().is_empty())
        .unwrap_or(Path::new("."))
        .to_path_buf()
}

#[tokio::main]
async fn main() -> Result<()> {
    match Cli::parse().cmd {
        Cmd::List { config } => {
            let cfg = Config::load(&config)?;
            for t in load_tasks(&base_dir(&config).join(&cfg.run.tasks_dir))? {
                println!(
                    "{:<24} {:<8} {}",
                    t.id(),
                    t.meta.difficulty,
                    t.meta.category
                );
            }
        }
        Cmd::Validate { config } => {
            let cfg = Config::load(&config)?;
            let tasks = load_tasks(&base_dir(&config).join(&cfg.run.tasks_dir))?;
            let mut bad = 0;
            for t in &tasks {
                let (fixture, solution) = validate_task(t, &cfg.run.python).await?;
                let ok = !fixture && solution;
                println!(
                    "{:<24} fixture_fails={} solution_passes={} {}",
                    t.id(),
                    !fixture,
                    solution,
                    if ok { "ok" } else { "BAD" }
                );
                bad += !ok as u32;
            }
            if bad > 0 {
                bail!("{bad} task(s) failed validation");
            }
        }
        Cmd::Run {
            config,
            arms,
            tasks,
            tag,
            samples,
            agent,
            out,
            yes,
        } => {
            let cfg = Config::load(&config)?;
            let base = base_dir(&config);
            let kind =
                AgentKind::parse(&agent).with_context(|| format!("unknown agent {agent:?}"))?;
            let mut all = load_tasks(&base.join(&cfg.run.tasks_dir))?;
            if let Some(tag) = &tag {
                all.retain(|t| t.meta.tags.iter().any(|x| x == tag));
            }
            if !tasks.is_empty() {
                all.retain(|t| tasks.iter().any(|id| id == t.id()));
            }
            let arm_list: Vec<_> = if arms.is_empty() {
                cfg.arms.iter().collect()
            } else {
                arms.iter()
                    .map(|n| {
                        cfg.arm(n)
                            .with_context(|| format!("no arm {n:?} in config"))
                    })
                    .collect::<Result<_>>()?
            };
            let samples = samples.unwrap_or(cfg.run.samples);
            let done = results::read(&out)?;
            let total = arm_list.len() * all.len() * samples as usize;
            println!(
                "plan: {} arms x {} tasks x {} samples = {} attempts ({})",
                arm_list.len(),
                all.len(),
                samples,
                total,
                agent
            );
            if kind == AgentKind::Claude {
                for arm in &arm_list {
                    println!(
                        "{}: {} {:?}",
                        arm.name,
                        cfg.run.claude_bin,
                        claude_args_with(
                            "<prompt>",
                            arm.model.as_deref(),
                            arm.is_clean(&cfg.run),
                            arm.effort.as_deref()
                        )
                    );
                }
                if !yes {
                    bail!("this launches real `claude` sessions; re-run with --yes to proceed");
                }
            }
            let opts = RunOpts {
                agent: kind,
                python: &cfg.run.python,
                claude_bin: &cfg.run.claude_bin,
                timeout: Duration::from_secs(cfg.run.timeout_secs),
                clean: cfg.run.clean,
            };
            // Arm by arm, strictly sequential: the tierline join relies on it.
            for arm in arm_list {
                // The proxy (if any) lives exactly as long as this block: it is killed
                // on success, on error (drop) and on Ctrl-C.
                let proxy = match &arm.proxy {
                    Some(p) => Some(Proxy::start(p, &base).await?),
                    None => None,
                };
                let mut arm_run = arm.clone();
                if let Some(p) = &proxy {
                    arm_run
                        .env
                        .insert("ANTHROPIC_BASE_URL".into(), p.base_url.clone());
                }
                let body = async {
                    for sample in 0..samples {
                        for t in &all {
                            if done.iter().any(|d| {
                                d.arm == arm.name && d.task == t.id() && d.sample == sample
                            }) {
                                continue;
                            }
                            let a = run_attempt(t, &arm_run, sample, &opts).await?;
                            println!(
                                "{} {} #{} {} ({} ms)",
                                a.arm,
                                a.task,
                                a.sample,
                                if a.pass { "pass" } else { "FAIL" },
                                a.duration_ms
                            );
                            results::append(&out, &a)?;
                        }
                    }
                    Ok::<(), anyhow::Error>(())
                };
                let r = tokio::select! {
                    r = body => r,
                    _ = tokio::signal::ctrl_c() => Err(anyhow::anyhow!("interrupted")),
                };
                if let Some(p) = proxy {
                    p.stop().await;
                }
                r?;
            }
        }
        Cmd::Report {
            config,
            results: rpath,
            out,
            resamples,
            seed,
        } => {
            let cfg = Config::load(&config)?;
            let attempts = results::read(&rpath)?;
            if attempts.is_empty() {
                bail!("no attempts in {}", rpath.display());
            }
            let rows = report::build(&cfg, &attempts, &base_dir(&config), resamples, seed)?;
            let md = report::markdown(&rows, resamples);
            print!("{md}");
            std::fs::create_dir_all(&out)?;
            std::fs::write(out.join("report.md"), &md)?;
            std::fs::write(out.join("report.svg"), report::svg(&rows))?;
            println!("wrote {}/report.md and report.svg", out.display());
        }
    }
    Ok(())
}
