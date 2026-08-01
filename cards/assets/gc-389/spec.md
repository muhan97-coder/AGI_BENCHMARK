# gc-389 -- Reproduce a sealed correlation and covariance profile of four channels

## Dataset

500 rows of four correlated numeric channels (columns: row_id, a, b, c, d) generated from a two-factor latent model.

File(s): `assets/gc-389/data.csv`. Total size is under 100KB. The data is synthetic and
public-domain; regenerate it byte-identically (stdlib only, fixed seed) with:

    python3 assets/gc-389/make_dataset.py

run from the benchmark repo root. The sha256 of each data file is sealed in
`assets/gc-389/expected_stats.json` and is checked by the grader, so the
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
| 1 | `pearson_ab` | sample Pearson correlation of columns a and b |
| 2 | `pearson_ac` | sample Pearson correlation of a and c |
| 3 | `pearson_ad` | sample Pearson correlation of a and d |
| 4 | `pearson_bc` | sample Pearson correlation of b and c |
| 5 | `pearson_bd` | sample Pearson correlation of b and d |
| 6 | `pearson_cd` | sample Pearson correlation of c and d |
| 7 | `spearman_ab` | Spearman correlation of a and b: Pearson correlation of ranks, ties resolved by average ranks |
| 8 | `spearman_cd` | Spearman correlation of c and d, same convention |
| 9 | `max_abs_pearson` | max of |pearson_*| over the six pairs |
| 10 | `mean_abs_pearson` | mean of |pearson_*| over the six pairs |
| 11 | `cov_trace` | sum of the four sample variances (n-1 denominator) |
| 12 | `cov_det` | determinant of the 4x4 sample covariance matrix (n-1 denominator) |

## Submission contract

Write `artifacts/gc-389/stats.json` (path relative to the benchmark repo
root): a single JSON object mapping each of the 12 names above to a finite
number. Extra keys are ignored; missing or non-finite values count as
mismatches (fail-closed).

## Grading

    python3 assets/gc-389/grade.py

run from the repo root (stdlib-only; no third-party packages needed). The
grader verifies the sealed data hashes, recomputes all 12 statistics with an
independent implementation, cross-checks them against the sealed values, and
then compares your submission within per-statistic tolerance
`tol = max(1e-8, 1e-6 * |sealed value|)`. Its final stdout line is a JSON
object whose `stats_matched` field is the graded metric; the card passes at
`stats_matched >= 12`. A missing or malformed submission, or a tampered data
file, scores 0.
