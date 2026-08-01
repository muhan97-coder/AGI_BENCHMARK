#!/usr/bin/env python3
"""Sealed checker for gc-431 task-05.

Standalone self-check: python3 check.py <out_dir>
Grading uses observe (untrusted subprocess) + verdict (trusted, pure).
"""
import json
from pathlib import Path

NEEDS_OBSERVE = False
ASSET_DIR = Path(__file__).resolve().parent


def observe(out_dir):
    return None


def verdict(out_dir, obs=None):
    import hashlib
    want = hashlib.sha256((ASSET_DIR / "input.txt").read_bytes()).hexdigest()
    p = Path(out_dir) / "out.txt"
    if not p.is_file():
        return {"pass": False, "why": "out.txt missing"}
    if p.read_text().strip().lower() != want:
        return {"pass": False, "why": "digest mismatch"}
    return {"pass": True, "why": "digest correct"}

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
