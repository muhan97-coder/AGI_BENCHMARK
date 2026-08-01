#!/usr/bin/env python3
"""numstat — reference solution for ex-tool_from_spec.

This is exactly the file an agent has to produce. Stdlib only.

The pipeline order is the whole game (SPEC.md "Ordering rules"):

    tokenize -> classify (value vs skipped) -> --min filter -> count
             -> sort (count desc, value asc) -> --top truncate

with `kept`/`sum` computed BEFORE truncation and `skipped` counting only
classification failures, never --min rejections.

Argument parsing is hand-rolled rather than argparse on purpose: argparse
writes its own message to stderr and exits 2 for unknown options, but it does
NOT print the `{"error": "usage"}` JSON line the spec demands on stdout, and it
accepts abbreviations like `--mi 3`. Deferring to it fails
test_usage_errors_exit_two_with_json.
"""
import json
import re
import sys

INT_RE = re.compile(r"^-?[0-9]+$")
DEFAULT_MIN = None      # no lower bound; NOT 0 — negatives are kept by default
DEFAULT_TOP = 3


def usage_error():
    """Single JSON line on stdout, exit 2 — as pinned by the spec."""
    print(json.dumps({"error": "usage"}))
    sys.exit(2)


def parse_args(argv):
    opts = {"min": DEFAULT_MIN, "top": DEFAULT_TOP}
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--min":
            key = "min"
        elif arg == "--top":
            key = "top"
        else:
            usage_error()          # unknown option (and any bare positional)
        if i + 1 >= len(argv):
            usage_error()          # option given without a value
        raw = argv[i + 1]
        if not INT_RE.match(raw):
            usage_error()          # "1.5", "x", "+5" are all usage errors
        value = int(raw)
        if key == "top" and value < 0:
            usage_error()          # N >= 0
        opts[key] = value
        i += 2
    return opts


def main(argv):
    opts = parse_args(argv)

    values, skipped = [], 0
    for token in sys.stdin.read().split():
        if INT_RE.match(token):
            values.append(int(token))
        else:
            skipped += 1

    lo = opts["min"]
    kept = values if lo is None else [v for v in values if v >= lo]

    counts = {}
    for v in kept:
        counts[v] = counts.get(v, 0) + 1

    # count descending, ties by value ascending
    entries = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))

    result = {
        "kept": len(kept),                      # pre-truncation
        "skipped": skipped,                     # classification failures only
        "sum": sum(kept),                       # pre-truncation
        "entries": [[v, c] for v, c in entries[: opts["top"]]],
    }
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
