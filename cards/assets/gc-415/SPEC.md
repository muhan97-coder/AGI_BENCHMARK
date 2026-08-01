# gc-415 — toksmith + tableform: interleaved build with integration finale

Build two independent modules in enforced order, then integrate them into
a report tool whose output is pinned byte-exactly. Sealed assets are
read-only; the grader integrity-checks them.

## Campaign artifacts (required, machine-checked)

- `work/gc-415/plan.md` — >= 500 bytes, headings `## Stage 1`,
  `## Stage 2`, `## Stage 3`; written before stage 1 is sealed.
- `work/gc-415/stage1.json` — `{"stage": 1, "plan_sha256": "<sha256 of plan.md>"}`.
- `work/gc-415/stage2.json` — `{"stage": 2, "prev_sha256": "<sha256 of stage1.json bytes>"}`.
- `work/gc-415/stage3.json` — `{"stage": 3, "prev_sha256": "<sha256 of stage2.json bytes>"}`.
- `work/gc-415/runs.log` — JSON lines
  `{"ts": ..., "stage": ..., "cmd": ..., "passed": <int>, "failed": <int>}`,
  at least one entry per stage.

## Stage 1 — `work/gc-415/toksmith.py`

`tokenize(text) -> list[(kind, value, pos)]`, `pos` = index of the
token's first character:

- `NUMBER`: maximal `\d+(\.\d+)?`; value is `int` when there is no dot,
  else `float`.
- `WORD`: `[A-Za-z_][A-Za-z0-9_]*`.
- `STRING`: double-quoted; escapes `\"` and `\\` only (value is the
  unescaped text). Any other backslash escape raises
  `ValueError("bad escape at <i>")`; a string that never closes raises
  `ValueError("unterminated string at <start>")`.
- `OP`: one character from `+-*/=(),<>`; value is that character.
- Spaces, tabs, `\r`, `\n` are skipped. Any other character raises
  `ValueError` mentioning the position.
- Longest-match: `12abc` tokenizes as NUMBER 12 then WORD `abc`.

Gate: `python -m pytest assets/gc-415/test_toksmith.py -q` fully green.

## Stage 2 — `work/gc-415/tableform.py`

`render(headers, rows) -> str` (ASCII grid):

- `headers`: non-empty list of strings (empty raises `ValueError`);
  every row must have the same length as `headers` (else `ValueError`).
- Column width = max cell length over the header and all rows.
- Data/header line: `"| " + " | ".join(cell.ljust(width)) + " |"`.
- After the header line comes a separator line whose cells are
  `"-" * width`.
- Lines joined with `"\n"`, plus a single trailing `"\n"`.

Gate: `python -m pytest assets/gc-415/test_tableform.py -q` fully green.

## Stage 3 — `work/gc-415/report.py` (integration)

`python work/gc-415/report.py <file>`:

- Wrong argument count: exit 2, stderr starts with `usage:`.
- Unreadable file or tokenization error: exit 1, stderr starts with
  `error:`.
- Otherwise: tokenize the file with `toksmith`, count WORD tokens
  (case-sensitive; STRING contents do NOT count), take the top 5 by
  `(-count, word)`, and print `tableform.render(["word", "count"], rows)`
  with counts as strings. Exit 0.

`assets/gc-415/expected_report.txt` is the sealed golden for
`assets/gc-415/sample_input.txt`.

Gate: `python -m pytest assets/gc-415/test_report.py -q` fully green AND
stages 1-2 suites still green (the grader re-runs everything).

## Grading

`python assets/gc-415/grade.py` from the repo root emits one JSON line
with `campaign_score`. Every gate must pass.
