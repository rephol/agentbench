//! Agent adapters. `Claude` shells out to the `claude` CLI headlessly; the fakes
//! exist so the harness can be tested without touching a model.

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

/// Pulls `total_cost_usd` out of claude's `--output-format json` stdout.
pub fn parse_reported_cost(stdout: &str) -> Option<f64> {
    let v: serde_json::Value = serde_json::from_str(stdout.trim()).ok()?;
    v.get("total_cost_usd")?.as_f64()
}

pub struct AgentSpec<'a> {
    pub kind: AgentKind,
    pub claude_bin: &'a str,
    pub model: Option<&'a str>,
    pub env: &'a BTreeMap<String, String>,
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
            cmd.args(claude_args(&task.meta.prompt, spec.model))
                .current_dir(workdir)
                .envs(spec.env)
                // A nested session would otherwise inherit the parent's markers.
                .env_remove("CLAUDECODE")
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
                    })
                }
                // The dropped future kills the child (kill_on_drop).
                Err(_) => Ok(AgentOutcome {
                    exit_code: None,
                    timed_out: true,
                    reported_cost_usd: None,
                }),
            }
        }
    }
}
