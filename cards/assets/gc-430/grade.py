#!/usr/bin/env python3
"""Sealed ratchet-mutation grader for gc-430.

Run from the benchmark repo root:  python3 assets/gc-430/grade.py
Prints a single JSON line; key metric: kill_rate (round-4 kills / 36).

The campaign must leave four round snapshots:
  work/gc-430/rounds/r1/tests/  ... r4/tests/     (unittest files test_*.py)
  work/gc-430/rounds/rN/round_report.json         {"killed": [mutant ids]}

Ratchet rules, all recomputed live (violations = kill_rate -1, fail-closed):
  - every round's suite is green on the pristine module; r1 collects >= 8
    tests and counts never shrink between rounds
  - test files are append-only: every test file of round N-1 must be present
    BYTE-IDENTICAL in round N (strengthening adds tests, never rewrites
    history)
  - recomputed kill sets must grow strictly: K1 < K2 < K3 < K4 as sets
    (superset + strictly larger) -- a copied suite cannot fake four rounds
  - each round_report.json must equal the recomputed kill set EXACTLY;
    over- or under-claiming one mutant id in any round disqualifies the run
  - sealed target/datex.py and mutants.jsonl are hash-checked
"""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CARD = "gc-430"
ASSETS = Path("assets") / CARD
WORK = Path("work") / CARD
MODULE = "datex.py"
ROUNDS = ["r1", "r2", "r3", "r4"]
MIN_TESTS_R1 = 8
PER_RUN_TIMEOUT = 120

SEALED_SHA = {
    "target/datex.py": "c83a542b59307a8a14750a153c575b1fdc453017f66dd3e16f9d1cd16ae37aa4",
    "mutants.jsonl": "cd7ba70fa040f0a767d04b671e15a3a097d0afd59f3884d9b17effcb68586407"
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


def disqualify(reason):
    out({"kill_rate": -1, "error": reason})


def run_suite(d: Path) -> dict:
    try:
        proc = subprocess.run([sys.executable, "-c", RUNNER, str(d)],
                              capture_output=True, text=True, timeout=PER_RUN_TIMEOUT)
    except subprocess.TimeoutExpired:
        return {"ran": -1, "failing": ["__TIMEOUT__"]}
    for line in reversed(proc.stdout.strip().splitlines() or [""]):
        if line.startswith("{"):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                break
    return {"ran": -1, "failing": ["__RUNNER_CRASHED__"]}


def main():
    for rel, want in SEALED_SHA.items():
        p = ASSETS / rel
        if not p.is_file() or sha(p) != want:
            disqualify(f"sealed asset tampered: {rel}")
    plan = WORK / "plan.md"
    if not plan.is_file() or len(plan.read_bytes()) < 250:
        disqualify("plan.md missing or under 250 bytes")

    module_src = (ASSETS / "target" / MODULE).read_text()
    mutants = [json.loads(line) for line in
               (ASSETS / "mutants.jsonl").read_text().splitlines() if line.strip()]

    round_files = {}
    for r in ROUNDS:
        tdir = WORK / "rounds" / r / "tests"
        files = sorted(tdir.glob("test_*.py")) if tdir.is_dir() else []
        if not files:
            disqualify(f"round {r}: no tests under rounds/{r}/tests/")
        round_files[r] = files

    # append-only file ratchet
    for prev, cur in zip(ROUNDS, ROUNDS[1:]):
        cur_by_name = {f.name: f for f in round_files[cur]}
        for f in round_files[prev]:
            g = cur_by_name.get(f.name)
            if g is None or sha(g) != sha(f):
                disqualify(f"ratchet broken: {f.name} of {prev} missing or "
                           f"modified in {cur}")

    kill_sets = {}
    ran_counts = {}
    with tempfile.TemporaryDirectory() as td_s:
        td = Path(td_s)

        def build(r, mutant=None):
            d = td / f"{r}_{mutant['id'] if mutant else 'baseline'}"
            d.mkdir()
            src = module_src
            if mutant is not None:
                if src.count(mutant["old"]) != 1:
                    disqualify(f"mutant {mutant['id']}: sealed old snippet not unique")
                src = src.replace(mutant["old"], mutant["new"])
            (d / MODULE).write_text(src)
            for tf in round_files[r]:
                shutil.copy(tf, d / tf.name)
            return d

        for r in ROUNDS:
            base = run_suite(build(r))
            if base["failing"] or base["ran"] <= 0:
                disqualify(f"round {r}: suite not green on pristine module: {base}")
            ran_counts[r] = base["ran"]
            kill_sets[r] = {m["id"] for m in mutants if run_suite(build(r, m))["failing"]}

    if ran_counts["r1"] < MIN_TESTS_R1:
        disqualify(f"round r1 collects only {ran_counts['r1']} tests (< {MIN_TESTS_R1})")
    for prev, cur in zip(ROUNDS, ROUNDS[1:]):
        if ran_counts[cur] < ran_counts[prev]:
            disqualify(f"test count shrank from {prev} to {cur}")
        if not (kill_sets[prev] <= kill_sets[cur] and
                len(kill_sets[prev]) < len(kill_sets[cur])):
            disqualify(f"kill ratchet broken: {cur} does not strictly extend {prev} "
                       f"({len(kill_sets[prev])} -> {len(kill_sets[cur])})")

    for r in ROUNDS:
        rp = WORK / "rounds" / r / "round_report.json"
        if not rp.is_file():
            disqualify(f"round {r}: round_report.json missing")
        try:
            claimed = set(json.loads(rp.read_text())["killed"])
        except (json.JSONDecodeError, KeyError, TypeError):
            disqualify(f"round {r}: round_report.json malformed")
        if claimed != kill_sets[r]:
            over, under = sorted(claimed - kill_sets[r]), sorted(kill_sets[r] - claimed)
            disqualify(f"round {r} report dishonest: overclaimed={over} "
                       f"underclaimed={under}")

    rate = round(len(kill_sets["r4"]) / len(mutants), 4)
    out({"kill_rate": rate, "mutants": len(mutants),
         "kills_per_round": [len(kill_sets[r]) for r in ROUNDS],
         "tests_per_round": [ran_counts[r] for r in ROUNDS]})


if __name__ == "__main__":
    main()
