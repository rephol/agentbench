//! Agent adapters. `Claude` shells out to the `claude` CLI headlessly; the fakes
//! exist so the harness can be tested without touching a model.

use crate::results::ModelTokens;
use crate::task::{clear_dir, copy_tree, Task};
use anyhow::Result;
use std::collections::BTreeMap;
use std::path::Path;
use std::process::Stdio;
use std::time::Duration;
use tokio::process::Command;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AgentKind {
    /// The real `claude` CLI. Spends money.
    Claude,
    /// Replaces the workdir with the task's reference solution.
    FakeSolve,
    /// Does nothing (the fixture should then fail its check).
    FakeNoop,
}

impl AgentKind {
    pub fn parse(s: &str) -> Option<AgentKind> {
        match s {
            "claude" => Some(AgentKind::Claude),
            "fake-solve" => Some(AgentKind::FakeSolve),
            "fake-noop" => Some(AgentKind::FakeNoop),
            _ => None,
        }
    }
}

#[derive(Debug, Default)]
pub struct AgentOutcome {
    pub exit_code: Option<i32>,
    pub timed_out: bool,
    /// Cost reported by the agent itself (claude's JSON `total_cost_usd`), if any.
    pub reported_cost_usd: Option<f64>,
    /// Per-model usage from claude's JSON `modelUsage`.
    pub model_usage: BTreeMap<String, ModelTokens>,
}

/// Tools the agent may use; everything else is denied.
pub const ALLOWED_TOOLS: &str = "Read,Edit,Write,Glob,Grep,Bash(python3:*)";

/// The exact argument list passed to the `claude` binary (after the binary name).
///
/// - `-p <prompt>`: headless, print mode, exits when done.
/// - `--permission-mode dontAsk` + `--allowedTools`: anything not on the allowlist is
///   denied without prompting. Only file tools and `python3` via Bash are allowed.
/// - `--output-format json`: one JSON result object, which carries `total_cost_usd`.
/// - `--no-session-persistence`: keep the runs from piling up in the session list.
/// - `--model <m>`: only when the arm sets one.
pub fn claude_args(prompt: &str, model: Option<&str>) -> Vec<String> {
    let mut a: Vec<String> = vec![
        "-p".into(),
        prompt.into(),
        "--permission-mode".into(),
        "dontAsk".into(),
        "--allowedTools".into(),
        ALLOWED_TOOLS.into(),
        "--output-format".into(),
        "json".into(),
        "--no-session-persistence".into(),
    ];
    if let Some(m) = model {
        a.push("--model".into());
        a.push(m.into());
    }
    a
}

/// Flags added by `clean = true`: ignore user-level settings (hooks, plugins), load no
/// MCP servers and no slash commands.
pub const CLEAN_ARGS: [&str; 6] = [
    "--setting-sources",
    "project,local",
    "--strict-mcp-config",
    "--mcp-config",
    r#"{"mcpServers":{}}"#,
    "--disable-slash-commands",
];

/// Env vars starting with these prefixes are removed from the agent's environment
/// when `clean = true` (they carry the parent Claude Code session's state).
pub const SCRUB_PREFIXES: [&str; 2] = ["CLAUDE", "AI_AGENT"];

/// Scrubbed-prefix variables that are kept because authentication needs them.
/// Everything else with a scrubbed prefix goes, as in the original `cleanenv.sh`.
pub const KEEP_VARS: [&str; 2] = ["CLAUDE_CODE_OAUTH_TOKEN", "CLAUDE_CONFIG_DIR"];

/// Which of `names` to remove from the environment for a clean run.
pub fn vars_to_scrub<I: IntoIterator<Item = String>>(names: I) -> Vec<String> {
    names
        .into_iter()
        .filter(|n| SCRUB_PREFIXES.iter().any(|p| n.starts_with(p)))
        .filter(|n| !KEEP_VARS.contains(&n.as_str()))
        .collect()
}

/// Like [`claude_args`], plus the clean-config flags and `--effort <level>`.
pub fn claude_args_with(
    prompt: &str,
    model: Option<&str>,
    clean: bool,
    effort: Option<&str>,
) -> Vec<String> {
    let mut a = claude_args(prompt, model);
    if clean {
        a.extend(CLEAN_ARGS.iter().map(|x| x.to_string()));
    }
    if let Some(e) = effort {
        a.push("--effort".into());
        a.push(e.into());
    }
    a
}

/// Pulls `total_cost_usd` out of claude's `--output-format json` stdout.
pub fn parse_reported_cost(stdout: &str) -> Option<f64> {
    let v: serde_json::Value = serde_json::from_str(stdout.trim()).ok()?;
    v.get("total_cost_usd")?.as_f64()
}

