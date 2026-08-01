# gc-386 -- Reproduce sealed frequency and entropy statistics of an event log

## Dataset

523 events (columns: event_id, category) drawn from 12 distinct event categories with a heavily skewed frequency profile.

File(s): `assets/gc-386/data.csv`. Total size is under 100KB. The data is synthetic and
public-domain; regenerate it byte-identically (stdlib only, fixed seed) with:

    python3 assets/gc-386/make_dataset.py

run from the benchmark repo root. The sha256 of each data file is sealed in
`assets/gc-386/expected_stats.json` and is checked by the grader, so the
bundled data must not be modified.

## General conventions

- Parse numeric CSV fields as IEEE-754 doubles exactly as written.
- "sample" variance/std uses the n-1 denominator.
- quantile(q) uses linear interpolation between order statistics (Type 7, the
  numpy/pandas default): on the ascending sorted sample s (0-indexed) let
  h = (n-1)*q; the result is s[floor(h)] + (h-floor(h)) * (s[floor(h)+1] - s[floor(h)]).
- median = quantile(0.5).
- Count-valued statistics are submitted as numbers like every other statistic.
- Entropy uses log base 2, not natural log.

## The 12 sealed statistics

| # | name | definition |
|---|------|------------|
| 1 | `n_events` | number of data rows |
| 2 | `n_categories` | number of distinct categories observed |
| 3 | `top1_count` | count of the most frequent category |
| 4 | `top1_share` | top1_count / n_events |
| 5 | `top3_share` | sum of the three largest category counts / n_events |
| 6 | `least_count` | count of the least frequent category |
| 7 | `entropy_bits` | Shannon entropy of the category distribution in bits: -sum(p_i * log2(p_i)) over observed categories |
| 8 | `gini_impurity` | 1 - sum(p_i^2) |
| 9 | `chi_square_uniform` | sum((o_i - e)^2 / e) with e = n_events / n_categories |
| 10 | `effective_categories` | 2 ** entropy_bits |
| 11 | `share_ratio_max_min` | top1_count / least_count |
| 12 | `n_above_uniform` | number of categories whose count is strictly greater than n_events / n_categories |

## Submission contract

Write `artifacts/gc-386/stats.json` (path relative to the benchmark repo
root): a single JSON object mapping each of the 12 names above to a finite
number. Extra keys are ignored; missing or non-finite values count as
mismatches (fail-closed).

## Grading

    python3 assets/gc-386/grade.py

run from the repo root (stdlib-only; no third-party packages needed). The
grader verifies the sealed data hashes, recomputes all 12 statistics with an
independent implementation, cross-checks them against the sealed values, and
then compares your submission within per-statistic tolerance
`tol = max(1e-8, 1e-6 * |sealed value|)`. Its final stdout line is a JSON
object whose `stats_matched` field is the graded metric; the card passes at
`stats_matched >= 12`. A missing or malformed submission, or a tampered data
file, scores 0.
