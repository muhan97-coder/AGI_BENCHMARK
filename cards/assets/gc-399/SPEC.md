# jsonpick — mini JSON path query library + CLI (spec v1)

Implement a pure-Python module at `workspace/gc-399/jsonpick.py` (relative to
the benchmark repo root). Only the standard library is allowed.

## Library API: `pick(doc, path) -> list`
`doc` is any JSON-compatible Python value. `path` is a query string.
Returns the list of ALL matched values, in traversal order. Never raises for
"not found" — missing paths simply contribute no matches. Raises `ValueError`
only for syntactically invalid paths.

### Path grammar
- A path MUST start with `$` (the root). `$` alone matches the whole document
  (one match).
- After `$`, zero or more segments follow, each one of:
  - `.NAME` — dict key access. NAME matches `[A-Za-z_][A-Za-z0-9_]*`.
    Anything else after `.` is a syntax error.
  - `["KEY"]` — quoted dict key (double quotes only). The only escapes are
    `\"` and `\\`; any other backslash use is a syntax error. Allows keys with
    dots, spaces, brackets, etc.
  - `[INT]` — list index, base-10 integer, may be negative (Python
    semantics). Out-of-range indexes contribute no matches.
  - `[*]` — wildcard. On a list: every element in order. On a dict: every
    value, in **sorted key order**. On anything else: no matches.
  - `[START:STOP]` — list slice, Python semantics, no step. Either side may
    be empty; either side may be negative. On non-lists: no matches.
- Whitespace is NOT allowed anywhere in the path (syntax error).
- Type mismatches are silent: `.name` or `["k"]` applied to a non-dict, and
  `[0]` or a slice applied to a non-list, contribute **no matches** (never an
  error). A dict never matches `[0]` even if it has the key `"0"`.

### Examples
    pick({"a": {"b": [10, 20]}}, "$.a.b[1]")        -> [20]
    pick({"a": 1, "b": 2}, "$[*]")                  -> [1, 2]
    pick([[1, 2], [3]], "$[*][0]")                  -> [1, 3]
    pick({"x.y": 5}, '$["x.y"]')                    -> [5]
    pick({"a": 1}, "$.missing")                     -> []

## CLI
    python3 workspace/gc-399/jsonpick.py PATH
- Reads one JSON document from stdin.
- On success prints exactly one compact JSON line
  `{"count": N, "matches": [...]}` and exits 0.
- Syntactically invalid path: prints `{"error": "path"}`, exits 2.
- Invalid JSON on stdin: prints `{"error": "json"}`, exits 3.
- Wrong number of CLI arguments: prints `{"error": "usage"}`, exits 4.

## Acceptance
Sealed suite: `assets/gc-399/test_accept.py`, run from the repo root with
pytest. Do not modify the test file.
