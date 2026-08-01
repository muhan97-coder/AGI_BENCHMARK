#!/usr/bin/env python3
"""Machine grader for goal cards (fail-closed, no LLM judgment).

Runs a card's ``success_criteria.spec`` and returns PASS/FAIL.
Spec contract:
  command        : one shell line (may itself be a ``docker run``)
  docker_image   : (optional) run ``command`` inside this image with the
                   workspace mounted at /ws (``-w /ws``)
  metric         : numeric metric name; ``"exit_code"`` uses the return code
  extract_regex  : (optional) regex whose group 1 extracts the number from
                   stdout; without it, the last JSON line of stdout must
                   contain ``metric`` as a key
  threshold, compare (>=|<=|==)

Grading is reproducible: the evidence (command, stdout tail, value, wall time)
is returned with the verdict. Fail-closed: an invalid spec, a failed
extraction, or a timeout is NEVER a pass (SPEC_INVALID / EXTRACT_FAIL /
TIMEOUT all carry ``passed: false``).

``--dry-run`` validates spec shape only, without executing anything.

Usage:
  python3 tools/goal_grader.py [--dry-run] <card.json> [workspace]
"""
from __future__ import annotations

import json
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

_COMPARES = {">=": lambda a, b: a >= b, "<=": lambda a, b: a <= b,
             "==": lambda a, b: a == b}
_TIMEOUT_S = 1800


def validate_spec(spec: dict[str, Any]) -> list[str]:
    """Return the list of spec defects (empty list = valid). Executes nothing."""
    problems: list[str] = []
    if not str(spec.get("command") or "").strip():
        problems.append("missing command")
    if not str(spec.get("metric") or "").strip():
        problems.append("missing metric")
    if spec.get("compare") not in _COMPARES:
        problems.append(f"invalid compare: {spec.get('compare')!r}")
    try:
        float(spec.get("threshold"))
    except (TypeError, ValueError):
        problems.append(f"threshold not a number: {spec.get('threshold')!r}")
    rex = spec.get("extract_regex")
    if rex:
        try:
            if re.compile(rex).groups < 1:
                problems.append("extract_regex has no capture group")
        except re.error as exc:
            problems.append(f"extract_regex does not compile: {exc}")
    return problems


def _extract_metric(spec: dict[str, Any], stdout: str, returncode: int) -> float:
    if spec.get("metric") == "exit_code":
        return float(returncode)
    rex = spec.get("extract_regex")
    if rex:
        m = re.search(rex, stdout, re.MULTILINE)
        if not m:
            raise ValueError(f"extract_regex did not match: {rex!r}")
        return float(m.group(1))
    for line in reversed(stdout.strip().splitlines()):
        line = line.strip()
        if line.startswith("{"):
            obj = json.loads(line)
            if spec["metric"] in obj:
                return float(obj[spec["metric"]])
    raise ValueError(f"metric {spec['metric']!r} not found in stdout")


def grade(card_path: str | Path, workspace: str | Path = ".",
          timeout_s: int = _TIMEOUT_S) -> dict[str, Any]:
    card = json.loads(Path(card_path).read_text())
    spec = card["success_criteria"]["spec"]
    problems = validate_spec(spec)
    if problems:
        # An ungradable spec fails without executing — "could not grade" must
        # never masquerade as a pass (fail-closed).
        return {"card_id": card.get("id"), "verdict": "SPEC_INVALID",
                "passed": False, "problems": problems}
    command = spec["command"]
    if spec.get("docker_image"):
        ws = str(Path(workspace).resolve())
        command = (f"docker run --rm -v {shlex.quote(ws)}:/ws -w /ws "
                   f"{shlex.quote(spec['docker_image'])} sh -c {shlex.quote(command)}")
    t0 = time.time()
    try:
        proc = subprocess.run(command, shell=True, cwd=str(workspace),
                              capture_output=True, text=True, timeout=timeout_s)
        stdout, returncode = proc.stdout, proc.returncode
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        stdout = (exc.stdout or b"").decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        returncode, timed_out = -9, True
    wall_s = round(time.time() - t0, 1)
    result: dict[str, Any] = {
        "card_id": card.get("id"), "grader": card["success_criteria"].get("grader"),
        "command": command, "wall_s": wall_s, "timed_out": timed_out,
        "stdout_tail": stdout[-2000:], "returncode": returncode,
    }
    if timed_out:
        result.update(verdict="TIMEOUT", passed=False)
        return result
    try:
        value = _extract_metric(spec, stdout, returncode)
    except (ValueError, json.JSONDecodeError) as exc:
        result.update(verdict="EXTRACT_FAIL", passed=False, error=str(exc))
        return result
    passed = _COMPARES[spec["compare"]](value, float(spec["threshold"]))
    result.update(verdict="PASS" if passed else "FAIL", passed=passed,
                  metric_value=value, threshold=float(spec["threshold"]),
                  compare=spec["compare"])
    return result


def main(argv: list[str]) -> int:
    args = [a for a in argv if not a.startswith("--")]
    if not args:
        print("usage: goal_grader [--dry-run] <card.json> [workspace]", file=sys.stderr)
        return 2
    card_path = args[0]
    if "--dry-run" in argv:
        spec = json.loads(Path(card_path).read_text())["success_criteria"]["spec"]
        problems = validate_spec(spec)
        print(json.dumps({"card": card_path, "spec_ok": not problems,
                          "problems": problems}, ensure_ascii=False))
        return 0 if not problems else 1
    workspace = args[1] if len(args) > 1 else "."
    result = grade(card_path, workspace)
    print(json.dumps(result, ensure_ascii=False, indent=1))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
