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
    /// Default for every arm's `clean` option.
    #[serde(default)]
    pub clean: bool,
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
            clean: false,
        }
    }
}

/// One configuration under test: a name, environment for the agent process, an
/// optional `--model`, and the tierline JSONL log that records this arm's traffic.
#[derive(Debug, Clone, Default, Deserialize)]
pub struct Arm {
    pub name: String,
    #[serde(default)]
    pub model: Option<String>,
    #[serde(default)]
    pub env: BTreeMap<String, String>,
    #[serde(default)]
    pub tierline_log: Option<String>,
    /// Extra arguments appended to the `claude` command line (e.g. `--settings`).
    #[serde(default)]
    pub extra_args: Vec<String>,
    /// Clean config for the claude adapter (overrides `run.clean`): scrub `CLAUDE*` /
    /// `AI_AGENT*` env vars and ignore user settings, MCP servers and slash commands.
    #[serde(default)]
    pub clean: Option<bool>,
    /// Passed as `--effort <level>`.
    #[serde(default)]
    pub effort: Option<String>,
    /// A proxy `run` starts before this arm and kills after it.
    #[serde(default)]
    pub proxy: Option<ProxyConfig>,
}

impl Arm {
    pub fn is_clean(&self, run: &RunConfig) -> bool {
        self.clean.unwrap_or(run.clean)
    }
}

/// A process started for the duration of one arm (e.g. tierline).
#[derive(Debug, Clone, Deserialize)]
pub struct ProxyConfig {
    pub command: String,
    #[serde(default)]
    pub args: Vec<String>,
    #[serde(default)]
    pub env: BTreeMap<String, String>,
    /// `host:port` the proxy listens on. `run` waits for it to accept connections and
    /// sets `ANTHROPIC_BASE_URL=http://<listen>` for the agent. Also exported to the
    /// proxy as `TIERLINE_LISTEN` unless `env` sets it.
    pub listen: String,
    /// File that receives the proxy's stdout and stderr. Default: discarded.
    #[serde(default)]
    pub log: Option<String>,
    #[serde(default = "d_ready")]
    pub ready_timeout_secs: u64,
}

fn d_ready() -> u64 {
    30
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
        for a in &c.arms {
            if let Some(p) = &a.proxy {
                if p.listen
                    .rsplit_once(':')
                    .and_then(|(_, port)| port.parse::<u16>().ok())
                    .is_none()
                {
                    bail!("arm {:?}: proxy.listen must look like host:port", a.name);
                }
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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_clean_effort_and_proxy() {
        let c = Config::parse(
            r#"
[run]
clean = true
[[arm]]
name = "a"
effort = "medium"
[[arm]]
name = "b"
clean = false
[arm.proxy]
command = "tierline"
listen = "127.0.0.1:8812"
env = { TIERLINE_ROUTE = "1" }
"#,
        )
        .unwrap();
        assert!(c.arms[0].is_clean(&c.run));
        assert_eq!(c.arms[0].effort.as_deref(), Some("medium"));
        assert!(!c.arms[1].is_clean(&c.run));
        let p = c.arms[1].proxy.as_ref().unwrap();
        assert_eq!(p.ready_timeout_secs, 30);
        assert_eq!(p.env["TIERLINE_ROUTE"], "1");
    }

    #[test]
    fn rejects_bad_listen() {
        let r = Config::parse("[[arm]]\nname=\"a\"\n[arm.proxy]\ncommand=\"x\"\nlisten=\"nope\"\n");
        assert!(r.is_err());
    }
}
