# gc-419 — logquery capstone: build, harden, extend, prove

Four sealed stages: build a log-query module on top of the shipped
`logfmt` parser, harden the parser by killing its sealed mutants, add
aggregations, then ship a CLI proven against goldens, a determinism
double-run, AND a probe log the grader generates fresh at grading time
(hard-coding goldens cannot pass). Sealed assets are read-only; the
grader integrity-checks them.

## Campaign artifacts (required, machine-checked)

- `work/gc-419/plan.md` — >= 700 bytes, headings `## Stage 1` ..
  `## Stage 4`; written before stage 1 is sealed.
- Marker chain: `work/gc-419/stage1.json`
  `{"stage": 1, "plan_sha256": "<sha256 of plan.md>"}`, then
  `stage2.json` / `stage3.json` / `stage4.json` each
  `{"stage": k, "prev_sha256": "<sha256 of stage(k-1).json bytes>"}`.
- `work/gc-419/runs.log` — JSON lines
  `{"ts": ..., "stage": ..., "cmd": ..., "passed": <int>, "failed": <int>}`;
  at least 8 entries, at least one per stage.
- `work/gc-419/cost.json` — `{"llm_usd": <number>, "grader_runs": <int>}`.

## Stage 1 — `work/gc-419/logquery.py`

Load the SEALED parser from `assets/gc-419/logfmt.py` (e.g. via
`importlib.util.spec_from_file_location`, path relative to the repo
root). API:

- `load(path)` — parse every line that is non-blank after stripping;
  return the list of dicts.
- `filter_records(records, key, op, value)` — ops `eq`, `ne`,
  `contains`, `gt`, `lt`; any other op raises `ValueError`. Records
  missing `key` never match. `eq`/`ne` use equality on the raw value.
  `contains`: only `str` values can match, substring test. `gt`/`lt`:
  compare `float(record_value)` with `float(value)`; records whose value
  does not coerce are excluded.

Gate: `python -m pytest assets/gc-419/test_stage1.py -q` fully green.

## Stage 2 — kill the sealed mutants of `logfmt`

`assets/gc-419/mutants/` holds 20 sealed single-change mutants. Write a
pytest suite under `work/gc-419/killtests/` that imports the target ONLY
as `import logfmt` (do NOT ship a `logfmt.py` there), is fully green on
the original (>= 10 passing tests), and fails on >= 18 of the 20
mutants. Source introspection is banned (disqualifies).

## Stage 3 — aggregations in `logquery.py`

- `count_by(records, key)` — dict `str(value) -> count` over records
  having the key.
- `stats(records, key)` — over float-coercible values:
  `{"count": n, "mean": round(sum/n, 6), "min": round(min, 6),
  "max": round(max, 6)}`; no coercible values raises `ValueError`.
- `top(records, key, n)` — list of `(value_str, count)` sorted by
  `(-count, value_str)`, first `n`.

Gate: `python -m pytest assets/gc-419/test_features.py -q` fully green
AND stage-1 suite still green.

## Stage 4 — `work/gc-419/cli.py`

- `python work/gc-419/cli.py count-by <key> <file>` — one line per value,
  `f"{value} {count}"`, sorted by `(-count, value)`. Exit 0.
- `python work/gc-419/cli.py stats <key> <file>` — four lines:
  `count N`, `mean X`, `min X`, `max X` where numbers are rendered with
  `str()` of the values from `stats` (floats keep their float form,
  e.g. `0.0`). Exit 0.
- Wrong argument count or unknown subcommand: exit 2, stderr starts
  with `usage:`. Unreadable file, parse error, or no numeric values for
  `stats`: exit 1, stderr starts with `error:`.

Goldens: `assets/gc-419/expected_countby.txt` (`count-by level`) and
`assets/gc-419/expected_stats.txt` (`stats bytes`) for
`assets/gc-419/sample.log`. The grader runs the CLI suite twice
(byte-identical results required) and additionally checks `count-by
level` on a generated probe log against its own reference computation.

Gate: `python -m pytest assets/gc-419/test_cli.py -q` fully green, twice.

## Grading

`python assets/gc-419/grade.py` from the repo root emits one JSON line
with `campaign_score`. Every gate must pass.
