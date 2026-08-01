# gc-392 -- Reproduce the sealed eigenspectrum of a correlation matrix

## Dataset

450 rows of four numeric measurements (columns: row_id, m1..m4) generated from a two-factor latent structure, so the correlation matrix has two dominant eigenvalues.

File(s): `assets/gc-392/data.csv`. Total size is under 100KB. The data is synthetic and
public-domain; regenerate it byte-identically (stdlib only, fixed seed) with:

    python3 assets/gc-392/make_dataset.py

run from the benchmark repo root. The sha256 of each data file is sealed in
`assets/gc-392/expected_stats.json` and is checked by the grader, so the
bundled data must not be modified.

## General conventions

- Parse numeric CSV fields as IEEE-754 doubles exactly as written.
- "sample" variance/std uses the n-1 denominator.
- quantile(q) uses linear interpolation between order statistics (Type 7, the
  numpy/pandas default): on the ascending sorted sample s (0-indexed) let
  h = (n-1)*q; the result is s[floor(h)] + (h-floor(h)) * (s[floor(h)+1] - s[floor(h)]).
- median = quantile(0.5).
- Count-valued statistics are submitted as numbers like every other statistic.
- The correlation matrix has unit diagonal and sample Pearson correlations off-diagonal (n-1 conventions cancel).

## The 12 sealed statistics

| # | name | definition |
|---|------|------------|
| 1 | `eig1` | largest eigenvalue of the 4x4 Pearson correlation matrix |
| 2 | `eig2` | second largest eigenvalue |
| 3 | `eig3` | third largest eigenvalue |
| 4 | `eig4` | smallest eigenvalue |
| 5 | `evr1` | eig1 / (eig1+eig2+eig3+eig4) |
| 6 | `evr2` | eig2 / trace |
| 7 | `cum_evr_top2` | (eig1 + eig2) / trace |
| 8 | `det_corr` | determinant of the correlation matrix (= product of eigenvalues) |
| 9 | `max_offdiag_abs` | max |r_ij| over the six off-diagonal pairs |
| 10 | `mean_offdiag_abs` | mean |r_ij| over the six off-diagonal pairs |
| 11 | `participation_ratio` | (sum of eigenvalues)^2 / sum of squared eigenvalues |
| 12 | `kaiser_count` | number of eigenvalues strictly greater than 1.0 |

## Submission contract

Write `artifacts/gc-392/stats.json` (path relative to the benchmark repo
root): a single JSON object mapping each of the 12 names above to a finite
number. Extra keys are ignored; missing or non-finite values count as
mismatches (fail-closed).

## Grading

    python3 assets/gc-392/grade.py

run from the repo root (stdlib-only; no third-party packages needed). The
grader verifies the sealed data hashes, recomputes all 12 statistics with an
independent implementation, cross-checks them against the sealed values, and
then compares your submission within per-statistic tolerance
`tol = max(1e-8, 1e-6 * |sealed value|)`. Its final stdout line is a JSON
object whose `stats_matched` field is the graded metric; the card passes at
`stats_matched >= 12`. A missing or malformed submission, or a tampered data
file, scores 0.
