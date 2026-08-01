# gc-416 — datex: build the calendar core, harden calweeks, extend, audit

Four sealed stages over a month-scale campaign. You implement a pure
arithmetic date library (standard date modules BANNED in the
implementation file), harden the shipped ISO-week library by killing its
sealed mutants, extend with recurrence helpers, and close with an audit
seal. Sealed assets are read-only; the grader integrity-checks them.

## Campaign artifacts (required, machine-checked)

- `work/gc-416/plan.md` — >= 700 bytes, headings `## Stage 1` ..
  `## Stage 4`; written before stage 1 is sealed.
- Marker chain: `work/gc-416/stage1.json`
  `{"stage": 1, "plan_sha256": "<sha256 of plan.md>"}`, then
  `stage2.json` / `stage3.json` / `stage4.json` each
  `{"stage": k, "prev_sha256": "<sha256 of stage(k-1).json bytes>"}`.
- `work/gc-416/runs.log` — JSON lines
  `{"ts": ..., "stage": ..., "cmd": ..., "passed": <int>, "failed": <int>}`;
  at least 8 entries total and at least one per stage.
- `work/gc-416/cost.json` — `{"llm_usd": <number>, "grader_runs": <int>}`.

## Stage 1 — implement `work/gc-416/datex.py` (proleptic Gregorian, years 1..9999)

The file must NOT import `datetime`, `calendar`, `time`, `zoneinfo`, or
`dateutil` (the grader scans import lines). API — invalid dates and
out-of-range results raise `ValueError`:

- `is_leap(y)`; `days_in_month(y, m)` (bad month raises `ValueError`).
- `day_of_year(y, m, d)` -> 1..366.
- `to_ordinal(y, m, d)` -> days since 0001-01-01, where
  `to_ordinal(1, 1, 1) == 1`; `from_ordinal(n)` -> `(y, m, d)` inverse.
- `day_of_week(y, m, d)` -> 0=Monday .. 6=Sunday.
- `add_days(y, m, d, n)` -> `(y, m, d)` shifted by `n` (may be negative).
- `diff_days(a, b)` -> `to_ordinal(*a) - to_ordinal(*b)` for tuples.

Gate: `python -m pytest assets/gc-416/test_stage1.py -q` fully green.

## Stage 2 — kill the sealed mutants of `calweeks`

`assets/gc-416/calweeks.py` computes ISO-8601 `(iso_year, week, weekday)`
via `iso_week(y, m, d)`; `assets/gc-416/mutants/` holds 20 sealed
single-change mutants. Write a pytest suite under
`work/gc-416/killtests/` that:

- imports the target ONLY as `import calweeks` (do NOT ship a
  `calweeks.py` in that directory);
- is fully green on the original (>= 10 passing tests);
- fails on >= 18 of the 20 mutants.

Source introspection is banned (disqualifies). Survivor-by-survivor
triage is expected: track surviving mutant ids in your plan/runs.

## Stage 3 — recurrence helpers in `datex.py`

- `next_weekday(y, m, d, target)` -> first date STRICTLY after the input
  with `day_of_week == target` (target 0..6, else `ValueError`).
- `nth_weekday_of_month(y, m, target, n)` -> the nth (n >= 1) date in
  month `m` with that weekday, or the last when `n == -1`; missing nth or
  other `n` values raise `ValueError`.

Gate: `python -m pytest assets/gc-416/test_stage3.py -q` fully green AND
stage-1 suite still green.

## Stage 4 — audit seal

Seal `stage4.json` only when: runs.log is complete (every stage
represented), cost.json is filled honestly, and both suites plus the
mutation gate pass in one grading run. The grader also enforces a total
suite runtime budget of 60 seconds and the import ban.

## Grading

`python assets/gc-416/grade.py` from the repo root emits one JSON line
with `campaign_score`. Every gate must pass.
