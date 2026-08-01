# gc-417 — triple-project repair ladder with failure-identity ledger

Three small projects ship with four seeded defects each (identities
discoverable from the sealed suites' test names): `proj_jsonl` (A01..A04),
`proj_queue` (Q01..Q04), `proj_tmpl` (T01..T04). Copy the starters from
`assets/gc-417/starters/` into `work/gc-417/pkgs/` (same filenames) and
clear them IN THE SEALED ORDER: jsonl (stage 1), then queue (stage 2),
then tmpl (stage 3). Stage 4 is the combined seal. Sealed assets are
read-only; the grader integrity-checks them.

## Campaign artifacts (required, machine-checked)

- `work/gc-417/plan.md` — >= 700 bytes, headings `## Stage 1` ..
  `## Stage 4`; written before stage 1 is sealed.
- Marker chain: `work/gc-417/stage1.json`
  `{"stage": 1, "plan_sha256": "<sha256 of plan.md>"}`, then
  `stage2.json` / `stage3.json` / `stage4.json` each
  `{"stage": k, "prev_sha256": "<sha256 of stage(k-1).json bytes>"}`.
- `work/gc-417/ledger.jsonl` — one JSON line per defect, all 12 ids:
  `{"id": "A01", "stage": 1, "status": "fixed", "cause": "<>=10 chars>",
  "fix": "<>=10 chars>"}`. The `stage` field must match the sealed order
  (A* -> 1, Q* -> 2, T* -> 3).
- `work/gc-417/runs.log` — JSON lines
  `{"ts": ..., "stage": ..., "cmd": ..., "passed": <int>, "failed": <int>}`;
  at least 8 entries and at least one per stage 1..4.

## Behavior contracts

### proj_jsonl (stage 1)

- `parse_lines(text)` — one JSON object per line; lines that are empty
  after stripping are skipped; a line that is valid JSON but not an
  object raises `ValueError`; invalid JSON raises `ValueError`.
- `filter_records(records, key, value)` — records where `key` is PRESENT
  and equals `value`; records missing the key are simply not matched.
- `summarize(records, key)` — `{"count": <all records>, "missing":
  <records without the key>, "distinct": <distinct present values>}`.
  Falsy values (`0`, `""`, `false`, `null`) are PRESENT values.

### proj_queue (stage 2)

- `new_queue()`, `push(q, item, priority)`, `pop(q)`, `peek(q)`,
  `qsize(q)`. `pop` returns the item with the LOWEST priority number;
  ties break FIFO. `peek` is non-destructive. `qsize` reflects pops.
  `pop`/`peek` on an empty queue raise `IndexError`. Items may be
  unhashable and non-comparable.

### proj_tmpl (stage 3)

- `render(template, ctx)` — `{name}` substitutes `str(ctx["name"])`;
  `{a.b}` walks nested dicts; `{{` and `}}` emit literal braces;
  a missing key raises `KeyError`; an unmatched `{`, an unmatched `}`,
  or an empty `{}` placeholder raises `ValueError`.

## Stage gates

Stage k is green when its sealed suite passes completely:
`python -m pytest assets/gc-417/test_proj_jsonl.py -q` (stage 1),
`test_proj_queue.py` (stage 2), `test_proj_tmpl.py` (stage 3).
Stage 4 = all three suites green in ONE combined run (the grader runs
the directory twice and requires identical results), ledger complete
and consistent, runs.log complete.

## Grading

`python assets/gc-417/grade.py` from the repo root emits one JSON line
with `campaign_score`. Every gate must pass.
