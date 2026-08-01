#!/usr/bin/env python3
"""Sealed checker for gc-431 task-03.

Standalone self-check: python3 check.py <out_dir>
Grading uses observe (untrusted subprocess) + verdict (trusted, pure).
"""
import json
from pathlib import Path

NEEDS_OBSERVE = True
PROBES = [1, 3, 4, 9, 14, 40, 49, 88, 90, 400, 944, 1000, 1494, 1666,
          2026, 3549, 3888, 3999]

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
        return {"out": [mod.roman(n) for n in PROBES]}
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {exc}"}


_VALS = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"),
         (90, "XC"), (50, "L"), (40, "XL"), (10, "X"), (9, "IX"),
         (5, "V"), (4, "IV"), (1, "I")]


def _ref(n):
    out = []
    for v, sym in _VALS:
        while n >= v:
            out.append(sym)
            n -= v
    return "".join(out)


def verdict(out_dir, obs):
    if not isinstance(obs, dict) or "error" in obs:
        return {"pass": False, "why": f"observe failed: {obs}"}
    want = [_ref(n) for n in PROBES]
    if obs.get("out") != want:
        return {"pass": False, "why": "roman() wrong on probe set"}
    return {"pass": True, "why": "roman numerals correct on probes"}

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
