//! Per-arm summary, markdown table and SVG chart.

use crate::config::Config;
use crate::results::{attribute, read_tierline, Attempt, Usage};
use crate::stats::bootstrap_ci;
use anyhow::Result;
use std::collections::BTreeMap;
use std::path::Path;

#[derive(Debug, Clone, PartialEq)]
pub struct ArmSummary {
    pub arm: String,
    pub attempts: usize,
    pub successes: usize,
    pub tasks: usize,
    /// Mean over tasks of that task's pass rate across samples.
    pub rate: f64,
    pub ci_lo: f64,
    pub ci_hi: f64,
    pub cost_usd: Option<f64>,
    pub cost_per_success: Option<f64>,
    /// "tierline", "agent-reported" or "none".
    pub cost_source: &'static str,
    /// Requests tierline could not price plus attempts with no matching traffic.
    pub cost_gaps: u64,
    pub mean_duration_s: f64,
}

/// `usages`, when given, is parallel to `attempts` (tierline-attributed).
pub fn summarize_arm(
    arm: &str,
    attempts: &[&Attempt],
    usages: Option<&[Usage]>,
    resamples: usize,
    seed: u64,
) -> ArmSummary {
    let mut per_task: BTreeMap<&str, (u32, u32)> = BTreeMap::new();
    for a in attempts {
        let e = per_task.entry(a.task.as_str()).or_default();
        e.0 += a.pass as u32;
        e.1 += 1;
    }
    let rates: Vec<f64> = per_task
        .values()
        .map(|(p, n)| *p as f64 / *n as f64)
        .collect();
    let (rate, ci_lo, ci_hi) = bootstrap_ci(&rates, resamples, seed);
    let successes = attempts.iter().filter(|a| a.pass).count();

    let (cost_usd, cost_source, cost_gaps) = match usages {
        Some(us) => {
            let gaps: u64 = us
                .iter()
                .map(|u| u.unpriced + (u.requests == 0) as u64)
                .sum();
            (Some(us.iter().map(|u| u.cost_usd).sum()), "tierline", gaps)
        }
        None => {
            let reported: Vec<f64> = attempts.iter().filter_map(|a| a.agent_cost_usd).collect();
            if reported.is_empty() {
                (None, "none", 0)
            } else {
                let missing = (attempts.len() - reported.len()) as u64;
                (Some(reported.iter().sum()), "agent-reported", missing)
            }
        }
    };
    let cost_per_success = match (cost_usd, successes) {
        (Some(c), s) if s > 0 => Some(c / s as f64),
        _ => None,
    };
    let mean_duration_s = if attempts.is_empty() {
        0.0
    } else {
        attempts.iter().map(|a| a.duration_ms as f64).sum::<f64>() / attempts.len() as f64 / 1000.0
    };
    ArmSummary {
        arm: arm.to_string(),
        attempts: attempts.len(),
        successes,
        tasks: per_task.len(),
        rate,
        ci_lo,
        ci_hi,
        cost_usd,
        cost_per_success,
        cost_source,
        cost_gaps,
        mean_duration_s,
    }
}

/// Summarizes every arm of `config` that has attempts, joining tierline logs
/// (paths resolved relative to `base`).
pub fn build(
    config: &Config,
    attempts: &[Attempt],
    base: &Path,
    resamples: usize,
    seed: u64,
) -> Result<Vec<ArmSummary>> {
    let mut out = Vec::new();
    for arm in &config.arms {
        let mine: Vec<&Attempt> = attempts.iter().filter(|a| a.arm == arm.name).collect();
        if mine.is_empty() {
            continue;
        }
        let usages = match &arm.tierline_log {
            Some(p) if base.join(p).is_file() => {
                let log = read_tierline(&base.join(p))?;
                Some(mine.iter().map(|a| attribute(a, &log)).collect::<Vec<_>>())
            }
            _ => None,
        };
        out.push(summarize_arm(
            &arm.name,
            &mine,
            usages.as_deref(),
            resamples,
            seed,
        ));
    }
    Ok(out)
}

fn usd(v: Option<f64>) -> String {
    v.map_or("n/a".into(), |c| format!("${c:.4}"))
}

