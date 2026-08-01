# gc-384 -- Reproduce 12 sealed univariate descriptives from a sensor log slice

## Dataset

900 temperature readings (columns: reading_id, temp_c) from a synthetic sensor with occasional injected heat spikes, so the distribution is right-skewed.

File(s): `assets/gc-384/data.csv`. Total size is under 100KB. The data is synthetic and
public-domain; regenerate it byte-identically (stdlib only, fixed seed) with:

    python3 assets/gc-384/make_dataset.py

run from the benchmark repo root. The sha256 of each data file is sealed in
`assets/gc-384/expected_stats.json` and is checked by the grader, so the
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
| 1 | `n_rows` | number of data rows |
| 2 | `mean` | arithmetic mean of temp_c |
| 3 | `sample_std` | sample standard deviation of temp_c (n-1 denominator) |
| 4 | `sample_variance` | sample variance of temp_c (n-1 denominator) |
| 5 | `minimum` | smallest temp_c value |
| 6 | `maximum` | largest temp_c value |
| 7 | `median` | quantile(0.5), Type-7 linear interpolation |
| 8 | `q25` | quantile(0.25), Type-7 |
| 9 | `q75` | quantile(0.75), Type-7 |
| 10 | `iqr` | q75 - q25 |
| 11 | `skewness_g1` | biased Fisher-Pearson skewness g1 = m3 / m2^(3/2), with population moments mk = sum((x-mean)^k)/n. This equals scipy.stats.skew(x, bias=True); the pandas .skew() adjusted estimator will NOT match |
| 12 | `value_range` | maximum - minimum |

## Submission contract

Write `artifacts/gc-384/stats.json` (path relative to the benchmark repo
root): a single JSON object mapping each of the 12 names above to a finite
number. Extra keys are ignored; missing or non-finite values count as
mismatches (fail-closed).

## Grading

    python3 assets/gc-384/grade.py

run from the repo root (stdlib-only; no third-party packages needed). The
grader verifies the sealed data hashes, recomputes all 12 statistics with an
independent implementation, cross-checks them against the sealed values, and
then compares your submission within per-statistic tolerance
`tol = max(1e-8, 1e-6 * |sealed value|)`. Its final stdout line is a JSON
object whose `stats_matched` field is the graded metric; the card passes at
`stats_matched >= 12`. A missing or malformed submission, or a tampered data
file, scores 0.
