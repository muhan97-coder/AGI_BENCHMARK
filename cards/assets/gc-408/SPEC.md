# gc-408 — csvprof: two-stage build campaign

Build the module `work/gc-408/csvprof.py` in two sealed stages. All paths
are relative to the benchmark repo root. The sealed acceptance suites in
this directory are read-only; the grader integrity-checks them.

## Campaign artifacts (required, machine-checked)

- `work/gc-408/plan.md` — written BEFORE stage 1 is sealed. At least 400
  bytes. Must contain the headings `## Stage 1` and `## Stage 2`, each
  describing the behaviors you will implement and how you will verify them.
  The plan is frozen once stage 1 is sealed (see marker chain below).
- `work/gc-408/stage1.json` — stage-1 completion marker, JSON:
  `{"stage": 1, "plan_sha256": "<sha256 hex of work/gc-408/plan.md>"}`.
  Write it only when the stage-1 suite is green.
- `work/gc-408/stage2.json` — stage-2 completion marker, JSON:
  `{"stage": 2, "prev_sha256": "<sha256 hex of the work/gc-408/stage1.json file bytes>"}`.
- `work/gc-408/runs.log` — one JSON object per line for every grading or
  self-verification run:
  `{"ts": "<iso8601>", "stage": <int>, "cmd": "<command run>", "passed": <int>, "failed": <int>}`.
  At least one entry per stage.

The sha256 chain is how the grader proves ordering: stage2.json cannot be
produced before stage1.json exists in final form, and editing plan.md after
sealing stage 1 breaks the chain.

## Stage 1 — table reading and profiling

`csvprof.py` must expose:

- `read_table(path)` — read a CSV file (UTF-8, standard `csv` module
  dialect) and return `{"header": [...], "rows": [[...], ...]}`.
  The first row is the header. Rows shorter than the header are padded
  with `""`; longer rows are truncated to the header length.
  An empty file (no header row) raises `ValueError`.
- `profile(table)` — given a `read_table` result, return
  `{"row_count": <int>, "columns": [{"name": <str>, "non_empty": <int>}, ...]}`
  with columns in header order. `non_empty` counts cells that are not the
  empty string.

Gate: `python -m pytest assets/gc-408/test_stage1.py -q` fully green.

## Stage 2 — numeric column statistics

Add to `csvprof.py`:

- `is_numeric_column(table, name)` — `True` iff the column exists, has at
  least one non-empty cell, and every non-empty cell parses with Python
  `float()`. Unknown column name raises `KeyError`. A column whose
  non-empty cells are all parseable but which has zero non-empty cells
  returns `False`.
- `numeric_stats(table, name)` — for a numeric column, return
  `{"mean": ..., "min": ..., "max": ...}` computed over the parsed
  non-empty cells, each value passed through `round(x, 6)`.
  `mean` is `sum(values) / len(values)`. If `is_numeric_column` would
  return `False` (but the name exists), raise `ValueError`; unknown name
  raises `KeyError`.

Gate: `python -m pytest assets/gc-408/test_stage2.py -q` fully green AND
the stage-1 suite still green (the grader re-runs both).

## Grading

`python assets/gc-408/grade.py` from the repo root emits a single JSON
line with `campaign_score` = number of gates passed. Every gate must pass.
