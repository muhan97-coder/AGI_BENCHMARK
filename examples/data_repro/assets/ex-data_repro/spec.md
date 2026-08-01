# ex-data_repro — reproduce 6 sealed univariate descriptives (teaching example)

This is the **worked example** for the `data_repro` category. It is not a
scored card. It mirrors the shape of a real card (e.g. `gc-384`, which asks for
12 statistics over 900 rows) at a size that grades in under a second.

## Dataset

24 temperature readings (columns: `reading_id`, `temp_c`) from a synthetic
sensor with three injected heat spikes, so the distribution is right-skewed.

File: `assets/ex-data_repro/data.csv`. The data is synthetic and public-domain;
regenerate it byte-identically (stdlib only, fixed seed) with

    python3 assets/ex-data_repro/make_dataset.py

run from the workspace root. The sha256 of the data file is sealed in
`assets/ex-data_repro/expected_stats.json` and is checked by the grader, so the
bundled data must not be modified.

## General conventions

- Parse numeric CSV fields as IEEE-754 doubles exactly as written.
- "sample" variance/std uses the `n-1` denominator.
- `quantile(q)` uses linear interpolation between order statistics (Type 7, the
  numpy/pandas default): on the ascending sorted sample `s` (0-indexed) let
  `h = (n-1)*q`; the result is
  `s[floor(h)] + (h - floor(h)) * (s[floor(h)+1] - s[floor(h)])`.
- `median = quantile(0.5)`.
- Count-valued statistics are submitted as numbers like every other statistic.

## The 6 sealed statistics

| # | name | definition |
|---|------|------------|
| 1 | `n_rows` | number of data rows |
| 2 | `mean` | arithmetic mean of `temp_c` |
| 3 | `sample_std` | sample standard deviation of `temp_c` (`n-1` denominator) |
| 4 | `q25` | `quantile(0.25)`, Type-7 linear interpolation |
| 5 | `median` | `quantile(0.5)`, Type-7 linear interpolation |
| 6 | `skewness_g1` | biased Fisher–Pearson skewness `g1 = m3 / m2**1.5`, with population moments `mk = sum((x-mean)**k)/n`. This equals `scipy.stats.skew(x, bias=True)`; the pandas `.skew()` adjusted estimator will **not** match |

Two of these are deliberately version-sensitive, exactly as in the scored
cards:

- `q25` / `median` — with `n = 24`, `h = 5.75` and `h = 11.5` both fall between
  order statistics, so a "nearest rank" or exclusive (Type-6) quantile gives a
  different number. Only Type-7 matches.
- `skewness_g1` — the **biased** `g1`, not the sample-adjusted `G1`. For
  `n = 24` the adjustment factor `sqrt(n(n-1))/(n-2) ≈ 1.0455`, which is far
  outside the tolerance below.

## Submission contract

Write `artifacts/ex-data_repro/stats.json` (path relative to the workspace
root): a single JSON object mapping each of the 6 names above to a finite
number. Extra keys are ignored; missing or non-finite values count as
mismatches (fail-closed).

## Grading

    python3 assets/ex-data_repro/grade.py

run from the workspace root (stdlib only; no third-party packages needed). The
grader verifies the sealed data hash, recomputes all 6 statistics with an
independent implementation, cross-checks them against the sealed values, and
then compares your submission within per-statistic tolerance
`tol = max(1e-8, 1e-6 * |sealed value|)`. Its final stdout line is a JSON
object whose `stats_matched` field is the graded metric; the card passes at
`stats_matched >= 6`. A missing or malformed submission, or a tampered data
file, scores 0.
