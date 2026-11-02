//! Per-attempt JSONL and the join with a tierline log.
//!
//! Join rule: every attempt records `start_ms`/`end_ms` (unix milliseconds,
//! wall clock). A tierline record belongs to an attempt when
//! `start_ms <= record.ts_ms <= end_ms`. This is only sound when the arm's
//! attempts run sequentially against a dedicated tierline instance whose log
//! file is configured as the arm's `tierline_log`; nothing else may use that
//! proxy while the arm runs.

use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::io::Write;
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Attempt {
    pub arm: String,
    pub task: String,
    pub sample: u32,
    pub pass: bool,
    pub duration_ms: u64,
    /// Agent exit code; null when it timed out.
    pub exit_code: Option<i32>,
    pub timed_out: bool,
    pub check_exit_code: Option<i32>,
    pub start_ms: u128,
    pub end_ms: u128,
    /// Cost the agent reported about itself (claude JSON output); fallback only.
    #[serde(default)]
    pub agent_cost_usd: Option<f64>,
}

pub fn append(path: &Path, a: &Attempt) -> Result<()> {
    if let Some(dir) = path.parent() {
        std::fs::create_dir_all(dir)?;
    }
    let mut f = std::fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(path)
        .with_context(|| format!("opening {}", path.display()))?;
    writeln!(f, "{}", serde_json::to_string(a)?)?;
    Ok(())
}

pub fn read(path: &Path) -> Result<Vec<Attempt>> {
    let raw = match std::fs::read_to_string(path) {
        Ok(r) => r,
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => return Ok(Vec::new()),
        Err(e) => return Err(e).with_context(|| format!("reading {}", path.display())),
    };
    raw.lines()
        .filter(|l| !l.trim().is_empty())
        .enumerate()
        .map(|(i, l)| {
            serde_json::from_str(l).with_context(|| format!("{}:{}", path.display(), i + 1))
        })
        .collect()
}

/// The subset of a tierline log line that the join needs.
#[derive(Debug, Clone, Deserialize)]
pub struct TierlineRecord {
    pub ts_ms: u128,
    #[serde(default)]
    pub input_tokens: u64,
    #[serde(default)]
    pub output_tokens: u64,
    #[serde(default)]
    pub cache_creation_tokens: u64,
    #[serde(default)]
    pub cache_read_tokens: u64,
    #[serde(default)]
    pub cost_usd: Option<f64>,
}

pub fn read_tierline(path: &Path) -> Result<Vec<TierlineRecord>> {
    let raw = std::fs::read_to_string(path)
        .with_context(|| format!("reading tierline log {}", path.display()))?;
    // Lines that do not parse are skipped, as `tierline summary` does.
    Ok(raw
        .lines()
        .filter_map(|l| serde_json::from_str(l).ok())
        .collect())
}

/// Tokens and cost attributed to one attempt.
#[derive(Debug, Clone, Default, PartialEq)]
pub struct Usage {
    pub requests: u64,
    pub input_tokens: u64,
    pub output_tokens: u64,
    pub cache_creation_tokens: u64,
    pub cache_read_tokens: u64,
    pub cost_usd: f64,
    /// Requests in the window that tierline could not price (`cost_usd` null).
    pub unpriced: u64,
}

pub fn attribute(attempt: &Attempt, log: &[TierlineRecord]) -> Usage {
    let mut u = Usage::default();
    for r in log
        .iter()
        .filter(|r| r.ts_ms >= attempt.start_ms && r.ts_ms <= attempt.end_ms)
    {
        u.requests += 1;
        u.input_tokens += r.input_tokens;
        u.output_tokens += r.output_tokens;
        u.cache_creation_tokens += r.cache_creation_tokens;
        u.cache_read_tokens += r.cache_read_tokens;
        match r.cost_usd {
            Some(c) => u.cost_usd += c,
            None => u.unpriced += 1,
        }
    }
    u
}
