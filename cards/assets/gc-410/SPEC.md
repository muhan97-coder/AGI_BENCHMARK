# gc-410 — iniread: build, then survive the adversarial suite

Build `work/gc-410/iniread.py` in two sealed stages. Stage 1 is the basic
parser; stage 2 pins down hostile edge cases and adds a canonical
serializer. Sealed assets are read-only; the grader integrity-checks them.

## Campaign artifacts (required, machine-checked)

- `work/gc-410/plan.md` — >= 400 bytes, headings `## Stage 1` and
  `## Stage 2`, written before stage 1 is sealed (frozen by the marker
  chain).
- `work/gc-410/stage1.json` — `{"stage": 1, "plan_sha256": "<sha256 of plan.md>"}`.
- `work/gc-410/stage2.json` — `{"stage": 2, "prev_sha256": "<sha256 of stage1.json bytes>"}`.
- `work/gc-410/runs.log` — JSON lines
  `{"ts": ..., "stage": ..., "cmd": ..., "passed": <int>, "failed": <int>}`,
  at least one entry per stage.

## Stage 1 — `parse(text) -> dict`

- Returns `{section_name: {key: value}}`. Keys appearing before any
  section header live in section `""`; that section is present ONLY if
  such keys exist.
- A section header is a line whose stripped form starts with `[` and
  ends with `]`; the name is the inner text, stripped. A header with no
  keys still appears in the result (empty dict). Duplicate sections merge.
- Lines whose stripped form is empty are ignored. Lines whose stripped
  form starts with `;` or `#` are comments.
- `key=value` splits on the FIRST `=`; key and value are stripped.
  Later `=` characters stay in the value. An empty key, or a
  non-comment non-blank line without `=`, raises `ValueError`.
- Duplicate keys within a section: last one wins.

Gate: `python -m pytest assets/gc-410/test_stage1.py -q` fully green.

## Stage 2 — adversarial pins and canonical serializer

Additional `parse` behavior:

- A trailing `\r` is stripped from every physical line first (CRLF input).
- Line continuation: after `\r` stripping, a physical line ending with a
  backslash continues: drop the backslash, strip the NEXT line's leading
  whitespace, and concatenate with no inserted character. Repeat while
  the joined line still ends with a backslash. Logical lines are then
  parsed normally.
- Tabs count as whitespace for all stripping. Values keep inline `;`
  and `#` (no inline comments). Keys are case-sensitive. `[]` names the
  empty-string section.

New function `serialize(data) -> str` (canonical form):

- Section `""` first (its keys emitted with NO header), then remaining
  sections sorted lexicographically, each as `[name]`.
- Keys sorted lexicographically, emitted as `key = value` (single spaces).
- Exactly one blank line BETWEEN section blocks, a single trailing
  newline at the end, and `serialize({}) == ""`.
- Round-trip: `parse(serialize(d)) == d` for values already in stripped
  form.

Gate: `python -m pytest assets/gc-410/test_stage2.py -q` fully green AND
the stage-1 suite still green (the grader re-runs both).

## Grading

`python assets/gc-410/grade.py` from the repo root emits one JSON line
with `campaign_score`. Every gate must pass.