/// Pulls `modelUsage` (per-model tokens and cost) out of claude's JSON stdout.
pub fn parse_model_usage(stdout: &str) -> BTreeMap<String, ModelTokens> {
    let mut out = BTreeMap::new();
    let Ok(v) = serde_json::from_str::<serde_json::Value>(stdout.trim()) else {
        return out;
    };
    let Some(m) = v.get("modelUsage").and_then(|m| m.as_object()) else {
        return out;
    };
    let n = |o: &serde_json::Value, k: &str| o.get(k).and_then(|x| x.as_u64()).unwrap_or(0);
    for (name, u) in m {
        out.insert(
            name.clone(),
            ModelTokens {
                input: n(u, "inputTokens"),
                output: n(u, "outputTokens"),
                cache_read: n(u, "cacheReadInputTokens"),
                cache_creation: n(u, "cacheCreationInputTokens"),
                cost_usd: u.get("costUSD").and_then(|x| x.as_f64()).unwrap_or(0.0),
            },
        );
    }
    out
}

pub struct AgentSpec<'a> {
    pub kind: AgentKind,
    pub claude_bin: &'a str,
    pub model: Option<&'a str>,
    pub env: &'a BTreeMap<String, String>,
    pub extra_args: &'a [String],
    pub clean: bool,
    pub effort: Option<&'a str>,
    pub timeout: Duration,
}

pub async fn run_agent(spec: &AgentSpec<'_>, task: &Task, workdir: &Path) -> Result<AgentOutcome> {
    match spec.kind {
        AgentKind::FakeNoop => Ok(AgentOutcome {
            exit_code: Some(0),
            ..Default::default()
        }),
        AgentKind::FakeSolve => {
            clear_dir(workdir)?;
            copy_tree(&task.solution_dir(), workdir)?;
            Ok(AgentOutcome {
                exit_code: Some(0),
                ..Default::default()
            })
        }
        AgentKind::Claude => {
            let mut cmd = Command::new(spec.claude_bin);
            cmd.args(claude_args_with(
                &task.meta.prompt,
                spec.model,
                spec.clean,
                spec.effort,
            ))
            .args(spec.extra_args)
            .current_dir(workdir);
            // A nested session would otherwise inherit the parent's markers.
            cmd.env_remove("CLAUDECODE");
            if spec.clean {
                for v in vars_to_scrub(std::env::vars().map(|(k, _)| k)) {
                    cmd.env_remove(v);
                }
            }
            // Arm env goes last so an arm can deliberately set a scrubbed name.
            cmd.envs(spec.env)
                .stdin(Stdio::null())
                .stdout(Stdio::piped())
                .stderr(Stdio::null())
                .kill_on_drop(true);
            let child = cmd.spawn()?;
            match tokio::time::timeout(spec.timeout, child.wait_with_output()).await {
                Ok(out) => {
                    let out = out?;
                    let stdout = String::from_utf8_lossy(&out.stdout);
                    Ok(AgentOutcome {
                        exit_code: out.status.code(),
                        timed_out: false,
                        reported_cost_usd: parse_reported_cost(&stdout),
                        model_usage: parse_model_usage(&stdout),
                    })
                }
                // The dropped future kills the child (kill_on_drop).
                Err(_) => Ok(AgentOutcome {
                    exit_code: None,
                    timed_out: true,
                    reported_cost_usd: None,
                    model_usage: BTreeMap::new(),
                }),
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn names(v: &[&str]) -> Vec<String> {
        v.iter().map(|s| s.to_string()).collect()
    }

    #[test]
    fn scrubs_claude_and_ai_agent_but_keeps_auth() {
        let got = vars_to_scrub(names(&[
            "CLAUDECODE",
            "CLAUDE_CODE_ENTRYPOINT",
            "CLAUDE_PLUGIN_ROOT",
            "AI_AGENT",
            "AI_AGENT_NAME",
            "CLAUDE_CODE_OAUTH_TOKEN",
            "CLAUDE_CONFIG_DIR",
            "ANTHROPIC_API_KEY",
            "ANTHROPIC_BASE_URL",
            "PATH",
            "HOME",
            "MYCLAUDE",
        ]));
        assert_eq!(
            got,
            names(&[
                "CLAUDECODE",
                "CLAUDE_CODE_ENTRYPOINT",
                "CLAUDE_PLUGIN_ROOT",
                "AI_AGENT",
                "AI_AGENT_NAME"
            ])
        );
    }

    #[test]
    fn plain_args_unchanged_without_clean_or_effort() {
        assert_eq!(
            claude_args_with("p", Some("opus"), false, None),
            claude_args("p", Some("opus"))
        );
    }

    #[test]
    fn clean_adds_isolation_flags_before_effort() {
        let a = claude_args_with("p", None, true, Some("medium"));
        let base = claude_args("p", None).len();
        assert_eq!(
            &a[base..],
            [
                "--setting-sources",
                "project,local",
                "--strict-mcp-config",
                "--mcp-config",
                r#"{"mcpServers":{}}"#,
                "--disable-slash-commands",
                "--effort",
                "medium"
            ]
        );
    }

    #[test]
    fn effort_without_clean() {
        let a = claude_args_with("p", None, false, Some("high"));
        assert!(!a.contains(&"--setting-sources".to_string()));
        assert_eq!(&a[a.len() - 2..], ["--effort", "high"]);
    }
}
