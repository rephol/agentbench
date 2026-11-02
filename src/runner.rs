//! One attempt = fresh temp copy of the fixture, agent run, then the check.
//! The check file is copied in only after the agent has exited.

use crate::agent::{run_agent, AgentKind, AgentSpec};
use crate::config::Arm;
use crate::results::Attempt;
use crate::task::{copy_tree, Task};
use anyhow::Result;
use std::path::Path;
use std::process::Stdio;
use std::time::{Duration, SystemTime, UNIX_EPOCH};
use tokio::process::Command;

pub fn now_ms() -> u128 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_millis())
        .unwrap_or(0)
}

pub struct RunOpts<'a> {
    pub agent: AgentKind,
    pub python: &'a str,
    pub claude_bin: &'a str,
    pub timeout: Duration,
}

/// Copies `check.py` into `workdir` and runs it. Exit code 0 means pass.
pub async fn run_check(
    task: &Task,
    workdir: &Path,
    python: &str,
    timeout: Duration,
) -> Result<(bool, Option<i32>)> {
    std::fs::copy(task.check_path(), workdir.join("check.py"))?;
    let child = Command::new(python)
        .arg("check.py")
        .current_dir(workdir)
        .env("PYTHONDONTWRITEBYTECODE", "1")
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .kill_on_drop(true)
        .spawn()?;
    match tokio::time::timeout(timeout, child.wait_with_output()).await {
        Ok(out) => {
            let code = out?.status.code();
            Ok((code == Some(0), code))
        }
        Err(_) => Ok((false, None)),
    }
}

pub async fn run_attempt(
    task: &Task,
    arm: &Arm,
    sample: u32,
    opts: &RunOpts<'_>,
) -> Result<Attempt> {
    let tmp = tempfile::tempdir()?;
    let work = tmp.path().join("work");
    copy_tree(&task.repo_dir(), &work)?;

    let spec = AgentSpec {
        kind: opts.agent,
        claude_bin: opts.claude_bin,
        model: arm.model.as_deref(),
        env: &arm.env,
        timeout: opts.timeout,
    };
    let start_ms = now_ms();
    let t0 = std::time::Instant::now();
    let outcome = run_agent(&spec, task, &work).await?;
    let duration_ms = t0.elapsed().as_millis() as u64;
    let end_ms = now_ms();

    let (pass, check_exit_code) =
        run_check(task, &work, opts.python, Duration::from_secs(120)).await?;
    Ok(Attempt {
        arm: arm.name.clone(),
        task: task.id().to_string(),
        sample,
        pass,
        duration_ms,
        exit_code: outcome.exit_code,
        timed_out: outcome.timed_out,
        check_exit_code,
        start_ms,
        end_ms,
        agent_cost_usd: outcome.reported_cost_usd,
    })
}

/// Sanity check for one task: the untouched fixture must fail, the reference
/// solution must pass. Returns (fixture_passed, solution_passed).
pub async fn validate_task(task: &Task, python: &str) -> Result<(bool, bool)> {
    let arm = Arm {
        name: "validate".into(),
        model: None,
        env: Default::default(),
        tierline_log: None,
    };
    let mut res = [false; 2];
    for (i, agent) in [AgentKind::FakeNoop, AgentKind::FakeSolve]
        .into_iter()
        .enumerate()
    {
        let opts = RunOpts {
            agent,
            python,
            claude_bin: "claude",
            timeout: Duration::from_secs(10),
        };
        res[i] = run_attempt(task, &arm, 0, &opts).await?.pass;
    }
    Ok((res[0], res[1]))
}
