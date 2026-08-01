#!/usr/bin/env python3
"""Sealed checker for gc-431 task-01.

Standalone self-check: python3 check.py <out_dir>
Grading uses observe (untrusted subprocess) + verdict (trusted, pure).
"""
import json
from pathlib import Path

NEEDS_OBSERVE = True
PROBES = ["aaabcc", "a", "abc", "zzzzzzzzzzzz", "aAbB", "qqqwwweee",
          "abbcccddddeeeee", "xy", "ppPPpp", "m" * 40]

def _load_solution(out_dir):
    import importlib.util
    from pathlib import Path
    p = Path(out_dir) / "solution.py"
    spec = importlib.util.spec_from_file_location("solution", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def observe(out_dir):
    try:
        mod = _load_solution(out_dir)
        return {"enc": [mod.rle_encode(s) for s in PROBES],
                "rt": [mod.rle_decode(mod.rle_encode(s)) for s in PROBES]}
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {exc}"}


def _ref_encode(s):
    out = []
    i = 0
    while i < len(s):
        j = i
        while j < len(s) and s[j] == s[i]:
            j += 1
        out.append(f"{j - i}{s[i]}")
        i = j
    return "".join(out)


def verdict(out_dir, obs):
    if not isinstance(obs, dict) or "error" in obs:
        return {"pass": False, "why": f"observe failed: {obs}"}
    want = [_ref_encode(s) for s in PROBES]
    if obs.get("enc") != want:
        return {"pass": False, "why": "rle_encode output wrong on probe set"}
    if obs.get("rt") != PROBES:
        return {"pass": False, "why": "decode(encode(s)) != s on probe set"}
    return {"pass": True, "why": "codec correct on probes and round trip"}

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
