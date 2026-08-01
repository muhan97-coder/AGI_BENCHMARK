# gc-418 — querylang: four-increment feature ratchet

One module, `work/gc-418/querylang.py`, grown through four sealed
increments. Each stage adds language surface; every earlier suite must
stay green (the grader re-runs all of them, and the marker chain pins the
order). Sealed assets are read-only; the grader integrity-checks them.

## Campaign artifacts (required, machine-checked)

- `work/gc-418/plan.md` — >= 700 bytes, headings `## Stage 1` ..
  `## Stage 4`; written before stage 1 is sealed.
- Marker chain: `work/gc-418/stage1.json`
  `{"stage": 1, "plan_sha256": "<sha256 of plan.md>"}`, then
  `stage2.json` / `stage3.json` / `stage4.json` each
  `{"stage": k, "prev_sha256": "<sha256 of stage(k-1).json bytes>"}`.
- `work/gc-418/runs.log` — JSON lines
  `{"ts": ..., "stage": ..., "cmd": ..., "passed": <int>, "failed": <int>}`;
  at least TWO entries per stage (verify, then re-verify).
- `work/gc-418/cost.json` — `{"llm_usd": <number>, "grader_runs": <int>}`.

## Language contract

`evaluate(expr, record)` evaluates a filter expression against a dict and
returns the resulting value. All language errors raise
`QueryError(message, pos)` — an exception class exported by the module
with attributes `message` (str) and `pos` (0-based character offset of
the offending token; end-of-input errors use `len(expr)`).

### Stage 1 — literals, fields, comparisons

- Literals: integers, floats (`\d+(\.\d+)?`), single-quoted strings with
  `\'` and `\\` escapes, `true`, `false`, `null`.
- A bare identifier (not a keyword) reads `record.get(name)`; a missing
  field is `null`.
- `== !=` compare any two values (Python equality; `null == null` is
  true). `< <= > >=` require two numbers (bool is NOT a number) or two
  strings; anything else raises QueryError at the operator position.
- Trailing tokens after a complete expression raise QueryError.
- Errors: unterminated string (pos of the opening quote), bad escape
  (pos of the backslash), unexpected character (its pos).

Gate: `python -m pytest assets/gc-418/test_stage1.py -q` fully green.

### Stage 2 — boolean logic

- `or` < `and` < `not` in binding strength; parentheses group.
- Operands of `and` / `or` / `not` must be actual booleans, else
  QueryError at the operator position; no truthiness.
- Short-circuit: the right operand is not evaluated when the left
  decides (`false and X`, `true or X`), so eval-time errors inside the
  skipped side do not fire.

Gate: `python -m pytest assets/gc-418/test_stage2.py -q` fully green.

### Stage 3 — functions

`len(s)`, `lower(s)`, `upper(s)`, `abs(x)`, `contains(haystack, needle)`,
`startswith(s, prefix)`. Calls nest anywhere a value fits. Errors at the
function-name position: unknown function, wrong argument count, wrong
argument type.

Gate: `python -m pytest assets/gc-418/test_stage3.py -q` fully green.

### Stage 4 — error identity audit

`QueryError.pos` values are pinned exactly (see the sealed suite):
unterminated string, bad escape, unexpected character, unexpected/trailing
token, unclosed parenthesis (pos = `len(expr)`), ordering-null operator
position, unknown-function position, arity position.

Gate: `python -m pytest assets/gc-418/test_stage4.py -q` fully green AND
stages 1-3 still green. Total suite runtime budget: 60 s.

## Grading

`python assets/gc-418/grade.py` from the repo root emits one JSON line
with `campaign_score`. Every gate must pass.
