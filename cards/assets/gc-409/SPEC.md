# gc-409 — globlite: repair-then-extend campaign

The starter module `assets/gc-409/starter/globlite.py` ships with FOUR
seeded defects (identities B01..B04, discoverable from the sealed
regression suite's test names). Copy the starter to
`work/gc-409/globlite.py` and run the campaign in two sealed stages.
Sealed assets are read-only; the grader integrity-checks them.

## Behavior contract (stage 1 scope)

`match(pattern, name) -> bool` for single-segment glob patterns:

- `*` matches any run of characters, INCLUDING the empty run.
- `?` matches exactly one character (never zero).
- `[abc]` matches one character in the set; `[!abc]` matches one
  character NOT in the set. No ranges (`a-z` inside a class is three
  literal characters). The set may not contain `]`.
- An unclosed `[` is not an error: it is treated as a literal `[`
  character.
- Everything else matches literally; matching is case-sensitive.
- The whole name must be consumed (full match, not prefix).

## Campaign artifacts (required, machine-checked)

- `work/gc-409/plan.md` — >= 400 bytes, headings `## Stage 1` and
  `## Stage 2`, written before stage 1 is sealed.
- `work/gc-409/stage1.json` — `{"stage": 1, "plan_sha256": "<sha256 of plan.md>"}`.
- `work/gc-409/stage2.json` — `{"stage": 2, "prev_sha256": "<sha256 of stage1.json bytes>"}`.
- `work/gc-409/ledger.jsonl` — one JSON line per repaired defect:
  `{"id": "B01", "status": "fixed", "cause": "<what was wrong, >=10 chars>", "fix": "<what you changed, >=10 chars>"}`.
  All four ids B01, B02, B03, B04 must appear.
- `work/gc-409/runs.log` — JSON lines
  `{"ts": ..., "stage": ..., "cmd": ..., "passed": <int>, "failed": <int>}`,
  at least one entry per stage.

## Stage 1 — repair

Fix the four seeded defects until
`python -m pytest assets/gc-409/test_regress.py -q` is fully green.
Track each failure by identity in the ledger as you clear it.

## Stage 2 — extend with brace expansion

Add to `work/gc-409/globlite.py`:

- `expand_braces(pattern) -> list[str]` — expand `{a,b,c}` alternation
  groups left to right (cartesian product for multiple groups). A brace
  pair whose body contains no comma is NOT a group (the braces stay
  literal). An unmatched `{` or `}` stays literal. Empty alternatives are
  allowed (`a{,b}` expands to `a` and `ab`). Nested groups need not be
  supported. Duplicates are removed, keeping first-occurrence order.
- `match` must now accept brace patterns: the name matches if ANY
  expanded pattern matches.

Gate: `python -m pytest assets/gc-409/test_feature.py -q` fully green AND
the stage-1 regression suite still green (the grader re-runs both).

## Grading

`python assets/gc-409/grade.py` from the repo root emits one JSON line
with `campaign_score`. Every gate must pass.
