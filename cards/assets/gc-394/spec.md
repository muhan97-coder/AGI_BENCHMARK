# gc-394 -- Reproduce sealed jackknife influence statistics for four estimators

## Dataset

240 paired observations (columns: row_id, x, y) where x has a small fraction of injected outliers and y is linearly related to x.

File(s): `assets/gc-394/data.csv`. Total size is under 100KB. The data is synthetic and
public-domain; regenerate it byte-identically (stdlib only, fixed seed) with:

    python3 assets/gc-394/make_dataset.py

run from the benchmark repo root. The sha256 of each data file is sealed in
`assets/gc-394/expected_stats.json` and is checked by the grader, so the
bundled data must not be modified.

## General conventions

- Parse numeric CSV fields as IEEE-754 doubles exactly as written.
- "sample" variance/std uses the n-1 denominator.
- quantile(q) uses linear interpolation between order statistics (Type 7, the
  numpy/pandas default): on the ascending sorted sample s (0-indexed) let
  h = (n-1)*q; the result is s[floor(h)] + (h-floor(h)) * (s[floor(h)+1] - s[floor(h)]).
- median = quantile(0.5).
- Count-valued statistics are submitted as numbers like every other statistic.
- Jackknife SE of an estimator theta: compute theta_(i) on each of the n leave-one-out subsamples, let theta_bar = mean of the theta_(i); SE = sqrt((n-1)/n * sum_i (theta_(i) - theta_bar)^2).
- Medians (full and LOO) use Type-7 quantile(0.5): for an even-size sample the mean of the two middle order statistics, for odd the middle one.

## The 12 sealed statistics

| # | name | definition |
|---|------|------------|
| 1 | `n_rows` | number of data rows (n) |
| 2 | `mean_x` | mean of x on the full sample |
| 3 | `median_x` | median of x, Type-7 quantile(0.5) |
| 4 | `trimmed_mean_x_10` | 10 percent trimmed mean of x: sort, drop k = floor(0.1*m) values from EACH end (m = sample size), mean of the rest |
| 5 | `jackknife_se_mean_x` | jackknife SE of the mean of x (formula below) |
| 6 | `jackknife_se_median_x` | jackknife SE of the median of x |
| 7 | `jackknife_se_trimmed_x` | jackknife SE of the 10 percent trimmed mean of x; the trim count k is recomputed on each LOO subsample of size n-1 |
| 8 | `pearson_xy` | sample Pearson correlation of x and y on the full sample |
| 9 | `jackknife_se_pearson_xy` | jackknife SE of the Pearson correlation |
| 10 | `jackknife_bias_pearson_xy` | jackknife bias estimate: (n-1) * (mean of LOO estimates - full-sample estimate) |
| 11 | `max_abs_influence_pearson` | max over i of |theta_(i) - theta_full| for the Pearson estimator |
| 12 | `min_loo_pearson` | minimum over i of the LOO Pearson estimates theta_(i) |

## Submission contract

Write `artifacts/gc-394/stats.json` (path relative to the benchmark repo
root): a single JSON object mapping each of the 12 names above to a finite
number. Extra keys are ignored; missing or non-finite values count as
mismatches (fail-closed).

## Grading

    python3 assets/gc-394/grade.py

run from the repo root (stdlib-only; no third-party packages needed). The
grader verifies the sealed data hashes, recomputes all 12 statistics with an
independent implementation, cross-checks them against the sealed values, and
then compares your submission within per-statistic tolerance
`tol = max(1e-8, 1e-6 * |sealed value|)`. Its final stdout line is a JSON
object whose `stats_matched` field is the graded metric; the card passes at
`stats_matched >= 12`. A missing or malformed submission, or a tampered data
file, scores 0.
