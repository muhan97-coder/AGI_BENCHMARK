# gc-414 — romanx: test-first, implement, ship the CLI

Three sealed stages, test-first: you must FIRST demonstrate you can pin
the behavior of the sealed reference `assets/gc-414/romanx.py` by killing
its mutants, THEN build the full module and a CLI on top. Sealed assets
are read-only; the grader integrity-checks them.

## Reference behavior (normative for stages 1 and 2)

- `to_roman(n)` — canonical Roman numeral for integers 1..3999.
  Non-`int` values, `bool` values, and out-of-range ints raise
  `ValueError`.
- `from_roman(s)` — inverse, STRICT: accepts only the canonical form
  produced by `to_roman` (e.g. `"IIII"`, `"VX"`, `""`, lowercase all
  raise `ValueError`).

## Campaign artifacts (required, machine-checked)

- `work/gc-414/plan.md` — >= 500 bytes, headings `## Stage 1`,
  `## Stage 2`, `## Stage 3`; written before stage 1 is sealed.
- `work/gc-414/stage1.json` — `{"stage": 1, "plan_sha256": "<sha256 of plan.md>"}`.
- `work/gc-414/stage2.json` — `{"stage": 2, "prev_sha256": "<sha256 of stage1.json bytes>"}`.
- `work/gc-414/stage3.json` — `{"stage": 3, "prev_sha256": "<sha256 of stage2.json bytes>"}`.
- `work/gc-414/runs.log` — JSON lines
  `{"ts": ..., "stage": ..., "cmd": ..., "passed": <int>, "failed": <int>}`,
  at least one entry per stage.
- `work/gc-414/cost.json` — `{"llm_usd": <number>, "grader_runs": <int>}`.

## Stage 1 — kill the sealed mutants

`assets/gc-414/mutants/` holds 12 sealed single-change mutants of the
reference. Write a pytest suite under `work/gc-414/killtests/` that:

- imports the target ONLY as `import romanx` (the grader supplies the
  module path; do NOT ship a `romanx.py` inside that directory);
- is fully green against the original (>= 8 passing tests);
- fails against >= 10 of the 12 mutants.

Source introspection (`__file__`, `getsource`, file reads, hashing) is
banned and disqualifies the gate. Behavior only.

## Stage 2 — implement `work/gc-414/romanx_full.py`

Same `to_roman` / `from_roman` contract as the reference, PLUS:

- `is_valid(s) -> bool` — `True` iff `from_roman(s)` would accept `s`;
  never raises for `str` input.
- `roman_range(start, stop, step=1)` — generator yielding
  `to_roman(v)` for `v in range(start, stop, step)`. Raises `ValueError`
  eagerly (at call time) if `step == 0` or if any yielded value would
  fall outside 1..3999. An empty range is fine.

Gate: `python -m pytest assets/gc-414/test_full.py -q` fully green.

## Stage 3 — ship `work/gc-414/cli.py`

- `python work/gc-414/cli.py to 14` prints `XIV` + newline, exit 0.
- `python work/gc-414/cli.py from XIV` prints `14` + newline, exit 0.
- Invalid value for a valid subcommand: exit 2, nothing on stdout, and
  stderr starting with `error:`.
- Unknown subcommand or wrong argument count: exit 2, nothing on stdout,
  stderr starting with `usage:`.

Gate: `python -m pytest assets/gc-414/test_cli.py -q` fully green AND the
stage-2 suite still green (the grader re-runs both).

## Grading

`python assets/gc-414/grade.py` from the repo root emits one JSON line
with `campaign_score`. Every gate must pass.
