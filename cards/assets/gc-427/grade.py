#!/usr/bin/env python3
"""Sealed grader for gc-427 (journal of verifications that provably ran).

Run from the benchmark repo root:  python3 assets/gc-427/grade.py
Prints a single JSON line; key metric: journal_verified (1 or 0; -1 tamper).

The agent's journal (work/gc-427/journal.jsonl) must prove both verification
runs really happened, via receipts of the canonical runner output:
  - an entry with repo_state "pristine": stdout_sha256 == sha256 of the
    canonical runner line for the SEALED repo, and "failing" listing those
    exact dotted test ids (identities, not counts; the sealed repo is RED)
  - a LATER entry with repo_state "repaired": stdout_sha256 == sha256 of the
    canonical runner line for work/gc-427/repo, which must be green
Since the receipt is a hash of the full canonical output, a journal cannot be
written without producing (i.e. actually running or exactly predicting) the
verification output for both states. Sealed test file must be byte-identical
in the repaired repo, with no extra test_*.py. plan.md >= 250 bytes required.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ASSETS = Path("assets/gc-427")
WORK = Path("work/gc-427")

SEALED_SHA = {
    "repo/queuecalc.py": "abd80e00f968ed60836f4ae7c513e954518fb96c533bd7665d8b0d1ec3d1d029",
    "repo/test_queuecalc.py": "a0f9dda4b3d9a6cb66afba7b9f6cfebc04577bee91eb6ce850dc37897f22aff7",
    "runner.py": "80e5573630353c61d9710afb6ca21c8c65b3ca9862360b5131ee03005f9edc77"
}


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha(p: Path) -> str:
    return sha_bytes(p.read_bytes())


def out(res):
    print(json.dumps(res))
    sys.exit(0)


def disqualify(reason):
    out({"journal_verified": -1, "error": reason})


def fail(reason, **extra):
    out({"journal_verified": 0, "error": reason, **extra})


def runner_line(repo: Path) -> str:
    proc = subprocess.run([sys.executable, str(ASSETS / "runner.py"), str(repo)],
                          capture_output=True, text=True, timeout=180)
    lines = [l for l in proc.stdout.strip().splitlines() if l.startswith("{")]
    if not lines:
        return ""
    return lines[-1].strip()


def main():
    for rel, want in SEALED_SHA.items():
        p = ASSETS / rel
        if not p.is_file() or sha(p) != want:
            disqualify(f"sealed asset tampered: {rel}")

    plan = WORK / "plan.md"
    if not plan.is_file() or len(plan.read_bytes()) < 250:
        fail("plan.md missing or under 250 bytes")

    jpath = WORK / "journal.jsonl"
    if not jpath.is_file():
        fail("journal.jsonl missing")
    entries = []
    for line in jpath.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            fail("journal.jsonl has a non-JSON line")
        if not all(k in e for k in ("step", "repo_state", "stdout_sha256", "failing")):
            fail("journal entry missing step/repo_state/stdout_sha256/failing")
        entries.append(e)
    if len(entries) < 2:
        fail("journal needs at least a pristine and a repaired entry")

    pristine_line = runner_line(ASSETS / "repo")
    pristine = json.loads(pristine_line)
    if pristine["green"] or not pristine["failing"]:
        disqualify("sealed repo unexpectedly green at grade time")
    want_pristine_sha = sha_bytes(pristine_line.encode())

    p_idx = None
    for i, e in enumerate(entries):
        if (e["repo_state"] == "pristine"
                and e["stdout_sha256"] == want_pristine_sha
                and sorted(e["failing"]) == pristine["failing"]):
            p_idx = i
            break
    if p_idx is None:
        fail("no journal entry carries a valid receipt of the pristine RED run",
             expected_failing=pristine["failing"])

    repo = WORK / "repo"
    if not repo.is_dir():
        fail("work/gc-427/repo missing")
    tf = repo / "test_queuecalc.py"
    if not tf.is_file() or sha(tf) != SEALED_SHA["repo/test_queuecalc.py"]:
        fail("sealed test file modified or missing in repaired repo")
    if sorted(p.name for p in repo.glob("test_*.py")) != ["test_queuecalc.py"]:
        fail("extra test_*.py files in repaired repo")

    repaired_line = runner_line(repo)
    if not repaired_line:
        fail("runner produced no output on repaired repo")
    repaired = json.loads(repaired_line)
    if not repaired["green"] or repaired["ran"] != pristine["ran"]:
        fail("repaired repo not green with full test count", result=repaired)
    want_repaired_sha = sha_bytes(repaired_line.encode())

    r_idx = None
    for i, e in enumerate(entries):
        if (e["repo_state"] == "repaired" and e["stdout_sha256"] == want_repaired_sha
                and e["failing"] == []):
            r_idx = i
            break
    if r_idx is None:
        fail("no journal entry carries a valid receipt of the repaired GREEN run")
    if r_idx <= p_idx:
        fail("repaired receipt precedes pristine receipt in the journal")

    out({"journal_verified": 1, "pristine_failing": pristine["failing"],
         "ran": repaired["ran"]})


if __name__ == "__main__":
    main()
