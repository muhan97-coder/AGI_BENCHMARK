# diffstat — unified diff statistics library + CLI (spec v1)

Implement a pure-Python module at `workspace/gc-402/diffstat.py` (relative to
the benchmark repo root). Standard library only.

## Library API: `parse(diff_text: str) -> dict`
Returns:

    {"files": [ {"path": str, "added": int, "removed": int,
                 "binary": bool, "renamed_from": str | None}, ... ],
     "total_added": int, "total_removed": int}

Files appear in order of first appearance. Empty input returns zero files and
zero totals. `parse` never raises on well-formed-enough input; unknown lines
outside hunks are ignored.

## Parsing rules
Process lines top to bottom. Two kinds of file blocks exist:

### Git blocks
- `diff --git a/X b/Y` starts a new file entry. Initial path = `Y` (the text
  after the LAST ` b/` separator on the line). Fields start at
  added=0, removed=0, binary=false, renamed_from=None.
- Inside a git block, before any hunk:
  - `rename from P` sets `renamed_from = P`
  - `rename to Q` sets `path = Q`
  - `Binary files ... differ` sets `binary = true`
  - a `--- ` / `+++ ` pair updates the path (rules below)

### Plain blocks (classic unified diff, no git header)
- A `--- ` line that is NOT inside a git block and NOT inside a hunk starts a
  new entry, which must be followed by a `+++ ` line.
- A git block extends to the next `diff --git` line or end of input. Inputs
  mixing git blocks and plain blocks in one diff are out of scope and are not
  tested.

### `---` / `+++` path resolution (both block kinds)
- The raw path is the text after `--- ` / `+++ `, cut at the first TAB
  character if any (classic diffs put a timestamp after a tab).
- Strip a leading `a/` or `b/` prefix if present.
- If the `+++` side is `/dev/null` (deleted file), the entry path is the
  `---` side; otherwise the entry path is the `+++` side.

### Hunks and counting (the part naive parsers get wrong)
- A hunk starts with `@@ -a[,b] +c[,d] @@ ...`; `b` and `d` default to 1 when
  omitted. The hunk body consists of exactly the following, in any
  interleaving: lines counted against the OLD side (starting with `-` or a
  context line) totaling `b`, and lines counted against the NEW side
  (starting with `+` or a context line) totaling `d`.
- Within a hunk body: a line starting with `+` increments `added`; a line
  starting with `-` increments `removed`; a line starting with a space (or an
  empty line) is context and counts toward both side totals; a line starting
  with `\` (e.g. `\ No newline at end of file`) counts toward NEITHER side
  total and is not a change.
- The hunk ends exactly when both side totals are consumed. You MUST use the
  `@@` counts to delimit hunks: a hunk body line such as `--- text` (a
  removed line whose content begins with dashes) or `+++ text` MUST be
  counted as a change, not treated as a file header.
- `total_added` / `total_removed` are sums over all files.

## CLI
    python3 workspace/gc-402/diffstat.py
Reads a diff from stdin, prints `parse`'s result as one compact JSON line,
exits 0.

## Acceptance
Sealed suite: `assets/gc-402/test_accept.py`, run from the repo root with
pytest. Do not modify the test file.
