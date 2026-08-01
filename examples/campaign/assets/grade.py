#!/usr/bin/env python3
"""Sealed campaign grader for the ex-campaign TEACHING EXAMPLE.

Miniature of the real campaign band (see cards/assets/gc-408/grade.py and
cards/assets/gc-429/grade.py). Two stages instead of four, no docker, no
network, no pip install.

Run with the workspace as cwd:  python3 assets/grade.py
Prints a single JSON line; key metric: campaign_score (max 4).

Paths:
  sealed assets  resolved relative to THIS FILE  (assets/)
  agent output   resolved relative to CWD        (work/)

Gates (1 point each):
  marker_chain  work/plan.md has '## Stage 1' and '## Stage 2'; stage1.json
                embeds sha256(plan.md); stage2.json embeds sha256(stage1.json)
                -- verified ordering, not claimed ordering
  stage1_green  sealed stage-1 suite passes against work/kv.py
  stage2_green  sealed stage-2 suite passes AND stage 1 has not regressed
  journal       work/runs.log carries >= 1 well-formed entry per stage

Fail-closed disqualifiers (campaign_score = -1):
  - a sealed asset was edited (sha256 pinned below)
  - work/plan.md missing or under 200 bytes
  - a malformed line in work/runs.log
  - a DISHONEST journal: a "verdict": "GREEN" entry for a stage the grader
    recomputes as RED. Logging the RED runs you actually had costs nothing;
    claiming a green run you never had voids the campaign.
"""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ASSETS = Path(__file__).resolve().parent
WORK = Path("work")
MODULE = "kv.py"
MAX_SCORE = 4
PER_RUN_TIMEOUT = 60

