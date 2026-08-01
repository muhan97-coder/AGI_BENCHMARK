# gc-390 -- Reproduce sealed missing-data census statistics under two estimands

## Dataset

600 rows (columns: row_id, x, y, z) where each numeric cell is independently missing with column-specific probability; missing cells are empty CSV fields.

File(s): `assets/gc-390/data.csv`. Total size is under 100KB. The data is synthetic and
public-domain; regenerate it byte-identically (stdlib only, fixed seed) with:

    python3 assets/gc-390/make_dataset.py

run from the benchmark repo root. The sha256 of each data file is sealed in
`assets/gc-390/expected_stats.json` and is checked by the grader, so the
bundled data must not be modified.

## General conventions

- Parse numeric CSV fields as IEEE-754 doubles exactly as written.
- "sample" variance/std uses the n-1 denominator.
- quantile(q) uses linear interpolation between order statistics (Type 7, the
  numpy/pandas default): on the ascending sorted sample s (0-indexed) let
  h = (n-1)*q; the result is s[floor(h)] + (h-floor(h)) * (s[floor(h)+1] - s[floor(h)]).
- median = quantile(0.5).
- Count-valued statistics are submitted as numbers like every other statistic.
- A cell is missing if and only if the CSV field is the empty string.
- Complete-case statistics condition on all three of x, y, z being present, even for the xy correlation.

## The 12 sealed statistics

| # | name | definition |
|---|------|------------|
| 1 | `n_rows` | total number of data rows |
| 2 | `n_complete_rows` | rows where x, y, and z are ALL present |
| 3 | `n_missing_cells` | total count of empty cells across columns x, y, z |
| 4 | `missing_rate` | n_missing_cells / (3 * n_rows) |
| 5 | `x_missing` | number of rows with x missing |
| 6 | `y_missing` | number of rows with y missing |
| 7 | `z_missing` | number of rows with z missing |
| 8 | `x_mean_available` | mean over ALL non-missing x values (available-case) |
| 9 | `y_mean_available` | mean over all non-missing y values |
| 10 | `z_mean_available` | mean over all non-missing z values |
| 11 | `x_mean_complete` | mean of x over complete rows only (x, y, z all present) |
| 12 | `pearson_xy_complete` | sample Pearson correlation of x and y computed over complete rows only (x, y, z all present) |

## Submission contract

Write `artifacts/gc-390/stats.json` (path relative to the benchmark repo
root): a single JSON object mapping each of the 12 names above to a finite
number. Extra keys are ignored; missing or non-finite values count as
mismatches (fail-closed).

## Grading

    python3 assets/gc-390/grade.py

run from the repo root (stdlib-only; no third-party packages needed). The
grader verifies the sealed data hashes, recomputes all 12 statistics with an
independent implementation, cross-checks them against the sealed values, and
then compares your submission within per-statistic tolerance
`tol = max(1e-8, 1e-6 * |sealed value|)`. Its final stdout line is a JSON
object whose `stats_matched` field is the graded metric; the card passes at
`stats_matched >= 12`. A missing or malformed submission, or a tampered data
file, scores 0.
