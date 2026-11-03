//! Per-arm proxy lifecycle: start, wait for the port, kill when dropped.

use crate::config::ProxyConfig;
use anyhow::{bail, Context, Result};
use std::path::Path;
use std::process::Stdio;
use std::time::Duration;
use tokio::process::{Child, Command};

/// A running proxy. The child is killed when this is dropped (`kill_on_drop`), which
/// covers early returns and errors; `stop` does it explicitly and reaps the process.
pub struct Proxy {
    child: Child,
    pub base_url: String,
}

impl Proxy {
    pub async fn start(cfg: &ProxyConfig, base: &Path) -> Result<Proxy> {
        let mut cmd = Command::new(&cfg.command);
        cmd.args(&cfg.args)
            .env("TIERLINE_LISTEN", &cfg.listen)
            .envs(&cfg.env)
            .stdin(Stdio::null())
            .kill_on_drop(true);
        match &cfg.log {
            Some(l) => {
                let path = base.join(l);
                if let Some(dir) = path.parent() {
                    std::fs::create_dir_all(dir)?;
                }
                let f = std::fs::File::create(&path)
                    .with_context(|| format!("creating {}", path.display()))?;
                cmd.stdout(f.try_clone()?).stderr(f);
            }
            None => {
                cmd.stdout(Stdio::null()).stderr(Stdio::null());
            }
        }
        let mut child = cmd
            .spawn()
            .with_context(|| format!("starting proxy {:?}", cfg.command))?;
        let deadline = tokio::time::Instant::now() + Duration::from_secs(cfg.ready_timeout_secs);
        loop {
            if tokio::net::TcpStream::connect(&cfg.listen).await.is_ok() {
                break;
            }
            if let Some(status) = child.try_wait()? {
                bail!("proxy {:?} exited early ({status})", cfg.command);
            }
            if tokio::time::Instant::now() >= deadline {
                let _ = child.kill().await;
                bail!(
                    "proxy {:?} did not accept connections on {} within {}s",
                    cfg.command,
                    cfg.listen,
                    cfg.ready_timeout_secs
                );
            }
            tokio::time::sleep(Duration::from_millis(100)).await;
        }
        Ok(Proxy {
            child,
            base_url: format!("http://{}", cfg.listen),
        })
    }

    pub async fn stop(mut self) {
        let _ = self.child.kill().await;
    }
}
