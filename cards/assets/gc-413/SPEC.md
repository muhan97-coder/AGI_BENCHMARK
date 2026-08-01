# gc-413 — textindex legacy rescue: repair, speed up, extend

The starter `assets/gc-413/starter/textindex.py` is a small inverted-index
module with FIVE seeded defects (identities D01..D05, discoverable from
the sealed suite's test names) and a linear-scan lookup that busts the
sealed comparison budget. Copy it to `work/gc-413/textindex.py` and run
three sealed stages. Sealed assets are read-only; the grader
integrity-checks them.

## Behavior contract

- `tokenize(text) -> list[str]` — lowercase the text, split into maximal
  runs of ASCII alphanumerics (`[0-9A-Za-z]+`), drop empty strings.
- `build_index(docs: list[str]) -> index` — the index representation is
  REQUIRED to be `{"keys": <sorted list of distinct tokens>, "postings":
  <list aligned with keys; each entry the sorted distinct doc ids
  containing that token>}`. `build_index([])` returns
  `{"keys": [], "postings": []}`.
- `lookup(index, token) -> list[int]` — doc ids for an exact token,
  `[]` when absent.

## Campaign artifacts (required, machine-checked)

- `work/gc-413/plan.md` — >= 500 bytes, headings `## Stage 1`,
  `## Stage 2`, `## Stage 3`; written before stage 1 is sealed.
- `work/gc-413/stage1.json` — `{"stage": 1, "plan_sha256": "<sha256 of plan.md>"}`.
- `work/gc-413/stage2.json` — `{"stage": 2, "prev_sha256": "<sha256 of stage1.json bytes>"}`.
- `work/gc-413/stage3.json` — `{"stage": 3, "prev_sha256": "<sha256 of stage2.json bytes>"}`.
- `work/gc-413/ledger.jsonl` — one JSON line per repaired defect:
  `{"id": "D01", "status": "fixed", "cause": "<>=10 chars>", "fix": "<>=10 chars>"}`
  for all of D01..D05.
- `work/gc-413/runs.log` — JSON lines
  `{"ts": ..., "stage": ..., "cmd": ..., "passed": <int>, "failed": <int>}`,
  at least one entry per stage.

## Stage 1 — repair the five seeded defects

`python -m pytest assets/gc-413/test_defects.py -q` fully green, ledger
complete.

## Stage 2 — meet the sealed comparison budget

`lookup` must locate tokens using an ordered strategy (e.g. binary search
over `keys`). The sealed perf suite builds a 4096-token index and issues
50 lookups with instrumented keys that count rich comparisons; the total
must be <= 2500 (a linear scan measures ~100k). Correctness is asserted
on the same instrumented keys.

Gate: `python -m pytest assets/gc-413/test_perf.py -q` fully green.

## Stage 3 — add prefix search

- `prefix_search(index, prefix) -> list[int]` — sorted distinct doc ids
  of all tokens starting with `prefix`. `prefix_search(index, "")`
  returns all doc ids present in the index. Must not mutate the index.

Gate: `python -m pytest assets/gc-413/test_feature.py -q` fully green AND
the earlier suites still green (the grader re-runs everything).

## Grading

`python assets/gc-413/grade.py` from the repo root emits one JSON line
with `campaign_score`. Every gate must pass.
