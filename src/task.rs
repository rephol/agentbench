//! Task loading. A task is a directory:
//!
//! ```text
//! tasks/<id>/task.toml   id, category, difficulty, prompt
//! tasks/<id>/repo/       the fixture the agent sees
//! tasks/<id>/check.py    hidden from the agent; exit 0 = pass
//! tasks/<id>/solution/   full reference tree (used by `validate` and the fake agent)
//! ```

use anyhow::{bail, Context, Result};
use serde::Deserialize;
use std::fs;
use std::path::{Path, PathBuf};

pub const DIFFICULTIES: [&str; 4] = ["trivial", "easy", "medium", "hard"];

#[derive(Debug, Clone, Deserialize)]
pub struct TaskMeta {
    pub id: String,
    pub category: String,
    pub difficulty: String,
    pub prompt: String,
}

#[derive(Debug, Clone)]
pub struct Task {
    pub meta: TaskMeta,
    pub dir: PathBuf,
}

impl Task {
    pub fn id(&self) -> &str {
        &self.meta.id
    }
    pub fn repo_dir(&self) -> PathBuf {
        self.dir.join("repo")
    }
    pub fn check_path(&self) -> PathBuf {
        self.dir.join("check.py")
    }
    pub fn solution_dir(&self) -> PathBuf {
        self.dir.join("solution")
    }
}

pub fn load_task(dir: &Path) -> Result<Task> {
    let raw = fs::read_to_string(dir.join("task.toml"))
        .with_context(|| format!("reading {}/task.toml", dir.display()))?;
    let meta: TaskMeta =
        toml::from_str(&raw).with_context(|| format!("parsing {}/task.toml", dir.display()))?;
    let dir_name = dir.file_name().and_then(|s| s.to_str()).unwrap_or("");
    if meta.id != dir_name {
        bail!(
            "task id {:?} does not match directory {:?}",
            meta.id,
            dir_name
        );
    }
    if !DIFFICULTIES.contains(&meta.difficulty.as_str()) {
        bail!("task {}: unknown difficulty {:?}", meta.id, meta.difficulty);
    }
    if meta.prompt.trim().is_empty() {
        bail!("task {}: empty prompt", meta.id);
    }
    let task = Task {
        meta,
        dir: dir.to_path_buf(),
    };
    for (what, p) in [
        ("repo/", task.repo_dir()),
        ("solution/", task.solution_dir()),
    ] {
        if !p.is_dir() {
            bail!("task {}: missing {}", task.id(), what);
        }
    }
    if !task.check_path().is_file() {
        bail!("task {}: missing check.py", task.id());
    }
    if task.repo_dir().join("check.py").exists() {
        bail!("task {}: check.py must not live in repo/", task.id());
    }
    Ok(task)
}

/// Loads every task under `root`, sorted by id.
pub fn load_tasks(root: &Path) -> Result<Vec<Task>> {
    let mut tasks = Vec::new();
    for entry in fs::read_dir(root).with_context(|| format!("reading {}", root.display()))? {
        let path = entry?.path();
        if path.is_dir() {
            tasks.push(load_task(&path)?);
        }
    }
    tasks.sort_by(|a, b| a.id().cmp(b.id()));
    Ok(tasks)
}

fn skipped(name: &str) -> bool {
    name == "__pycache__" || name == ".git" || name == ".DS_Store"
}

/// Recursively copies the contents of `src` into `dst` (created if needed).
pub fn copy_tree(src: &Path, dst: &Path) -> Result<()> {
    fs::create_dir_all(dst)?;
    for entry in fs::read_dir(src)? {
        let entry = entry?;
        let name = entry.file_name();
        if skipped(&name.to_string_lossy()) {
            continue;
        }
        let to = dst.join(&name);
        if entry.file_type()?.is_dir() {
            copy_tree(&entry.path(), &to)?;
        } else {
            fs::copy(entry.path(), &to)?;
        }
    }
    Ok(())
}

/// Removes everything inside `dir` but keeps `dir` itself.
pub fn clear_dir(dir: &Path) -> Result<()> {
    for entry in fs::read_dir(dir)? {
        let p = entry?.path();
        if p.is_dir() {
            fs::remove_dir_all(&p)?;
        } else {
            fs::remove_file(&p)?;
        }
    }
    Ok(())
}
