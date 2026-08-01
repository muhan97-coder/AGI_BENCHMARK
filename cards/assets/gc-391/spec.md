# gc-391 -- Reproduce a sealed one-way ANOVA decomposition across four machines

## Dataset

650 production units (columns: unit_id, machine, yield_pct) from four machines (alpha, beta, gamma, delta) with unequal group sizes and different mean yields.

File(s): `assets/gc-391/data.csv`. Total size is under 100KB. The data is synthetic and
public-domain; regenerate it byte-identically (stdlib only, fixed seed) with:

    python3 assets/gc-391/make_dataset.py

run from the benchmark repo root. The sha256 of each data file is sealed in
`assets/gc-391/expected_stats.json` and is checked by the grader, so the
bundled data must not be modified.

## General conventions

- Parse numeric CSV fields as IEEE-754 doubles exactly as written.
- "sample" variance/std uses the n-1 denominator.
- quantile(q) uses linear interpolation between order statistics (Type 7, the
  numpy/pandas default): on the ascending sorted sample s (0-indexed) let
  h = (n-1)*q; the result is s[floor(h)] + (h-floor(h)) * (s[floor(h)+1] - s[floor(h)]).
- median = quantile(0.5).
- Count-valued statistics are submitted as numbers like every other statistic.

## The 12 sealed statistics

| # | name | definition |
|---|------|------------|
| 1 | `n_total` | total number of units |
| 2 | `grand_mean` | mean of yield_pct over all units |
| 3 | `mean_alpha` | mean yield_pct of machine alpha |
| 4 | `mean_beta` | mean yield_pct of machine beta |
| 5 | `mean_gamma` | mean yield_pct of machine gamma |
| 6 | `mean_delta` | mean yield_pct of machine delta |
| 7 | `ss_between` | sum over groups of n_g * (mean_g - grand_mean)^2 |
| 8 | `ss_within` | sum over groups of sum((value - mean_g)^2) |
| 9 | `f_statistic` | (ss_between / (k-1)) / (ss_within / (n-k)) with k = 4 groups |
| 10 | `eta_squared` | ss_between / (ss_between + ss_within) |
| 11 | `largest_group_n` | size of the largest group |
| 12 | `range_of_group_means` | max group mean - min group mean |

## Submission contract

Write `artifacts/gc-391/stats.json` (path relative to the benchmark repo
root): a single JSON object mapping each of the 12 names above to a finite
number. Extra keys are ignored; missing or non-finite values count as
mismatches (fail-closed).

## Grading

    python3 assets/gc-391/grade.py

run from the repo root (stdlib-only; no third-party packages needed). The
grader verifies the sealed data hashes, recomputes all 12 statistics with an
independent implementation, cross-checks them against the sealed values, and
then compares your submission within per-statistic tolerance
`tol = max(1e-8, 1e-6 * |sealed value|)`. Its final stdout line is a JSON
object whose `stats_matched` field is the graded metric; the card passes at
`stats_matched >= 12`. A missing or malformed submission, or a tampered data
file, scores 0.
