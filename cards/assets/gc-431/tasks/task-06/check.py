#!/usr/bin/env python3
"""Sealed checker for gc-431 task-06.

Standalone self-check: python3 check.py <out_dir>
Grading uses observe (untrusted subprocess) + verdict (trusted, pure).
"""
import json
from pathlib import Path

NEEDS_OBSERVE = True
PROBES = [[1], [1, 2], [3, 1, 2], [4, 1, 3, 2], [1.5, 2.5], [7, 7, 7, 7],
          [-3, -1, -2], [10, 2, 8, 4, 6], [1, 2, 3, 4, 5, 6], [9, -9]]

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
        outs = []
        mutated = False
        for p in PROBES:
            arg = list(p)
            outs.append(mod.median(arg))
            if arg != p:
                mutated = True
        return {"out": outs, "mutated": mutated}
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {exc}"}


def _ref(nums):
    s = sorted(nums)
    n = len(s)
    if n % 2:
        return float(s[n // 2])
    return (s[n // 2 - 1] + s[n // 2]) / 2


def verdict(out_dir, obs):
    if not isinstance(obs, dict) or "error" in obs:
        return {"pass": False, "why": f"observe failed: {obs}"}
    if obs.get("mutated"):
        return {"pass": False, "why": "median() mutated its input list"}
    got = obs.get("out")
    want = [_ref(p) for p in PROBES]
    if (not isinstance(got, list) or len(got) != len(want)
            or any(not isinstance(g, (int, float)) or abs(g - w) > 1e-9
                   for g, w in zip(got, want))):
        return {"pass": False, "why": "median() wrong on probe set"}
    return {"pass": True, "why": "median correct on probes"}

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
