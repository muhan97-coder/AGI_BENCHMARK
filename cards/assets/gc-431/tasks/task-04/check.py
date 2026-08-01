#!/usr/bin/env python3
"""Sealed checker for gc-431 task-04.

Standalone self-check: python3 check.py <out_dir>
Grading uses observe (untrusted subprocess) + verdict (trusted, pure).
"""
import json
from pathlib import Path

NEEDS_OBSERVE = True
PROBES = ["", "()", "([])", "([)]", "(((", ")(", "{[()()]}", "([]{})",
          "]", "()[]{}", "({[", "()()", "a(b)c[d]", "([x)]"]

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
        return {"out": [bool(mod.balanced(s)) for s in PROBES]}
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {exc}"}


def _ref(s):
    pairs = {")": "(", "]": "[", "}": "{"}
    stack = []
    for ch in s:
        if ch in "([{":
            stack.append(ch)
        elif ch in pairs:
            if not stack or stack.pop() != pairs[ch]:
                return False
    return not stack


def verdict(out_dir, obs):
    if not isinstance(obs, dict) or "error" in obs:
        return {"pass": False, "why": f"observe failed: {obs}"}
    want = [_ref(s) for s in PROBES]
    if obs.get("out") != want:
        return {"pass": False, "why": "balanced() wrong on probe set"}
    return {"pass": True, "why": "bracket matching correct on probes"}

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
