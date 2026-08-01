# gc-393 -- Reproduce a sealed fixed-init Lloyd k-means trajectory

## Dataset

400 two-dimensional points (columns: point_id, px, py) drawn from three Gaussian blobs and shuffled.

File(s): `assets/gc-393/data.csv`. Total size is under 100KB. The data is synthetic and
public-domain; regenerate it byte-identically (stdlib only, fixed seed) with:

    python3 assets/gc-393/make_dataset.py

run from the benchmark repo root. The sha256 of each data file is sealed in
`assets/gc-393/expected_stats.json` and is checked by the grader, so the
bundled data must not be modified.

## General conventions

- Parse numeric CSV fields as IEEE-754 doubles exactly as written.
- "sample" variance/std uses the n-1 denominator.
- quantile(q) uses linear interpolation between order statistics (Type 7, the
  numpy/pandas default): on the ascending sorted sample s (0-indexed) let
  h = (n-1)*q; the result is s[floor(h)] + (h-floor(h)) * (s[floor(h)+1] - s[floor(h)]).
- median = quantile(0.5).
- Count-valued statistics are submitted as numbers like every other statistic.
- Algorithm (normative): centroids start at exactly (0.0, 1.0), (0.5, 2.0), (1.0, 3.0) in that index order. All three deliberately sit in the central overlap region, so the trajectory takes several iterations to separate. Loop: (1) assign every point to the centroid with the smallest squared Euclidean distance, breaking ties by the lowest centroid index; (2) if this assignment vector is identical to the previous iteration's, STOP; (3) recompute each centroid as the arithmetic mean of its assigned points; go to (1).
- iterations counts assignment passes including the final repeated one; the final centroids are the ones in effect when the repeat is detected (the means of the converged assignment).

## The 12 sealed statistics

| # | name | definition |
|---|------|------------|
| 1 | `final_inertia` | sum over points of squared Euclidean distance to the final centroid of the point's final cluster |
| 2 | `iterations` | number of assignment passes performed, INCLUDING the final pass whose assignment equals the previous one (see algorithm below) |
| 3 | `size_c0` | final number of points assigned to centroid index 0 |
| 4 | `size_c1` | final number of points assigned to centroid index 1 |
| 5 | `size_c2` | final number of points assigned to centroid index 2 |
| 6 | `centroid0_x` | final x coordinate of centroid 0 |
| 7 | `centroid0_y` | final y coordinate of centroid 0 |
| 8 | `centroid1_x` | final x coordinate of centroid 1 |
| 9 | `centroid1_y` | final y coordinate of centroid 1 |
| 10 | `centroid2_x` | final x coordinate of centroid 2 |
| 11 | `centroid2_y` | final y coordinate of centroid 2 |
| 12 | `min_intercentroid_dist` | minimum pairwise Euclidean distance between the three final centroids |

## Submission contract

Write `artifacts/gc-393/stats.json` (path relative to the benchmark repo
root): a single JSON object mapping each of the 12 names above to a finite
number. Extra keys are ignored; missing or non-finite values count as
mismatches (fail-closed).

## Grading

    python3 assets/gc-393/grade.py

run from the repo root (stdlib-only; no third-party packages needed). The
grader verifies the sealed data hashes, recomputes all 12 statistics with an
independent implementation, cross-checks them against the sealed values, and
then compares your submission within per-statistic tolerance
`tol = max(1e-8, 1e-6 * |sealed value|)`. Its final stdout line is a JSON
object whose `stats_matched` field is the graded metric; the card passes at
`stats_matched >= 12`. A missing or malformed submission, or a tampered data
file, scores 0.
