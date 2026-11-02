use agentbench::agent::{claude_args, parse_reported_cost, AgentKind};
use agentbench::config::{Arm, Config};
use agentbench::report::{markdown, summarize_arm, svg};
use agentbench::results::{self, attribute, Attempt, TierlineRecord, Usage};
use agentbench::runner::{run_attempt, validate_task, RunOpts};
use agentbench::stats::{bootstrap_ci, Rng};
use agentbench::task::{load_task, load_tasks};
use std::collections::BTreeMap;
use std::path::{Path, PathBuf};
use std::time::Duration;

fn tasks_dir() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR")).join("tasks")
}

fn arm(name: &str) -> Arm {
    Arm {
        name: name.into(),
        model: None,
        env: BTreeMap::new(),
        tierline_log: None,
    }
}

fn opts<'a>(agent: AgentKind, claude_bin: &'a str, secs: u64) -> RunOpts<'a> {
    RunOpts {
        agent,
        python: "python3",
        claude_bin,
        timeout: Duration::from_secs(secs),
    }
}

fn attempt(arm: &str, task: &str, sample: u32, pass: bool, start: u128, end: u128) -> Attempt {
    Attempt {
        arm: arm.into(),
        task: task.into(),
        sample,
        pass,
        duration_ms: (end - start) as u64,
        exit_code: Some(0),
        timed_out: false,
        check_exit_code: Some(if pass { 0 } else { 1 }),
        start_ms: start,
        end_ms: end,
        agent_cost_usd: None,
    }
}

// ---- task loading ----

#[test]
fn loads_fifteen_valid_tasks_with_a_difficulty_spread() {
    let tasks = load_tasks(&tasks_dir()).unwrap();
    assert_eq!(tasks.len(), 15);
    let count = |d: &str| tasks.iter().filter(|t| t.meta.difficulty == d).count();
    assert_eq!(count("trivial"), 1);
    assert!(count("easy") >= 3);
    assert!(count("medium") >= 5);
    assert_eq!(count("hard"), 4);
    let mut ids: Vec<_> = tasks.iter().map(|t| t.id().to_string()).collect();
    let sorted = ids.clone();
    ids.sort();
    assert_eq!(ids, sorted, "tasks come back sorted by id");
}

#[test]
fn rejects_malformed_tasks() {
    let tmp = tempfile::tempdir().unwrap();
    let d = tmp.path().join("t1");
    std::fs::create_dir_all(d.join("repo")).unwrap();
    std::fs::create_dir_all(d.join("solution")).unwrap();
    std::fs::write(d.join("check.py"), "").unwrap();
    let write = |s: &str| std::fs::write(d.join("task.toml"), s).unwrap();

    write("id = \"t1\"\ncategory = \"x\"\ndifficulty = \"easy\"\nprompt = \"p\"\n");
    assert!(load_task(&d).is_ok());
    write("id = \"other\"\ncategory = \"x\"\ndifficulty = \"easy\"\nprompt = \"p\"\n");
    assert!(load_task(&d)
        .unwrap_err()
        .to_string()
        .contains("does not match"));
    write("id = \"t1\"\ncategory = \"x\"\ndifficulty = \"brutal\"\nprompt = \"p\"\n");
    assert!(load_task(&d)
        .unwrap_err()
        .to_string()
        .contains("difficulty"));
    write("id = \"t1\"\ncategory = \"x\"\ndifficulty = \"easy\"\nprompt = \" \"\n");
    assert!(load_task(&d)
        .unwrap_err()
        .to_string()
        .contains("empty prompt"));
    write("id = \"t1\"\ncategory = \"x\"\ndifficulty = \"easy\"\nprompt = \"p\"\n");
    std::fs::write(d.join("repo/check.py"), "").unwrap();
    assert!(load_task(&d)
        .unwrap_err()
        .to_string()
        .contains("must not live in repo"));
}

#[test]
fn no_fixture_ships_its_check_or_solution() {
    for t in load_tasks(&tasks_dir()).unwrap() {
        assert!(!t.repo_dir().join("check.py").exists(), "{}", t.id());
        assert!(!t.repo_dir().join("solution").exists(), "{}", t.id());
        assert!(!t.repo_dir().join("task.toml").exists(), "{}", t.id());
    }
}

