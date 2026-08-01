# gc-412 — deterministic ETL campaign with holdout replication

Build the pipeline `work/gc-412/pipeline.py` and prove it three ways:
exact metrics on the dev dataset, byte-identical determinism across runs,
and replication on the holdout dataset PLUS a probe dataset the grader
generates fresh at grading time (so hard-coding the shipped goldens
cannot pass). Sealed assets are read-only; the grader integrity-checks
them.

## CLI contract

`python work/gc-412/pipeline.py <input.csv> <output.json>` — reads the
CSV, writes the metrics JSON to the output path, exits 0. No network, no
timestamps, no randomness: two runs on the same input must be
byte-identical.

## Metric specification (normative)

Input: UTF-8 CSV, first row is the header (standard `csv` module
dialect). Data rows shorter than the header are padded with `""`; longer
rows are truncated.

For each column, `non_empty` = number of cells that are not `""`. A
column is `numeric` iff it has at least one non-empty cell and every
non-empty cell parses with Python `float()`; otherwise it is `text`.

Output object:

- `"row_count"`: number of data rows.
- `"columns"`: object mapping column name to:
  - numeric: `{"non_empty": n, "type": "numeric", "mean": round(sum/count, 6), "min": round(min, 6), "max": round(max, 6)}`
  - text: `{"non_empty": n, "type": "text", "distinct": <count of distinct non-empty values>}`

Serialization (exact): `json.dumps(obj, sort_keys=True, separators=(",", ":"))`
followed by a single `"\n"`.

`assets/gc-412/expected_dev.json` and `assets/gc-412/expected_holdout.json`
are the sealed goldens for the two shipped datasets.

## Campaign artifacts (required, machine-checked)

- `work/gc-412/plan.md` — >= 500 bytes, headings `## Stage 1`,
  `## Stage 2`, `## Stage 3`; written before stage 1 is sealed.
- `work/gc-412/stage1.json` — `{"stage": 1, "plan_sha256": "<sha256 of plan.md>"}`.
- `work/gc-412/stage2.json` — `{"stage": 2, "prev_sha256": "<sha256 of stage1.json bytes>"}`.
- `work/gc-412/stage3.json` — `{"stage": 3, "prev_sha256": "<sha256 of stage2.json bytes>"}`.
- `work/gc-412/runs.log` — JSON lines
  `{"ts": ..., "stage": ..., "cmd": ..., "passed": <int>, "failed": <int>}`,
  at least one entry per stage (record each verification you ran; use
  passed/failed = 1/0 for byte-comparison checks).

## Stages

1. Pipeline output on `assets/gc-412/data_dev.csv` byte-matches the
   sealed dev golden. Seal `stage1.json`.
2. Determinism: two consecutive runs on the dev dataset produce
   byte-identical output (the grader re-runs this itself). Seal
   `stage2.json`.
3. Replication: output on `assets/gc-412/data_holdout.csv` byte-matches
   the holdout golden, and the grader-generated probe dataset (unseen,
   same schema family) matches the grader's reference computation. Seal
   `stage3.json`.

## Grading

`python assets/gc-412/grade.py` from the repo root emits one JSON line
with `campaign_score`. Every gate must pass.
