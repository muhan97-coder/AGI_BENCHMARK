# wordtally — word frequency CLI (spec v1)

Implement a command-line tool at `workspace/gc-396/wordtally.py` (relative to the
benchmark repo root). It is invoked as:

    python3 workspace/gc-396/wordtally.py [--top N] [--min-len K] [--min-count C]

It reads UTF-8 text from **stdin** and writes exactly **one line of JSON** to stdout.

## Tokenization
1. Lowercase the entire input using Python `str.lower()` semantics.
2. A token is a maximal run of characters from the set `[a-z0-9']`
   (ASCII lowercase letters, ASCII digits, apostrophe `'`). Every other
   character (punctuation, whitespace, non-ASCII letters, etc.) is a separator.
3. Strip leading and trailing apostrophes from each token
   (`'tis` -> `tis`, `''x''` -> `x`). Interior apostrophes are kept
   (`don't` stays `don't`, `rock'n'roll` stays `rock'n'roll`).
4. Tokens that are empty after stripping are discarded.

## Options
- `--top N` (default 10): emit at most N entries. `N >= 0`. `--top 0` emits an
  empty entries list.
- `--min-len K` (default 1): only tokens whose length (after apostrophe
  stripping) is `>= K` are counted at all. `K >= 1`.
- `--min-count C` (default 1): only words with a final count `>= C` may appear
  in entries. `C >= 1`.

Option values must parse as base-10 integers and satisfy the bounds above.
Any violation, or any unknown option, is a usage error: print exactly
`{"error": "usage"}` as a single JSON line to stdout and exit with code **2**.

## Output
On success print one compact JSON object and exit 0:

    {"total_tokens": T, "entries": [[word, count], ...]}

- `total_tokens` = number of tokens counted, i.e. the number of tokens that
  survived tokenization and the `--min-len` filter (equivalently, the sum of
  all counts before `--min-count` / `--top` are applied).
- `entries` = word/count pairs sorted by count **descending**, ties broken by
  word **ascending** (codepoint order), filtered by `--min-count`, then
  truncated to `--top`.
- Empty input is not an error: `{"total_tokens": 0, "entries": []}`, exit 0.

## Examples
    echo "The the THE cat" | python3 workspace/gc-396/wordtally.py --top 2
    -> {"total_tokens": 4, "entries": [["the", 3], ["cat", 1]]}

## Acceptance
The sealed suite `assets/gc-396/test_accept.py` is run from the repo root with
pytest. All tests must pass. Do not modify the test file.
