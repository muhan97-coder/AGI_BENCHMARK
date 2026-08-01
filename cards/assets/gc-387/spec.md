# gc-387 -- Reproduce a sealed OLS decomposition on a bundled xy slice

## Dataset

640 observations (columns: obs_id, x, y) with a linear relationship y ~ 3.2 + 0.85x plus Gaussian noise.

File(s): `assets/gc-387/data.csv`. Total size is under 100KB. The data is synthetic and
public-domain; regenerate it byte-identically (stdlib only, fixed seed) with:

    python3 assets/gc-387/make_dataset.py

run from the benchmark repo root. The sha256 of each data file is sealed in
`assets/gc-387/expected_stats.json` and is checked by the grader, so the
bundled data must not be modified.

## General conventions

- Parse numeric CSV fields as IEEE-754 doubles exactly as written.
- "sample" variance/std uses the n-1 denominator.
- quantile(q) uses linear interpolation between order statistics (Type 7, the
  numpy/pandas default): on the ascending sorted sample s (0-indexed) let
  h = (n-1)*q; the result is s[floor(h)] + (h-floor(h)) * (s[floor(h)+1] - s[floor(h)]).
- median = quantile(0.5).
- Count-valued statistics are submitted as numbers like every other statistic.
- yhat = intercept + slope * x for every row.

## The 12 sealed statistics

| # | name | definition |
|---|------|------------|
| 1 | `n_rows` | number of data rows |
| 2 | `slope` | OLS slope of y on x: sum((x-mx)(y-my)) / sum((x-mx)^2) |
| 3 | `intercept` | mean(y) - slope * mean(x) |
| 4 | `pearson_r` | sample Pearson correlation of x and y |
| 5 | `r_squared` | 1 - SSE/SST |
| 6 | `sse` | sum of squared residuals sum((y - yhat)^2) |
| 7 | `ssr` | regression sum of squares sum((yhat - mean(y))^2) |
| 8 | `sst` | total sum of squares sum((y - mean(y))^2) |
| 9 | `residual_std` | sqrt(SSE / (n - 2)) |
| 10 | `mean_x` | mean of x |
| 11 | `max_abs_residual` | max |y - yhat| |
| 12 | `pred_at_x_50` | intercept + slope * 50.0 |

## Submission contract

Write `artifacts/gc-387/stats.json` (path relative to the benchmark repo
root): a single JSON object mapping each of the 12 names above to a finite
number. Extra keys are ignored; missing or non-finite values count as
mismatches (fail-closed).

## Grading

    python3 assets/gc-387/grade.py

run from the repo root (stdlib-only; no third-party packages needed). The
grader verifies the sealed data hashes, recomputes all 12 statistics with an
independent implementation, cross-checks them against the sealed values, and
then compares your submission within per-statistic tolerance
`tol = max(1e-8, 1e-6 * |sealed value|)`. Its final stdout line is a JSON
object whose `stats_matched` field is the graded metric; the card passes at
`stats_matched >= 12`. A missing or malformed submission, or a tampered data
file, scores 0.
