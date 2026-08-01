# gc-411 — unitconv: implement, harden the dependency, extend

Three sealed stages. You will (1) implement a unit-conversion module from
this spec, (2) harden your confidence in the shipped prefix library
`assets/gc-411/siunits.py` by writing a test suite that kills its sealed
mutants, and (3) extend your module with compound speed units. Sealed
assets are read-only; the grader integrity-checks them.

## Campaign artifacts (required, machine-checked)

- `work/gc-411/plan.md` — >= 500 bytes, headings `## Stage 1`,
  `## Stage 2`, `## Stage 3`; written before stage 1 is sealed.
- `work/gc-411/stage1.json` — `{"stage": 1, "plan_sha256": "<sha256 of plan.md>"}`.
- `work/gc-411/stage2.json` — `{"stage": 2, "prev_sha256": "<sha256 of stage1.json bytes>"}`.
- `work/gc-411/stage3.json` — `{"stage": 3, "prev_sha256": "<sha256 of stage2.json bytes>"}`.
- `work/gc-411/runs.log` — JSON lines
  `{"ts": ..., "stage": ..., "cmd": ..., "passed": <int>, "failed": <int>}`,
  at least one entry per stage.
- `work/gc-411/cost.json` — `{"llm_usd": <number>, "grader_runs": <int>}`,
  honest totals for the whole campaign.

## Stage 1 — implement `work/gc-411/unitconv.py`

Conversion factors (exact, to the base unit of each dimension):

- length (base m): `m` 1.0, `km` 1000.0, `mi` 1609.344, `ft` 0.3048
- mass (base kg): `kg` 1.0, `g` 0.001, `lb` 0.45359237, `oz` 0.028349523125
- time (base s): `s` 1.0, `min` 60.0, `h` 3600.0

API:

- `dimension_of(unit) -> "length" | "mass" | "time"`; unknown unit raises
  `KeyError`.
- `convert(value, from_unit, to_unit) -> float` =
  `round(value * F[from_unit] / F[to_unit], 9)`. Unknown units raise
  `KeyError`; units of different dimensions raise `ValueError`.

Gate: `python -m pytest assets/gc-411/test_stage1.py -q` fully green.

## Stage 2 — kill the sealed mutants of `siunits`

`assets/gc-411/mutants/` contains 15 sealed single-change mutants of
`siunits.py`. Write a pytest suite under `work/gc-411/killtests/`
(files `test_*.py`) that:

- imports the target ONLY as `import siunits` (the grader supplies the
  module path; do NOT ship your own `siunits.py` in that directory);
- passes completely against the original `assets/gc-411/siunits.py`
  (baseline must be green, at least 8 passing tests);
- fails (at least one test) against >= 12 of the 15 mutants.

Tests must probe behavior only: source introspection (`__file__`,
`getsource`, file reads, hashing) is banned and disqualifies the gate.

## Stage 3 — extend with compound speed units

Add to `work/gc-411/unitconv.py`:

- `convert_speed(value, from_unit, to_unit) -> float` for units of the
  form `"<length>/<time>"` (e.g. `"km/h"`, `"m/s"`, `"mi/h"`, `"ft/s"`).
  Factor of `"L/T"` is `F[L] / F[T]` (to m/s); result =
  `round(value * factor_from / factor_to, 9)`.
  A unit without exactly one `/`, or with an unknown part, raises
  `ValueError`. The numerator must be a length unit and the denominator a
  time unit, else `ValueError`.

Gate: `python -m pytest assets/gc-411/test_stage3.py -q` fully green AND
the stage-1 suite still green (the grader re-runs both).

## Grading

`python assets/gc-411/grade.py` from the repo root emits one JSON line
with `campaign_score`. Every gate must pass.
