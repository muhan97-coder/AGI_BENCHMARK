# gc-385 -- Reproduce sealed Welch A/B statistics for a latency experiment

## Dataset

800 request latencies (columns: sample_id, group, latency_ms) from a two-arm experiment: 420 samples in group A, 380 in group B, log-normal-shaped.

File(s): `assets/gc-385/data.csv`. Total size is under 100KB. The data is synthetic and
public-domain; regenerate it byte-identically (stdlib only, fixed seed) with:

    python3 assets/gc-385/make_dataset.py

run from the benchmark repo root. The sha256 of each data file is sealed in
`assets/gc-385/expected_stats.json` and is checked by the grader, so the
bundled data must not be modified.

## General conventions

- Parse numeric CSV fields as IEEE-754 doubles exactly as written.
- "sample" variance/std uses the n-1 denominator.
- quantile(q) uses linear interpolation between order statistics (Type 7, the
  numpy/pandas default): on the ascending sorted sample s (0-indexed) let
  h = (n-1)*q; the result is s[floor(h)] + (h-floor(h)) * (s[floor(h)+1] - s[floor(h)]).
- median = quantile(0.5).
- Count-valued statistics are submitted as numbers like every other statistic.
- All variances/stds are sample statistics (n-1 denominator).
- Directional statistics are B minus A; a flipped sign is a mismatch.

## The 12 sealed statistics

| # | name | definition |
|---|------|------------|
| 1 | `n_a` | number of rows with group == A |
| 2 | `n_b` | number of rows with group == B |
| 3 | `mean_a` | mean latency_ms of group A |
| 4 | `mean_b` | mean latency_ms of group B |
| 5 | `mean_diff_b_minus_a` | mean_b - mean_a (sign matters) |
| 6 | `sample_std_a` | sample std (n-1) of group A |
| 7 | `sample_std_b` | sample std (n-1) of group B |
| 8 | `pooled_std` | sqrt(((n_a-1)*var_a + (n_b-1)*var_b) / (n_a+n_b-2)) with sample variances |
| 9 | `cohens_d` | mean_diff_b_minus_a / pooled_std |
| 10 | `welch_t` | mean_diff_b_minus_a / sqrt(var_a/n_a + var_b/n_b) |
| 11 | `welch_df` | Welch-Satterthwaite degrees of freedom: (var_a/n_a + var_b/n_b)^2 / ((var_a/n_a)^2/(n_a-1) + (var_b/n_b)^2/(n_b-1)) |
| 12 | `median_diff_b_minus_a` | median_b - median_a, medians via Type-7 quantile(0.5) |

## Submission contract

Write `artifacts/gc-385/stats.json` (path relative to the benchmark repo
root): a single JSON object mapping each of the 12 names above to a finite
number. Extra keys are ignored; missing or non-finite values count as
mismatches (fail-closed).

## Grading

    python3 assets/gc-385/grade.py

run from the repo root (stdlib-only; no third-party packages needed). The
grader verifies the sealed data hashes, recomputes all 12 statistics with an
independent implementation, cross-checks them against the sealed values, and
then compares your submission within per-statistic tolerance
`tol = max(1e-8, 1e-6 * |sealed value|)`. Its final stdout line is a JSON
object whose `stats_matched` field is the graded metric; the card passes at
`stats_matched >= 12`. A missing or malformed submission, or a tampered data
file, scores 0.
