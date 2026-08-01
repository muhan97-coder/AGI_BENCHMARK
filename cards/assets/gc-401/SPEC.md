# tably — deterministic ASCII table renderer (spec v1)

Implement a pure-Python module at `workspace/gc-401/tably.py` (relative to the
benchmark repo root). Standard library only. One public function:

    render(headers, rows, aligns=None, max_col=None) -> str

## Inputs
- `headers`: non-empty list; each item rendered with `str()`. Empty list or
  non-list -> `ValueError`.
- `rows`: list of sequences. Every cell is rendered with `str()` (so `None`
  becomes `"None"`, `3` becomes `"3"`).
  - A row SHORTER than headers is right-padded with empty-string cells.
  - A row LONGER than headers -> `ValueError`.
- `aligns`: `None` (all left) or a string over the alphabet `l`, `r`, `c`
  (left/right/center), one char per column, applied left to right. Shorter
  strings are padded with `l`. A string longer than the column count or
  containing any other character -> `ValueError`.
- `max_col`: `None` or an `int >= 4` (else `ValueError`). Caps every column
  width.

## Layout algorithm (exact)
1. Column natural width = max over `len()` of the header and every cell in
   that column (after `str()` conversion). With no data rows, it is the
   header length.
2. If `max_col` is given, width = `min(natural, max_col)`.
3. Any cell or header longer than its column width is truncated to
   `width - 3` characters plus `"..."`.
4. Cell field of width W: left = text then spaces; right = spaces then text;
   center = `pad // 2` spaces on the left, the remainder on the right.
5. Every content line is `| ` + field + ` | ` + field + ... + ` |`
   (i.e. one space padding inside each pipe).
6. The separator line (second line) is `|` + `-` * (W+2) per column + `|`.
7. Output = header line, separator line, then one line per data row, joined
   with `"\n"`. NO trailing newline.

## Worked examples (normative)
    render(["name", "qty"], [["apple", 3], ["kiwi", 12]])
    == "| name  | qty |\n|-------|-----|\n| apple | 3   |\n| kiwi  | 12  |"

    render(["name", "qty"], [["apple", 3], ["kiwi", 12]], aligns="lr")
    == "| name  | qty |\n|-------|-----|\n| apple |   3 |\n| kiwi  |  12 |"

    render(["h"], [["abcdefghij"]], max_col=6)
    == "| h      |\n|--------|\n| abc... |"

    render(["a", "b"], [[1]], aligns="cc")
    == "| a | b |\n|---|---|\n| 1 |   |"

    render(["col"], [])
    == "| col |\n|-----|"

## Acceptance
Sealed suite: `assets/gc-401/test_accept.py`, run from the repo root with
pytest. Do not modify the test file.
