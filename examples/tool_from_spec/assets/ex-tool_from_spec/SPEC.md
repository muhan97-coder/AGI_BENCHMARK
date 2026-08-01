# numstat — integer stream summariser (spec v1, teaching example)

Implement a command-line tool at `workspace/ex-tool_from_spec/numstat.py`
(relative to the workspace root). It is invoked as:

    python3 workspace/ex-tool_from_spec/numstat.py [--min M] [--top N]

It reads UTF-8 text from **stdin** and writes exactly **one line of JSON** to
stdout.

This is the worked example for the `tool_from_spec` category. It is not a
scored card; it mirrors the shape of e.g. `gc-396` (`wordtally`) at a size that
grades in about a second.

## Tokenization

1. Split stdin on **any whitespace** (`str.split()` semantics): runs of
   whitespace separate tokens, leading/trailing whitespace is ignored.
2. A token is a **value** if and only if it matches `^-?[0-9]+$` — an optional
   single leading minus sign followed by one or more ASCII digits. Values are
   parsed as base-10 integers.
3. Every token that is not a value is **skipped**. `+5`, `3.0`, `1_000`, `--`,
   `abc`, `1e3` and `٣` are all skipped.

## Options

- `--min M` (default: **no lower bound**, i.e. every value is kept): only
  values `>= M` are **kept**. `M` may be any integer, including negative.
- `--top N` (default `3`): emit at most `N` entries. `N >= 0`. `--top 0` emits
  an empty entries list.

Option values must parse as base-10 integers (same `^-?[0-9]+$` rule) and
satisfy the bounds above. Any violation, any unknown option, and any option
given without a value is a **usage error**: print exactly `{"error": "usage"}`
as a single JSON line to stdout and exit with code **2**.

## Output

On success print one compact JSON object and exit 0:

    {"kept": K, "skipped": S, "sum": SUM, "entries": [[value, count], ...]}

- `skipped` = the number of **non-value tokens**. It is counted during
  tokenization and is **not** affected by `--min`: a value filtered out by
  `--min` is *not* skipped, it is simply not kept.
- `kept` = the number of values that survive the `--min` filter (duplicates
  counted each time).
- `sum` = the sum of the kept values (`0` when nothing is kept).
- `entries` = distinct kept values with their counts, sorted by count
  **descending**, ties broken by value **ascending**, then truncated to
  `--top`. `entries` is truncated *after* sorting; `kept` and `sum` are
  computed *before* truncation.
- Empty input is not an error: `{"kept": 0, "skipped": 0, "sum": 0, "entries": []}`,
  exit 0.

## Ordering rules, stated once and precisely

The pipeline is: **tokenize → classify (value vs skipped) → `--min` filter →
count → sort → `--top` truncate**. Three consequences a naive implementation
usually gets wrong:

1. `skipped` counts only classification failures, never `--min` rejections.
2. `kept` and `sum` are pre-truncation totals; `--top 1` does not change them.
3. Ties are broken by value **ascending**, so with counts equal, `-5` precedes
   `7`. Note that with no `--min` given, negative values are ordinary kept
   values — the default is *no bound*, not `0`.

## Examples

    echo "4 4 7 x" | python3 workspace/ex-tool_from_spec/numstat.py
    -> {"kept": 3, "skipped": 1, "sum": 15, "entries": [[4, 2], [7, 1]]}

    echo "1 2 3" | python3 workspace/ex-tool_from_spec/numstat.py --min 2 --top 1
    -> {"kept": 2, "skipped": 0, "sum": 5, "entries": [[2, 1]]}

## Acceptance

The sealed suite `assets/ex-tool_from_spec/test_accept.py` is run from the
workspace root with pytest. All tests must pass. Do not modify the test file.