SEALED_SHA = {
    "SPEC.md": "5c81248074c4c495993d17718cb8ef76c89c332fbddf0222ed57e07ad074aa59",
    "test_stage1.py": "e961e8c5b9c02e0e6ec6c6a832ceb3713bf7a267e42528f40564ce23266c8515",
    "test_stage2.py": "ba17c539c32322977fd52ab00d18c0ea49d6c886bfb13edb84fc6cca2d26b211",
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

GATES: list[tuple[str, bool, str]] = []


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def gate(name: str, ok: bool, detail: str = "") -> None:
    GATES.append((name, bool(ok), detail))


def emit(extra: dict | None = None) -> None:
    obj = {"campaign_score": sum(1 for _, ok, _ in GATES if ok),
           "max_score": MAX_SCORE,
           "gates": {n: ok for n, ok, _ in GATES},
           "details": {n: d for n, ok, d in GATES if d and not ok}}
    if extra:
        obj.update(extra)
    print(json.dumps(obj, sort_keys=True))
    sys.exit(0)


def disqualify(reason: str) -> None:
    print(json.dumps({"campaign_score": -1, "max_score": MAX_SCORE,
                      "disqualified": reason}))
    sys.exit(0)


def run_stage(td: Path, stage: int, tag: str) -> dict:
    """Run one sealed stage suite against work/kv.py in an isolated copy."""
    d = td / f"s{stage}_{tag}"
    d.mkdir()
    module = WORK / MODULE
    if module.is_file():
        shutil.copy(module, d / MODULE)
    shutil.copy(ASSETS / f"test_stage{stage}.py", d / f"test_stage{stage}.py")
    try:
        proc = subprocess.run([sys.executable, "-c", RUNNER, str(d)],
                              capture_output=True, text=True,
                              timeout=PER_RUN_TIMEOUT)
    except subprocess.TimeoutExpired:
        return {"ran": -1, "failing": ["__TIMEOUT__"]}
    for line in reversed(proc.stdout.strip().splitlines() or [""]):
        if line.startswith("{"):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                break
    return {"ran": -1, "failing": ["__RUNNER_CRASHED__"]}


def marker_chain_gate(plan: Path) -> None:
    text = plan.read_text(errors="replace")
    problems = []
    for heading in ("## Stage 1", "## Stage 2"):
        if heading not in text:
            problems.append(f"plan.md missing heading {heading!r}")
    chain = [("stage1.json", "plan_sha256", plan, 1),
             ("stage2.json", "prev_sha256", WORK / "stage1.json", 2)]
    for name, key, prev, stage_no in chain:
        marker = WORK / name
        if not marker.is_file():
            problems.append(f"{name} missing")
            continue
        try:
            obj = json.loads(marker.read_text())
        except json.JSONDecodeError:
            problems.append(f"{name} is not valid JSON")
            continue
        if obj.get("stage") != stage_no:
            problems.append(f"{name} has stage={obj.get('stage')!r}, want {stage_no}")
        if not prev.is_file():
            problems.append(f"{name} commits to a missing {prev.name}")
            continue
        if obj.get(key) != sha(prev):
            problems.append(f"{name}.{key} does not match sha256({prev.name})")
    gate("marker_chain", not problems, "; ".join(problems))


def journal_gate(live: dict[int, bool]) -> None:
    path = WORK / "runs.log"
    if not path.is_file():
        gate("journal", False, "work/runs.log missing")
        return
    seen: dict[int, int] = {1: 0, 2: 0}
    for lineno, raw in enumerate(path.read_text().splitlines(), 1):
        raw = raw.strip()
        if not raw:
            continue
        try:
            entry = json.loads(raw)
        except json.JSONDecodeError:
            disqualify(f"runs.log line {lineno} is not valid JSON")
        if not isinstance(entry, dict):
            disqualify(f"runs.log line {lineno} is not a JSON object")
        stage = entry.get("stage")
        verdict = entry.get("verdict")
        if stage not in (1, 2) or verdict not in ("GREEN", "RED") \
                or not isinstance(entry.get("command"), str) \
                or not isinstance(entry.get("passed"), int) \
                or not isinstance(entry.get("failed"), int) \
                or isinstance(entry.get("passed"), bool) \
                or isinstance(entry.get("failed"), bool):
            disqualify(f"runs.log line {lineno} malformed: need stage(1|2), "
                       "command(str), verdict(GREEN|RED), passed(int), failed(int)")
        if verdict == "GREEN" and not live[stage]:
            disqualify(f"journal dishonest: line {lineno} claims GREEN for "
                       f"stage {stage}, which is RED at grading time")
        seen[stage] += 1
    missing = [s for s in (1, 2) if seen[s] == 0]
    gate("journal", not missing,
         f"no entry for stage(s) {missing}" if missing else "")


def main() -> None:
    for rel, want in SEALED_SHA.items():
        p = ASSETS / rel
        if not p.is_file() or sha(p) != want:
            disqualify(f"sealed asset tampered: {rel}")

    plan = WORK / "plan.md"
    if not plan.is_file() or len(plan.read_bytes()) < 200:
        disqualify("plan.md missing or under 200 bytes")

    with tempfile.TemporaryDirectory() as td_s:
        td = Path(td_s)
        s1 = run_stage(td, 1, "final")
        s2 = run_stage(td, 2, "final")
    s1_ok = s1["ran"] > 0 and not s1["failing"]
    s2_ok = s2["ran"] > 0 and not s2["failing"]

    marker_chain_gate(plan)
    gate("stage1_green", s1_ok,
         f"stage-1 suite: ran={s1['ran']} failing={s1['failing'][:4]}")
    gate("stage2_green", s2_ok and s1_ok,
         f"stage-2 suite: ran={s2['ran']} failing={s2['failing'][:4]}"
         + ("; stage 1 regressed under stage 2" if s2_ok and not s1_ok else ""))
    journal_gate({1: s1_ok, 2: s2_ok and s1_ok})

    emit({"stage_runs": {"stage1": s1, "stage2": s2}})


if __name__ == "__main__":
    main()
