//! Seeded bootstrap. Method follows Cloudflare's auto-router evaluation: resample
//! *tasks* (not individual attempts) with replacement, recompute the mean
//! success rate, and take the 2.5th and 97.5th percentiles.

/// SplitMix64: tiny, seedable, and identical on every platform.
pub struct Rng(u64);

impl Rng {
    pub fn new(seed: u64) -> Rng {
        Rng(seed)
    }
    pub fn next_u64(&mut self) -> u64 {
        self.0 = self.0.wrapping_add(0x9E37_79B9_7F4A_7C15);
        let mut z = self.0;
        z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
        z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
        z ^ (z >> 31)
    }
    /// Uniform in `0..n` (modulo bias is negligible for n << 2^64).
    pub fn below(&mut self, n: usize) -> usize {
        (self.next_u64() % n as u64) as usize
    }
}

pub fn mean(xs: &[f64]) -> f64 {
    if xs.is_empty() {
        0.0
    } else {
        xs.iter().sum::<f64>() / xs.len() as f64
    }
}

/// Returns (point estimate, lower, upper) of a 95% percentile bootstrap CI over
/// per-task success rates. Empty input yields zeros.
pub fn bootstrap_ci(task_rates: &[f64], resamples: usize, seed: u64) -> (f64, f64, f64) {
    if task_rates.is_empty() || resamples == 0 {
        return (0.0, 0.0, 0.0);
    }
    let mut rng = Rng::new(seed);
    let n = task_rates.len();
    let mut means: Vec<f64> = (0..resamples)
        .map(|_| {
            let s: f64 = (0..n).map(|_| task_rates[rng.below(n)]).sum();
            s / n as f64
        })
        .collect();
    means.sort_by(|a, b| a.partial_cmp(b).unwrap());
    let lo = means[((0.025 * resamples as f64).floor() as usize).min(resamples - 1)];
    let hi_idx = ((0.975 * resamples as f64).ceil() as usize).clamp(1, resamples) - 1;
    (mean(task_rates), lo, means[hi_idx])
}
