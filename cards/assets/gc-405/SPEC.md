# globby — glob pattern matching engine (spec v1)

Implement a pure-Python module at `workspace/gc-405/globby.py` (relative to
the benchmark repo root).

**Hard constraint:** the implementation MUST NOT import `fnmatch` or
`pathlib` (the sealed suite scans the source). The `re` module IS allowed —
translating patterns to regular expressions is a legitimate strategy.

## API
- `match(pattern: str, path: str) -> bool` — full-path matching (the whole
  path must match, not a substring).
- `any_match(patterns: list[str], path: str) -> bool` — True iff at least
  one pattern matches.

Paths use `/` as the separator. Matching is case-sensitive. The empty
pattern matches only the empty path.

## Wildcards
- `*` matches any run (possibly empty) of characters EXCEPT `/`.
- `?` matches exactly one character EXCEPT `/`.
- Character classes `[...]`:
  - `[abc]` one char from the set; `[a-z]` ranges; multiple ranges and
    singles mix freely (`[a-cx-z0]`).
  - `[!...]` negates the set.
  - A `]` as the FIRST class char (after optional `!`) is a literal `]`:
    `[]a]` matches `]` or `a`; `[!]a]` matches anything except `]`, `a`
    (and `/`).
  - `-` first or last in the class is a literal `-` (`[a-]` = `a` or `-`).
  - A class NEVER matches `/`, even negated classes and even `[/]`.
  - An UNCLOSED `[` (no terminating `]`) is a literal `[` character.
  - Ranges are by code point; a reversed range like `[z-a]` matches nothing
    (but the class may still match its other members).

## Globstar `**` (deliberately tricky)
`**` is special ONLY when it occupies a whole path segment:
- pattern `**` matches every path (including the empty path).
- `**/rest` matches `rest` after ZERO or more leading segments:
  `**/foo.txt` matches `foo.txt`, `a/foo.txt`, `a/b/foo.txt`.
- `head/**` matches `head/` followed by one or more segments —
  `head/**` matches `head/x` and `head/x/y` but NOT `head` itself.
- `a/**/b` matches `a/b`, `a/x/b`, `a/x/y/b` (zero or more middle
  segments).
- When `**` appears INSIDE a segment (`a**b`, `**x`, `x**`), each `*` in it
  behaves like an ordinary `*` (non-slash), so `a**b` == `a*b` in effect.
- Multiple globstar segments may appear: `**/a/**` must work.

## Notes
- There is no escape character in this dialect: to match a literal `*`, use
  the class `[*]`; a literal `?` is `[?]`.
- All other characters (including `.`, `+`, `(`, `)`, spaces, unicode)
  match themselves literally — implementations translating to regex MUST
  escape them properly.

## Acceptance
Sealed suite: `assets/gc-405/test_accept.py`, run from the repo root with
pytest. Do not modify the test file.
