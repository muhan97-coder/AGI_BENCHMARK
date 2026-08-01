# csvcast — CSV to JSON Lines converter (spec v1)

Implement a command-line tool at `workspace/gc-397/csvcast.py` (relative to the
benchmark repo root). Invocation:

    python3 workspace/gc-397/csvcast.py [--strict]

It reads RFC-4180-style CSV from **stdin** (Python's `csv` module is allowed)
and writes **one compact JSON object per data row** to stdout (JSON Lines).

## Header
- The first CSV record is the header.
- Empty header names are replaced by `col<i>` where `<i>` is the 1-based column
  index. This replacement happens **before** deduplication.
- Duplicate header names are deduplicated left to right: the second occurrence
  of `name` becomes `name.2`, the third `name.3`, and so on.
- Output object keys appear in header (column) order.

## Type inference (applied to each raw cell string, no trimming)
Rules are checked in this order; first match wins:
1. `""` (empty cell) -> JSON `null`
2. case-insensitive `true` / `false` -> JSON boolean
3. case-insensitive `null` -> JSON `null`
4. integer: matches regex `^-?(0|[1-9][0-9]*)$` -> JSON integer
   (so `007` is NOT an integer; `-0` parses to `0`)
5. float: matches regex `^-?(0|[1-9][0-9]*)\.[0-9]+$` -> JSON number
   (so `1.`, `.5`, `00.5`, `1e5` are NOT floats)
6. otherwise -> JSON string (unchanged, no trimming: `" 42"` stays a string)

## Ragged rows (default mode)
- A data row with fewer cells than the header is padded with `null`.
- A data row with more cells: the surplus cells are collected, as **raw
  strings** (no type inference), into an extra key `"_extra"` (a JSON array)
  appended after the header keys.

## Ragged rows (--strict)
With `--strict`, the first ragged data row (shorter OR longer than the header)
aborts processing: rows before it are emitted normally, then the tool prints
`{"error": "ragged", "row": R}` (R = 1-based data-row number) as the final
line and exits with code **3**.

## Misc
- Completely empty stdin: print nothing, exit 0.
- Header only, no data rows: print nothing, exit 0.
- On success exit 0.

## Acceptance
Sealed suite: `assets/gc-397/test_accept.py`, run from the repo root with
pytest. Do not modify the test file.