// ---- reference solutions ----

#[tokio::test]
async fn every_fixture_fails_and_every_solution_passes() {
    for t in load_tasks(&tasks_dir()).unwrap() {
        let (fixture, solution) = validate_task(&t, "python3").await.unwrap();
        assert!(!fixture, "{}: unmodified fixture passed its check", t.id());
        assert!(solution, "{}: reference solution failed its check", t.id());
    }
}

// ---- agent adapters ----

#[test]
fn claude_command_line_is_headless_and_non_interactive() {
    assert_eq!(
        claude_args("do it", None),
        [
            "-p",
            "do it",
            "--dangerously-skip-permissions",
            "--output-format",
            "json",
            "--no-session-persistence"
        ]
    );
    let with_model = claude_args("do it", Some("opus"));
    assert_eq!(&with_model[6..], ["--model", "opus"]);
}

#[test]
fn parses_agent_reported_cost() {
    assert_eq!(
        parse_reported_cost(r#"{"type":"result","total_cost_usd":0.0421}"#),
        Some(0.0421)
    );
    assert_eq!(parse_reported_cost("not json"), None);
    assert_eq!(parse_reported_cost(r#"{"result":"x"}"#), None);
}

#[cfg(unix)]
fn fake_claude(dir: &Path, body: &str) -> PathBuf {
    use std::os::unix::fs::PermissionsExt;
    let p = dir.join("fake-claude");
    std::fs::write(&p, format!("#!/bin/sh\n{body}\n")).unwrap();
    std::fs::set_permissions(&p, std::fs::Permissions::from_mode(0o755)).unwrap();
    p
}

/// The agent must not see check.py, and must receive the arm's env and flags.
/// A shell script stands in for the `claude` binary; no model is involved.
#[cfg(unix)]
#[tokio::test]
async fn agent_does_not_see_check_files_and_gets_arm_env() {
    let tmp = tempfile::tempdir().unwrap();
    let record = tmp.path().join("record.txt");
    let bin = fake_claude(
        tmp.path(),
        &format!(
            "ls -A > '{0}'\necho \"BASE=$ANTHROPIC_BASE_URL\" >> '{0}'\necho \"ARGS=$*\" >> '{0}'\necho '{{\"total_cost_usd\":0.5}}'",
            record.display()
        ),
    );
    let task = load_tasks(&tasks_dir()).unwrap().remove(0);
    let mut a = arm("a");
    a.model = Some("opus".into());
    a.env
        .insert("ANTHROPIC_BASE_URL".into(), "http://127.0.0.1:9".into());
    let got = run_attempt(
        &task,
        &a,
        0,
        &opts(AgentKind::Claude, bin.to_str().unwrap(), 30),
    )
    .await
    .unwrap();

    let rec = std::fs::read_to_string(&record).unwrap();
    assert!(rec.contains("pager.py"), "fixture is present: {rec}");
    assert!(!rec.contains("check.py"), "agent saw check.py: {rec}");
    assert!(!rec.contains("solution"), "agent saw the solution: {rec}");
    assert!(rec.contains("BASE=http://127.0.0.1:9"));
    assert!(rec.contains("-p "));
    assert!(rec.contains("--dangerously-skip-permissions"));
    assert!(rec.contains("--model opus"));
    // The fake changed nothing, so the check (copied in afterwards) fails.
    assert!(!got.pass);
    assert_eq!(got.exit_code, Some(0));
    assert_eq!(got.agent_cost_usd, Some(0.5));
    assert!(got.end_ms >= got.start_ms);
}

#[cfg(unix)]
#[tokio::test]
async fn agent_timeout_is_recorded_and_fails_the_attempt() {
    let tmp = tempfile::tempdir().unwrap();
    let bin = fake_claude(tmp.path(), "sleep 30");
    let task = load_tasks(&tasks_dir()).unwrap().remove(0);
    let t0 = std::time::Instant::now();
    let got = run_attempt(
        &task,
        &arm("a"),
        0,
        &opts(AgentKind::Claude, bin.to_str().unwrap(), 1),
    )
    .await
    .unwrap();
    assert!(got.timed_out && !got.pass && got.exit_code.is_none());
    assert!(t0.elapsed() < Duration::from_secs(20));
}

#[tokio::test]
async fn fake_agents_solve_or_do_nothing() {
    let task = load_tasks(&tasks_dir()).unwrap().remove(0);
    let solve = run_attempt(
        &task,
        &arm("a"),
        3,
        &opts(AgentKind::FakeSolve, "claude", 10),
    )
    .await
    .unwrap();
    let noop = run_attempt(
        &task,
        &arm("a"),
        4,
        &opts(AgentKind::FakeNoop, "claude", 10),
    )
    .await
    .unwrap();
    assert!(solve.pass && !noop.pass);
    assert_eq!((solve.sample, noop.sample), (3, 4));
}

// ---- full run through the CLI with the fake agent ----

fn bench_toml(dir: &Path) -> PathBuf {
    let p = dir.join("bench.toml");
    let toml = format!(
        "[run]\nsamples = 2\ntasks_dir = {:?}\n\n[[arm]]\nname = \"alpha\"\n[arm.env]\nANTHROPIC_BASE_URL = \"http://127.0.0.1:1\"\n\n[[arm]]\nname = \"beta\"\n",
        tasks_dir().to_str().unwrap()
    );
    std::fs::write(&p, toml).unwrap();
    p
}

fn cli(args: &[&str]) -> std::process::Output {
    std::process::Command::new(env!("CARGO_BIN_EXE_agentbench"))
        .args(args)
        .output()
        .unwrap()
}

#[test]
fn fake_agent_full_run_resume_and_report() {
    let tmp = tempfile::tempdir().unwrap();
    let cfg = bench_toml(tmp.path());
    let out = tmp.path().join("results/r.jsonl");
    let (c, o) = (cfg.to_str().unwrap(), out.to_str().unwrap());

    let r = cli(&[
        "run",
        "--config",
        c,
        "--agent",
        "fake-solve",
        "--out",
        o,
        "--arms",
        "alpha",
        "--samples",
        "1",
    ]);
    assert!(r.status.success(), "{}", String::from_utf8_lossy(&r.stderr));
    let r = cli(&[
        "run",
        "--config",
        c,
        "--agent",
        "fake-noop",
        "--out",
        o,
        "--arms",
        "beta",
        "--samples",
        "1",
    ]);
    assert!(r.status.success());

    let attempts = results::read(&out).unwrap();
    assert_eq!(attempts.len(), 30);
    assert!(attempts.iter().filter(|a| a.arm == "alpha").all(|a| a.pass));
    assert!(attempts.iter().filter(|a| a.arm == "beta").all(|a| !a.pass));

    // Re-running is a no-op: finished (arm, task, sample) triples are skipped.
    let r = cli(&[
        "run",
        "--config",
        c,
        "--agent",
        "fake-solve",
        "--out",
        o,
        "--arms",
        "alpha",
        "--samples",
        "1",
    ]);
    assert!(r.status.success());
    assert_eq!(results::read(&out).unwrap().len(), 30);

    let rep = tmp.path().join("rep");
    let r = cli(&[
        "report",
        "--config",
        c,
        "--results",
        o,
        "--out",
        rep.to_str().unwrap(),
    ]);
    assert!(r.status.success(), "{}", String::from_utf8_lossy(&r.stderr));
    let md = std::fs::read_to_string(rep.join("report.md")).unwrap();
    assert!(
        md.contains("| alpha | 15 | 15 | 100.0% (15/15) | 100.0% to 100.0% |"),
        "{md}"
    );
    assert!(
        md.contains("| beta | 15 | 15 | 0.0% (0/15) | 0.0% to 0.0% |"),
        "{md}"
    );
    let svg = std::fs::read_to_string(rep.join("report.svg")).unwrap();
    assert!(svg.starts_with("<svg") && svg.contains("alpha") && svg.contains("beta"));
}

#[test]
fn real_agent_requires_explicit_confirmation() {
    let tmp = tempfile::tempdir().unwrap();
    let cfg = bench_toml(tmp.path());
    let out = tmp.path().join("r.jsonl");
    let r = cli(&[
        "run",
        "--config",
        cfg.to_str().unwrap(),
        "--out",
        out.to_str().unwrap(),
    ]);
    assert!(!r.status.success());
    assert!(String::from_utf8_lossy(&r.stderr).contains("--yes"));
    assert!(!out.exists(), "nothing may run without --yes");
}

// ---- config ----

#[test]
fn config_validation() {
    assert!(Config::parse("").is_err(), "no arms");
    assert!(Config::parse("[[arm]]\nname=\"a\"\n[[arm]]\nname=\"a\"\n").is_err());
    assert!(Config::parse("[run]\nsamples=0\n[[arm]]\nname=\"a\"\n").is_err());
    let c = Config::parse("[[arm]]\nname=\"a\"\nmodel=\"opus\"\n[arm.env]\nK=\"v\"\n").unwrap();
    assert_eq!(c.run.samples, 2);
    assert_eq!(c.arm("a").unwrap().env["K"], "v");
    // The shipped config parses and has the three documented arms.
    let shipped = Config::load(&Path::new(env!("CARGO_MANIFEST_DIR")).join("bench.toml")).unwrap();
    let names: Vec<_> = shipped.arms.iter().map(|a| a.name.as_str()).collect();
    assert_eq!(names, ["opus-direct", "tierline-off", "tierline-route"]);
}

// ---- statistics ----

#[test]
fn rng_is_deterministic() {
    let mut a = Rng::new(42);
    let mut b = Rng::new(42);
    let xs: Vec<u64> = (0..5).map(|_| a.next_u64()).collect();
    assert_eq!(xs, (0..5).map(|_| b.next_u64()).collect::<Vec<_>>());
    // SplitMix64 reference output for seed 0.
    assert_eq!(Rng::new(0).next_u64(), 0xE220_A839_7B1D_CDAF);
}

#[test]
fn bootstrap_is_seeded_and_sane() {
    let rates = [1.0, 1.0, 0.5, 0.0, 1.0, 0.0, 1.0, 0.5];
    let a = bootstrap_ci(&rates, 10_000, 42);
    assert_eq!(
        a,
        bootstrap_ci(&rates, 10_000, 42),
        "same seed, same interval"
    );
    assert_ne!(Rng::new(42).next_u64(), Rng::new(43).next_u64());
    let (m, lo, hi) = a;
    assert!((m - 0.625).abs() < 1e-12);
    assert!(lo < m && m < hi && lo >= 0.0 && hi <= 1.0);
    // Bootstrap SE is about sd/sqrt(n) ~ 0.14 here, so the interval is roughly +-0.28.
    assert!((0.25..0.45).contains(&lo), "lo = {lo}");
    assert!((0.78..0.95).contains(&hi), "hi = {hi}");
}

#[test]
fn bootstrap_degenerate_cases() {
    assert_eq!(bootstrap_ci(&[1.0; 6], 1000, 1), (1.0, 1.0, 1.0));
    assert_eq!(bootstrap_ci(&[0.0; 6], 1000, 1), (0.0, 0.0, 0.0));
    assert_eq!(bootstrap_ci(&[], 1000, 1), (0.0, 0.0, 0.0));
    // One task: nothing to resample, so the interval collapses to the point.
    assert_eq!(bootstrap_ci(&[0.5], 1000, 1), (0.5, 0.5, 0.5));
}

// ---- tierline join and report math ----

#[test]
fn attributes_tierline_records_by_time_window() {
    let line = |ts: u128, cost: &str| {
        format!(
            r#"{{"ts_ms":{ts},"method":"POST","path":"/v1/messages","status":200,"model":"m","input_tokens":100,"output_tokens":10,"cache_creation_tokens":5,"cache_read_tokens":50,"cost_usd":{cost},"pre_upstream_us":3,"ttfb_ms":1,"total_ms":2,"stream":true,"requested_model":"m"}}"#
        )
    };
    let tmp = tempfile::tempdir().unwrap();
    let p = tmp.path().join("tl.jsonl");
    let body = [
        line(999, "9.0"),
        line(1000, "0.10"),
        line(1500, "0.20"),
        line(2000, "null"),
        line(2001, "9.0"),
        "garbage line".into(),
    ]
    .join("\n");
    std::fs::write(&p, body).unwrap();
    let log = results::read_tierline(&p).unwrap();
    assert_eq!(log.len(), 5, "unparseable line skipped");

    let u = attribute(&attempt("a", "t", 0, true, 1000, 2000), &log);
    assert_eq!(u.requests, 3);
    assert_eq!((u.input_tokens, u.output_tokens), (300, 30));
    assert_eq!((u.cache_creation_tokens, u.cache_read_tokens), (15, 150));
    assert!((u.cost_usd - 0.30).abs() < 1e-12);
    assert_eq!(u.unpriced, 1);
    let none = attribute(&attempt("a", "t", 1, true, 5000, 6000), &log);
    assert_eq!(none, Usage::default());
}

#[test]
fn report_math_cost_per_success() {
    // Two tasks x two samples: t1 passes both, t2 passes one.
    let at = [
        attempt("x", "t1", 0, true, 0, 1000),
        attempt("x", "t1", 1, true, 1000, 2000),
        attempt("x", "t2", 0, true, 2000, 3000),
        attempt("x", "t2", 1, false, 3000, 5000),
    ];
    let refs: Vec<&Attempt> = at.iter().collect();
    let us: Vec<Usage> = [0.10, 0.10, 0.20, 0.60]
        .into_iter()
        .map(|c| Usage {
            requests: 1,
            cost_usd: c,
            ..Default::default()
        })
        .collect();
    let s = summarize_arm("x", &refs, Some(&us), 2000, 42);
    assert_eq!((s.attempts, s.successes, s.tasks), (4, 3, 2));
    assert!(
        (s.rate - 0.75).abs() < 1e-12,
        "mean of task rates 1.0 and 0.5"
    );
    assert!((s.cost_usd.unwrap() - 1.0).abs() < 1e-12);
    // Failed attempts still cost money: 1.00 / 3 successes.
    assert!((s.cost_per_success.unwrap() - 1.0 / 3.0).abs() < 1e-12);
    assert_eq!((s.cost_source, s.cost_gaps), ("tierline", 0));
    assert!((s.mean_duration_s - 1.25).abs() < 1e-12);
    assert!(s.ci_lo <= s.rate && s.rate <= s.ci_hi);
}

#[test]
fn cost_gaps_and_fallbacks() {
    let mut at = [
        attempt("x", "t1", 0, true, 0, 10),
        attempt("x", "t1", 1, false, 10, 20),
    ];
    // Tierline: one unpriced request and one attempt with no traffic are both gaps.
    let us = [
        Usage {
            requests: 2,
            unpriced: 1,
            cost_usd: 0.5,
            ..Default::default()
        },
        Usage::default(),
    ];
    let s = summarize_arm("x", &at.iter().collect::<Vec<_>>(), Some(&us), 100, 1);
    assert_eq!(s.cost_gaps, 2);
    // No tierline log: fall back to the agent's own number, flagging the missing one.
    at[0].agent_cost_usd = Some(0.25);
    let s = summarize_arm("x", &at.iter().collect::<Vec<_>>(), None, 100, 1);
    assert_eq!((s.cost_source, s.cost_gaps), ("agent-reported", 1));
    assert_eq!(s.cost_usd, Some(0.25));
    // Nothing known: cost is n/a and never invented.
    at[0].agent_cost_usd = None;
    let s = summarize_arm("x", &at.iter().collect::<Vec<_>>(), None, 100, 1);
    assert_eq!(
        (s.cost_usd, s.cost_per_success, s.cost_source),
        (None, None, "none")
    );
    assert!(markdown(std::slice::from_ref(&s), 100).contains("n/a"));
    assert!(svg(&[s]).contains("n/a"));
    // Zero successes: cost per success undefined even when cost is known.
    let fails = [attempt("x", "t1", 0, false, 0, 10)];
    let us = [Usage {
        requests: 1,
        cost_usd: 1.0,
        ..Default::default()
    }];
    let s = summarize_arm("x", &fails.iter().collect::<Vec<_>>(), Some(&us), 100, 1);
    assert_eq!((s.cost_usd, s.cost_per_success), (Some(1.0), None));
}

#[test]
fn tierline_record_ignores_unknown_fields() {
    let r: TierlineRecord = serde_json::from_str(r#"{"ts_ms":5,"future_field":{"x":1}}"#).unwrap();
    assert_eq!((r.ts_ms, r.input_tokens, r.cost_usd), (5, 0, None));
}
