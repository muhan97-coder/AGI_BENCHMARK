#!/usr/bin/env python3
"""Sealed checker for gc-431 task-10.

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
    want = (ASSET_DIR / "digest.txt").read_text().strip()
    p = Path(out_dir) / "out.bin"
    if not p.is_file():
        return {"pass": False, "why": "out.bin missing"}
    data = p.read_bytes()
    if len(data) != 32:
        return {"pass": False, "why": "key must be exactly 32 bytes"}
    if hashlib.sha256(data).hexdigest() != want:
        return {"pass": False, "why": "sha256(key) does not match digest"}
    return {"pass": True, "why": "session key verified"}

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
