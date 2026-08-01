#!/usr/bin/env python3
"""Sealed grader for gc-421 (failure identities, then repair).

Run from the benchmark repo root:  python3 assets/gc-421/grade.py
Prints a single JSON line; key metric: identity_score (max 3, -1 fail-closed).

Points:
  +1 work/gc-421/failure_identity.json lists EXACTLY the failing test ids of
     the pristine sealed repo (identities, not counts; recomputed live here)
  +1 sealed test file is byte-identical in the work repo and is the only
     test_*.py there (no test weakening, no shadow suites)
  +1 suite is green in work/gc-421/repo with the same number of tests ran
Gate: work/gc-421/plan.md >= 200 bytes, sealed assets untampered; else -1.
"""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ASSETS = Path("assets/gc-421")
WORK = Path("work/gc-421")

SEALED_SHA = {
    "repo/textstat.py": "cc01ff609e8f7da62cf4e5ff4d44daccb5c5d3dae06f2071259e892b189d19ba",
    "repo/test_textstat.py": "fef5df628b784f69cad55f8700ba837b24352a1f6c87cce86420781d9ab39f8f",
}

RUNNER = r"""
import json, sys, unittest
loader = unittest.TestLoader()
suite = loader.discover(sys.argv[1], pattern="test_*.py", top_level_dir=sys.argv[1])
result = unittest.TestResult()
suite.run(result)
failing = sorted({t.id() for t, _ in result.failures} | {t.id() for t, _ in result.errors})
print(json.dumps({"ran": result.testsRun, "failing": failing}))
"""


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def out(res):
    print(json.dumps(res))
    sys.exit(0)


def run_suite(repo_dir: Path) -> dict:
    proc = subprocess.run([sys.executable, "-c", RUNNER, str(repo_dir)],
                          capture_output=True, text=True, timeout=120)
    for line in reversed(proc.stdout.strip().splitlines() or [""]):
        if line.startswith("{"):
            return json.loads(line)
    return {"ran": 0, "failing": ["__RUNNER_CRASHED__"]}


def main():
    for rel, want in SEALED_SHA.items():
        p = ASSETS / rel
        if not p.is_file() or sha(p) != want:
            out({"identity_score": -1, "error": f"sealed asset tampered: {rel}"})

    plan = WORK / "plan.md"
    if not plan.is_file() or len(plan.read_bytes()) < 200:
        out({"identity_score": -1, "error": "plan.md missing or under 200 bytes"})

    # Recompute ground-truth failure identities on a pristine copy.
    with tempfile.TemporaryDirectory() as td:
        pristine = Path(td) / "repo"
        shutil.copytree(ASSETS / "repo", pristine)
        truth = run_suite(pristine)
    if not truth["failing"]:
        out({"identity_score": -1, "error": "sealed repo unexpectedly green"})

    score = 0
    detail = {"expected_failing": truth["failing"]}

    ident = WORK / "failure_identity.json"
    claimed = []
    if ident.is_file():
        try:
            claimed = json.loads(ident.read_text()).get("failing_tests", [])
        except (json.JSONDecodeError, AttributeError):
            claimed = []
    identity_ok = sorted(claimed) == truth["failing"]
    detail["identity_ok"] = identity_ok
    score += 1 if identity_ok else 0

    repo = WORK / "repo"
    tests_ok = False
    if repo.is_dir():
        tf = repo / "test_textstat.py"
        only_sealed = (tf.is_file() and sha(tf) == SEALED_SHA["repo/test_textstat.py"]
                       and sorted(p.name for p in repo.glob("test_*.py")) == ["test_textstat.py"])
        tests_ok = only_sealed
    detail["tests_untouched"] = tests_ok
    score += 1 if tests_ok else 0

    green_ok = False
    if repo.is_dir():
        res = run_suite(repo)
        green_ok = res["failing"] == [] and res["ran"] == truth["ran"] and res["ran"] > 0
        detail["work_suite"] = res
    score += 1 if green_ok else 0

    out({"identity_score": score, "max": 3, "detail": detail})


if __name__ == "__main__":
    main()
