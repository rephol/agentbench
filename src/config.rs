//! `bench.toml`: run settings and arms.

use anyhow::{bail, Context, Result};
use serde::Deserialize;
use std::collections::BTreeMap;
use std::path::Path;

#[derive(Debug, Clone, Deserialize)]
pub struct RunConfig {
    #[serde(default = "d_samples")]
    pub samples: u32,
    #[serde(default = "d_timeout")]
    pub timeout_secs: u64,
    #[serde(default = "d_tasks")]
    pub tasks_dir: String,
    #[serde(default = "d_python")]
    pub python: String,
    #[serde(default = "d_claude")]
    pub claude_bin: String,
}

fn d_samples() -> u32 {
    2
}
fn d_timeout() -> u64 {
    900
}
fn d_tasks() -> String {
    "tasks".into()
}
fn d_python() -> String {
    "python3".into()
}
fn d_claude() -> String {
    "claude".into()
}

impl Default for RunConfig {
    fn default() -> Self {
        RunConfig {
            samples: d_samples(),
            timeout_secs: d_timeout(),
            tasks_dir: d_tasks(),
            python: d_python(),
            claude_bin: d_claude(),
        }
    }
}

/// One configuration under test: a name, environment for the agent process, an
/// optional `--model`, and the tierline JSONL log that records this arm's traffic.
#[derive(Debug, Clone, Deserialize)]
pub struct Arm {
    pub name: String,
    #[serde(default)]
    pub model: Option<String>,
    #[serde(default)]
    pub env: BTreeMap<String, String>,
    #[serde(default)]
    pub tierline_log: Option<String>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct Config {
    #[serde(default)]
    pub run: RunConfig,
    #[serde(default, rename = "arm")]
    pub arms: Vec<Arm>,
}

impl Config {
    pub fn parse(s: &str) -> Result<Config> {
        let c: Config = toml::from_str(s)?;
        if c.arms.is_empty() {
            bail!("bench.toml defines no [[arm]]");
        }
        let mut seen = std::collections::BTreeSet::new();
        for a in &c.arms {
            if !seen.insert(&a.name) {
                bail!("duplicate arm name {:?}", a.name);
            }
        }
        if c.run.samples == 0 {
            bail!("run.samples must be >= 1");
        }
        Ok(c)
    }

    pub fn load(path: &Path) -> Result<Config> {
        let raw =
            std::fs::read_to_string(path).with_context(|| format!("reading {}", path.display()))?;
        Config::parse(&raw).with_context(|| format!("parsing {}", path.display()))
    }

    pub fn arm(&self, name: &str) -> Option<&Arm> {
        self.arms.iter().find(|a| a.name == name)
    }
}
