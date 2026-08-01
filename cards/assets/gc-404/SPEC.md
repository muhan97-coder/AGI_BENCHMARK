# microjson — strict RFC 8259 JSON parser + serializer (spec v1)

Implement a pure-Python module at `workspace/gc-404/microjson.py` (relative
to the benchmark repo root).

**Hard constraint:** the implementation MUST NOT use Python's built-in JSON
machinery. The sealed suite scans the source file and fails if it matches
`import json`, `from json`, `__import__` or `importlib`. Everything else in
the standard library is allowed.

## `loads(s: str) -> object`
Strict RFC 8259 parser: objects -> `dict`, arrays -> `list`, strings ->
`str`, `true`/`false` -> `bool`, `null` -> `None`. Numbers: `int` when the
literal has no `.`, `e`, or `E`; otherwise `float` (`1e2` is the float
`100.0`; `-0` is the int `0`).

### Must REJECT (raise `ValueError`)
- trailing commas: `[1,]`, `{"a":1,}`
- single quotes, unquoted keys, comments
- `NaN`, `Infinity`, `-Infinity`
- leading zeros (`01`, `-01`), `+1`, `.5`, `5.`, `0x10`, `1.`, `.e1`
- raw control characters U+0000..U+001F inside strings (must be escaped)
- invalid escapes (`\x`, `\'`), capital `\U` escapes
- lone UTF-16 surrogates: `"\uD800"` without a following low surrogate is an
  error; `"😀"` is one astral code point
- any garbage after the document (`{} x`), empty input, truncated documents
- whitespace is only space, tab, `\n`, `\r`

### Duplicate keys
Last occurrence wins: `{"a":1,"a":2}` -> `{"a": 2}`.

### Error positions
`ValueError` messages MUST contain the substring `line L col C` (1-based)
locating the FIRST character that cannot continue a valid document. Lines
split on `\n`; col counts characters (not bytes) from 1. Examples:
- `loads('[1,]')` -> error mentions `line 1 col 4` (the `]`)
- `loads('{"a": @}')` -> error mentions `line 1 col 7` (the `@`)
- `loads('[1,\n 2,,')` -> error mentions `line 2 col 4` (the second comma)
For unexpected end of input the position is one past the last character.

## `dumps(v) -> str`
- Compact: no spaces after `,` or `:`.
- Object keys sorted with plain Python `sorted()` on the key strings; only
  `str` keys are legal -> otherwise `TypeError`.
- Escapes in strings: exactly `\"`, `\\`, `\b`, `\f`, `\n`, `\r`, `\t`, and
  `\u00XX` (lowercase hex) for the remaining control chars < U+0020. All
  other characters, including non-ASCII, are emitted raw (UTF-8 friendly).
- `int` via `str()`; `float` via `repr()`; `True`/`False`/`None` ->
  `true`/`false`/`null`. Floats that are NaN or infinite -> `ValueError`.
- Accepted container types: `dict`, `list`, `tuple` (tuple serializes as
  array). Any other type (set, bytes, custom) -> `TypeError`.
- `bool` must serialize as `true`/`false`, NOT as `1`/`0` (test the
  isinstance order: `True` is an `int` subclass in Python).

## Round trip
For any value built from the accepted types, `loads(dumps(v))` must equal
`v` (tuples become lists).

## Acceptance
Sealed suite: `assets/gc-404/test_accept.py`, run from the repo root with
pytest. Do not modify the test file.
