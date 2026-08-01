# gc-388 -- Reproduce sealed trend and autocorrelation figures of a daily series

## Dataset

A 730-step daily series (columns: day_index, value) with a linear trend, a day-of-week seasonal pattern, and AR(1) noise.

File(s): `assets/gc-388/data.csv`. Total size is under 100KB. The data is synthetic and
public-domain; regenerate it byte-identically (stdlib only, fixed seed) with:

    python3 assets/gc-388/make_dataset.py

run from the benchmark repo root. The sha256 of each data file is sealed in
`assets/gc-388/expected_stats.json` and is checked by the grader, so the
bundled data must not be modified.

## General conventions

- Parse numeric CSV fields as IEEE-754 doubles exactly as written.
- "sample" variance/std uses the n-1 denominator.
- quantile(q) uses linear interpolation between order statistics (Type 7, the
  numpy/pandas default): on the ascending sorted sample s (0-indexed) let
  h = (n-1)*q; the result is s[floor(h)] + (h-floor(h)) * (s[floor(h)+1] - s[floor(h)]).
- median = quantile(0.5).
- Count-valued statistics are submitted as numbers like every other statistic.
- The ACF uses one overall mean and the full-sample denominator (the standard biased estimator); do not use per-window means.

## The 12 sealed statistics

| # | name | definition |
|---|------|------------|
| 1 | `n_obs` | number of observations |
| 2 | `series_mean` | mean of value |
| 3 | `series_sample_std` | sample std (n-1) of value |
| 4 | `trend_slope` | OLS slope of value on day_index (0..n-1) |
| 5 | `trend_intercept` | OLS intercept of value on day_index |
| 6 | `acf_lag1` | sum_{t=1..n-1}((x_t - xbar)(x_{t-1} - xbar)) / sum_{t=0..n-1}((x_t - xbar)^2), xbar = overall mean |
| 7 | `acf_lag2` | same estimator at lag 2 |
| 8 | `acf_lag3` | same estimator at lag 3 |
| 9 | `rolling7_mean_max` | maximum over all n-6 windows of 7 consecutive values of the window mean |
| 10 | `first_diff_sample_std` | sample std (n-1) of the n-1 first differences x_{t+1} - x_t |
| 11 | `longest_up_run` | longest number of consecutive strictly positive first differences |
| 12 | `frac_above_mean` | (number of x_t strictly greater than the overall mean) / n |

## Submission contract

Write `artifacts/gc-388/stats.json` (path relative to the benchmark repo
root): a single JSON object mapping each of the 12 names above to a finite
number. Extra keys are ignored; missing or non-finite values count as
mismatches (fail-closed).

## Grading

    python3 assets/gc-388/grade.py

run from the repo root (stdlib-only; no third-party packages needed). The
grader verifies the sealed data hashes, recomputes all 12 statistics with an
independent implementation, cross-checks them against the sealed values, and
then compares your submission within per-statistic tolerance
`tol = max(1e-8, 1e-6 * |sealed value|)`. Its final stdout line is a JSON
object whose `stats_matched` field is the graded metric; the card passes at
`stats_matched >= 12`. A missing or malformed submission, or a tampered data
file, scores 0.
