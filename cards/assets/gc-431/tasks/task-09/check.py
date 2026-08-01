#!/usr/bin/env python3
"""Sealed checker for gc-431 task-09.

Standalone self-check: python3 check.py <out_dir>
Grading uses observe (untrusted subprocess) + verdict (trusted, pure).
"""
import json
from pathlib import Path

NEEDS_OBSERVE = False


def observe(out_dir):
    return None


def verdict(out_dir, obs=None):
    import re
    p = Path(out_dir) / "out.txt"
    if not p.is_file():
        return {"pass": False, "why": "out.txt missing"}
    m = re.fullmatch(r"(\d+)\s+(\d+)\s+(\d+)", p.read_text().strip())
    if not m:
        return {"pass": False, "why": "expected three integers 'a b c'"}
    a, b, c = (int(m.group(i)) for i in (1, 2, 3))
    if not (0 < a < b < c):
        return {"pass": False, "why": "need 0 < a < b < c"}
    if a * a + b * b != c * c:
        return {"pass": False, "why": "not a Pythagorean triple"}
    if a + b + c != 1000:
        return {"pass": False, "why": "sum is not 1000"}
    return {"pass": True, "why": "valid triple summing to 1000"}

if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3 and sys.argv[1] == "observe":
        print(json.dumps(observe(sys.argv[2])))
        sys.exit(0)
    if len(sys.argv) != 2:
        print(json.dumps({"pass": False, "why": "usage: check.py <out_dir>"}))
        sys.exit(2)
    _obs = observe(sys.argv[1]) if NEEDS_OBSERVE else None
    try:
        _v = verdict(sys.argv[1], _obs)
    except Exception as exc:
        _v = {"pass": False, "why": f"verdict error: {type(exc).__name__}"}
    print(json.dumps(_v))
    sys.exit(0 if _v.get("pass") else 1)
