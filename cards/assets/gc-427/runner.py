#!/usr/bin/env python3
"""Canonical verification runner for gc-427 (sealed).

Usage: python3 assets/gc-427/runner.py <repo_dir>
Runs the unittest suite found in <repo_dir> and prints EXACTLY ONE canonical
JSON line: {"failing": [...sorted dotted ids...], "green": bool, "ran": N}
(sort_keys, compact separators). The line is deterministic for a given repo
state, so its SHA-256 acts as a verifiable receipt that this verification
really ran on that state. Journal entries must carry sha256 of this exact
line (UTF-8, no trailing newline).
"""
import json
import subprocess
import sys

RUNNER = r"""
import json, sys, unittest
loader = unittest.TestLoader()
suite = loader.discover(sys.argv[1], pattern="test_*.py", top_level_dir=sys.argv[1])
result = unittest.TestResult()
suite.run(result)
failing = sorted({t.id() for t, _ in result.failures} | {t.id() for t, _ in result.errors})
print(json.dumps({"ran": result.testsRun, "failing": failing}))
"""


def main():
    if len(sys.argv) != 2:
        print(json.dumps({"failing": ["__USAGE__"], "green": False, "ran": 0},
                         sort_keys=True, separators=(",", ":")))
        return
    proc = subprocess.run([sys.executable, "-c", RUNNER, sys.argv[1]],
                          capture_output=True, text=True, timeout=120)
    res = {"ran": 0, "failing": ["__RUNNER_CRASHED__"]}
    for line in reversed(proc.stdout.strip().splitlines() or [""]):
        if line.startswith("{"):
            try:
                res = json.loads(line)
                break
            except json.JSONDecodeError:
                break
    out = {"failing": res["failing"], "green": res["failing"] == [] and res["ran"] > 0,
           "ran": res["ran"]}
    print(json.dumps(out, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