pub fn markdown(rows: &[ArmSummary], resamples: usize) -> String {
    let mut s = String::from(
        "| arm | tasks | attempts | success rate | 95% CI | total cost | cost / success | cost source | mean time |\n\
         |---|---|---|---|---|---|---|---|---|\n",
    );
    for r in rows {
        let gaps = if r.cost_gaps > 0 {
            format!(" ({} gaps)", r.cost_gaps)
        } else {
            String::new()
        };
        s += &format!(
            "| {} | {} | {} | {:.1}% ({}/{}) | {:.1}% to {:.1}% | {} | {} | {}{} | {:.0}s |\n",
            r.arm,
            r.tasks,
            r.attempts,
            r.rate * 100.0,
            r.successes,
            r.attempts,
            r.ci_lo * 100.0,
            r.ci_hi * 100.0,
            usd(r.cost_usd),
            usd(r.cost_per_success),
            r.cost_source,
            gaps,
            r.mean_duration_s
        );
    }
    s += &format!(
        "\nSuccess rate is the mean over tasks of each task's pass rate across samples. The CI is a \
         percentile bootstrap with {resamples} task-level resamples. A cost gap is a request tierline \
         could not price or an attempt with no matching request in the log.\n"
    );
    s
}

fn esc(s: &str) -> String {
    s.replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
}

/// Two panels: success rate with CI whiskers, and cost per success.
pub fn svg(rows: &[ArmSummary]) -> String {
    let w = 640.0;
    let row_h = 44.0;
    let top = 56.0;
    let panel_h = top + row_h * rows.len().max(1) as f64 + 24.0;
    let h = panel_h * 2.0;
    let left = 150.0;
    let plot_w = w - left - 70.0;
    let mut s = format!(
        "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 {w} {h}\" width=\"{w}\" height=\"{h}\" \
         font-family=\"system-ui, sans-serif\" font-size=\"13\">\n<rect width=\"100%\" height=\"100%\" fill=\"#ffffff\"/>\n"
    );
    s += "<text x=\"16\" y=\"28\" font-size=\"15\" font-weight=\"600\" fill=\"#111\">Success rate (95% bootstrap CI)</text>\n";
    for (i, r) in rows.iter().enumerate() {
        let y = top + row_h * i as f64;
        let bw = plot_w * r.rate;
        let x = |v: f64| left + plot_w * v;
        s += &format!(
            "<text x=\"{}\" y=\"{}\" text-anchor=\"end\" fill=\"#111\">{}</text>\n\
             <rect x=\"{left}\" y=\"{}\" width=\"{bw:.1}\" height=\"20\" fill=\"#2f6fdb\"/>\n\
             <line x1=\"{:.1}\" x2=\"{:.1}\" y1=\"{}\" y2=\"{}\" stroke=\"#111\" stroke-width=\"2\"/>\n\
             <text x=\"{:.1}\" y=\"{}\" fill=\"#111\">{:.0}%</text>\n",
            left - 10.0,
            y + 15.0,
            esc(&r.arm),
            y,
            x(r.ci_lo),
            x(r.ci_hi),
            y + 10.0,
            y + 10.0,
            x(r.ci_hi.max(r.rate)) + 8.0,
            y + 15.0,
            r.rate * 100.0
        );
    }
    let oy = panel_h;
    s += &format!(
        "<text x=\"16\" y=\"{}\" font-size=\"15\" font-weight=\"600\" fill=\"#111\">Cost per successful task (USD)</text>\n",
        oy + 28.0
    );
    let max = rows
        .iter()
        .filter_map(|r| r.cost_per_success)
        .fold(0.0_f64, f64::max);
    for (i, r) in rows.iter().enumerate() {
        let y = oy + top + row_h * i as f64;
        s += &format!(
            "<text x=\"{}\" y=\"{}\" text-anchor=\"end\" fill=\"#111\">{}</text>\n",
            left - 10.0,
            y + 15.0,
            esc(&r.arm)
        );
        match r.cost_per_success {
            Some(c) if max > 0.0 => {
                let bw = plot_w * c / max;
                s += &format!(
                    "<rect x=\"{left}\" y=\"{y}\" width=\"{bw:.1}\" height=\"20\" fill=\"#d9822b\"/>\n\
                     <text x=\"{:.1}\" y=\"{}\" fill=\"#111\">${c:.4}</text>\n",
                    left + bw + 8.0,
                    y + 15.0
                );
            }
            _ => {
                s += &format!(
                    "<text x=\"{left}\" y=\"{}\" fill=\"#666\">n/a</text>\n",
                    y + 15.0
                );
            }
        }
    }
    s += "</svg>\n";
    s
}
