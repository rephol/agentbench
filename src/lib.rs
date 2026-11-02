//! agentbench: run coding-agent tasks in throwaway directories, check them
//! deterministically, and report success rate and cost per successful task.

pub mod agent;
pub mod config;
pub mod report;
pub mod results;
pub mod runner;
pub mod stats;
pub mod task;
