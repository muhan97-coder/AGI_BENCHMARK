#!/usr/bin/env python3
"""Sealed campaign grader (AGI_BENCHMARK, campaign band).

Reads config.json sitting next to this file and scores a multi-stage
campaign: final state (sealed acceptance suites, mutation kill gates,
golden outputs, generated probes) AND the existence/ordering of the
intermediate artifacts the campaign demands (plan file, hash-chained
stage markers, run journal, failure ledger).

Contract:
  - Run from the benchmark repo root (or /ws inside the pinned docker
    image). Prints exactly ONE JSON object as the LAST line of stdout;
    the key "campaign_score" is always present.
  - campaign_score = number of gates passed (0..max_score). The card
    threshold requires every gate green.
  - Fail-closed: any setup, integrity or internal failure emits
    campaign_score -1 (never a false PASS, never a crash without the
    metric line).

Ordering is enforced logically, not by mtimes: each stage marker must
embed the sha256 of the previous artifact (plan.md for stage 1, the
previous marker file for later stages), so markers cannot be produced
out of order and the plan cannot be rewritten after stage 1 is sealed.

Anti-gaming guards:
  - Sealed asset files are integrity-checked against sha256 values
    pinned in config.json; config.json itself is pinned in this file.
  - Agent-authored kill-test dirs are scanned for source-introspection
    tokens and may not shadow the mutation target module.
  - Probe gates regenerate fresh inputs at grading time from a sealed
    seed and compare against a reference computation embedded here, so
    hard-coding shipped golden outputs cannot pass alone.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.getcwd()
CONFIG_SHA256 = "0d190e2ec60ea21a362b17d704ae43d2eb53a2ca8684e512e7cd27d4c8eb46a1"

GATES: list[tuple[str, bool, str]] = []


def emit(score: int, max_score: int, extra: dict | None = None) -> None:
    obj = {"campaign_score": score, "max_score": max_score,
           "gates": {n: ok for n, ok, _ in GATES},
           "details": {n: d for n, ok, d in GATES if d and not ok}}
    if extra:
        obj.update(extra)
    print(json.dumps(obj, sort_keys=True))
    sys.exit(0)


def hard_fail(reason: str) -> None:
    print(json.dumps({"campaign_score": -1, "disqualified": reason}))
    sys.exit(0)


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_config() -> dict:
    path = os.path.join(HERE, "config.json")
    if not os.path.isfile(path):
        hard_fail("config.json missing next to grader")
    if sha256_file(path) != CONFIG_SHA256:
        hard_fail("config.json integrity check failed (sealed asset edited)")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def ensure_pytest(version: str) -> None:
    try:
        import pytest  # noqa: F401
        return
    except ImportError:
        pass
    r = subprocess.run([sys.executable, "-m", "pip", "install", "-q",
                        f"pytest=={version}"], capture_output=True, text=True,
                       timeout=600)
    if r.returncode != 0:
        hard_fail(f"could not install pinned pytest=={version}")


def runner_env(extra_path: str | None = None) -> dict:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    if extra_path:
        env["PYTHONPATH"] = extra_path
    else:
        env.pop("PYTHONPATH", None)
    return env


def run_pytest(target: str, cwd: str, timeout: int,
               extra_path: str | None = None) -> tuple[int, int, int, float]:
    """Return (returncode, passed, failed, wall_s); (-1,-1,-1) on timeout."""
    t0 = time.time()
    try:
        r = subprocess.run(
            [sys.executable, "-m", "pytest", target, "-q", "--tb=no",
             "-p", "no:cacheprovider"],
            cwd=cwd, env=runner_env(extra_path), capture_output=True,
            text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return -1, -1, -1, time.time() - t0
    out = r.stdout + r.stderr
    mp = re.search(r"(\d+) passed", out)
    mf = re.search(r"(\d+) failed", out)
    passed = int(mp.group(1)) if mp else 0
    failed = int(mf.group(1)) if mf else 0
    return r.returncode, passed, failed, time.time() - t0


SUITE_WALL: list[float] = []


# ---------------- gate implementations ----------------

def gate_plan(g: dict) -> tuple[bool, str]:
    path = os.path.join(REPO, g["path"])
    if not os.path.isfile(path):
        return False, f"{g['path']} missing"
    data = open(path, "r", encoding="utf-8", errors="replace").read()
    if len(data.encode()) < g.get("min_bytes", 300):
        return False, "plan too short"
    missing = [h for h in g.get("headings", []) if h not in data]
    if missing:
        return False, f"plan missing headings: {missing}"
    return True, ""


def gate_chain(g: dict) -> tuple[bool, str]:
    marker = os.path.join(REPO, g["marker"])
    prev = os.path.join(REPO, g["prev"])
    if not os.path.isfile(marker):
        return False, f"{g['marker']} missing"
    if not os.path.isfile(prev):
        return False, f"chain predecessor {g['prev']} missing"
    try:
        obj = json.load(open(marker, "r", encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return False, f"{g['marker']} is not valid JSON"
    if obj.get("stage") != g["stage"]:
        return False, f"{g['marker']} stage field != {g['stage']}"
    want = sha256_file(prev)
    if obj.get(g["prev_key"]) != want:
        return False, (f"{g['marker']}[{g['prev_key']}] does not match "
                       f"sha256 of {g['prev']} (out-of-order or edited)")
    return True, ""


def gate_suite(g: dict) -> tuple[bool, str]:
    rc, passed, failed, wall = run_pytest(
        g["path"], REPO, g.get("timeout", 300), extra_path=g.get("pythonpath"))
    SUITE_WALL.append(wall)
    repeats = 2 if g.get("double_run") else 1
    for _ in range(repeats - 1):
        rc2, p2, f2, w2 = run_pytest(
            g["path"], REPO, g.get("timeout", 300),
            extra_path=g.get("pythonpath"))
        SUITE_WALL.append(w2)
        if (rc2, p2, f2) != (rc, passed, failed):
            return False, "suite result differs between identical runs"
    if rc == -1:
        return False, "suite timed out"
    if rc != 0 or failed != 0:
        return False, f"suite red (rc={rc}, passed={passed}, failed={failed})"
    if passed != g["expected_pass"]:
        return False, f"expected exactly {g['expected_pass']} passing, got {passed}"
    return True, ""


BANNED_TOKENS = ["__file__", "__loader__", "__spec__", "getsource",
                 "get_source", "getsourcefile", "co_filename", "linecache",
                 "find_spec", "importlib.util.find", "read_text", "read_bytes",
                 "hashlib"]


def _scan_banned(dirpath: str) -> str | None:
    for root, _dirs, files in os.walk(dirpath):
        for fn in files:
            if not fn.endswith(".py"):
                continue
            text = open(os.path.join(root, fn), "r", encoding="utf-8",
                        errors="replace").read()
            for tok in BANNED_TOKENS:
                if tok in text:
                    return f"{fn} contains banned token {tok!r}"
    return None


def gate_mutation(g: dict) -> tuple[bool, str]:
    tests_dir = os.path.join(REPO, g["tests_dir"])
    ref = os.path.join(REPO, g["reference"])
    mutants_dir = os.path.join(REPO, g["mutants_dir"])
    target = g["target_module"] + ".py"
    if not os.path.isdir(tests_dir):
        return False, f"{g['tests_dir']} missing"
    test_files = [f for f in sorted(os.listdir(tests_dir))
                  if f.startswith("test_") and f.endswith(".py")]
    if not test_files:
        return False, "no test_*.py files in kill-test dir"
    for root, _d, files in os.walk(tests_dir):
        if target in files:
            return False, f"kill-test dir shadows target module {target}"
    bad = _scan_banned(tests_dir)
    if bad:
        return False, f"banned token: {bad}"
    mutants = sorted(f for f in os.listdir(mutants_dir) if f.endswith(".py"))
    if len(mutants) != g["mutant_total"]:
        return False, "sealed mutant total drift"

    def run_against(module_src: str) -> tuple[int, int, int]:
        with tempfile.TemporaryDirectory() as tmp:
            for tf in test_files:
                shutil.copy(os.path.join(tests_dir, tf), os.path.join(tmp, tf))
            shutil.copy(module_src, os.path.join(tmp, target))
            rc, passed, failed, _w = run_pytest(".", tmp,
                                                g.get("timeout", 120),
                                                extra_path=tmp)
            return rc, passed, failed

    rc, passed, failed = run_against(ref)
    if rc != 0 or failed != 0 or passed < g.get("baseline_min_tests", 5):
        return False, (f"baseline vs reference not green enough "
                       f"(rc={rc}, passed={passed}, failed={failed}, "
                       f"need >= {g.get('baseline_min_tests', 5)} passing)")
    killed = []
    for m in mutants:
        mrc, _p, mfailed, = run_against(os.path.join(mutants_dir, m))[0:3]
        if mrc not in (0, -1):
            killed.append(m)
        elif mrc == 0 and mfailed > 0:
            killed.append(m)
    if len(killed) < g["min_killed"]:
        surv = [m for m in mutants if m not in killed]
        return False, (f"killed {len(killed)}/{len(mutants)}, need "
                       f">= {g['min_killed']}; survivors: {surv}")
    return True, ""


def gate_ledger(g: dict) -> tuple[bool, str]:
    path = os.path.join(REPO, g["path"])
    if not os.path.isfile(path):
        return False, f"{g['path']} missing"
    seen: dict[str, dict] = {}
    for i, line in enumerate(open(path, "r", encoding="utf-8"), 1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            return False, f"ledger line {i} is not JSON"
        if not isinstance(obj, dict) or "id" not in obj:
            return False, f"ledger line {i} lacks an id"
        seen[obj["id"]] = obj
    for want in g["required_ids"]:
        obj = seen.get(want)
        if obj is None:
            return False, f"failure id {want} missing from ledger"
        if obj.get("status") != "fixed":
            return False, f"failure id {want} not marked fixed"
        for field in ("cause", "fix"):
            if len(str(obj.get(field, ""))) < g.get("min_field_len", 10):
                return False, f"failure id {want} field {field!r} too thin"
    stage_of = g.get("stage_of", {})
    for want, stage in stage_of.items():
        if seen.get(want, {}).get("stage") != stage:
            return False, f"failure id {want} must carry stage={stage}"
    return True, ""


def gate_runslog(g: dict) -> tuple[bool, str]:
    path = os.path.join(REPO, g["path"])
    if not os.path.isfile(path):
        return False, f"{g['path']} missing"
    per_stage: dict[int, int] = {}
    n = 0
    for i, line in enumerate(open(path, "r", encoding="utf-8"), 1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            return False, f"runs.log line {i} is not JSON"
        for key in ("ts", "stage", "cmd", "passed", "failed"):
            if key not in obj:
                return False, f"runs.log line {i} lacks key {key!r}"
        if not isinstance(obj["passed"], int) or not isinstance(obj["failed"], int):
            return False, f"runs.log line {i} passed/failed not integers"
        n += 1
        per_stage[obj["stage"]] = per_stage.get(obj["stage"], 0) + 1
    if n < g.get("min_lines", 2):
        return False, f"runs.log has {n} entries, need >= {g.get('min_lines', 2)}"
    for st in g.get("stages", []):
        if per_stage.get(st, 0) < g.get("min_per_stage", 1):
            return False, (f"runs.log needs >= {g.get('min_per_stage', 1)} "
                           f"entries for stage {st}")
    return True, ""


def gate_cost(g: dict) -> tuple[bool, str]:
    path = os.path.join(REPO, g["path"])
    if not os.path.isfile(path):
        return False, f"{g['path']} missing"
    try:
        obj = json.load(open(path, "r", encoding="utf-8"))
    except json.JSONDecodeError:
        return False, "cost file is not JSON"
    for field in g.get("fields", ["llm_usd", "grader_runs"]):
        if not isinstance(obj.get(field), (int, float)):
            return False, f"cost field {field!r} missing or non-numeric"
    return True, ""


def gate_import_ban(g: dict) -> tuple[bool, str]:
    path = os.path.join(REPO, g["file"])
    if not os.path.isfile(path):
        return False, f"{g['file']} missing"
    pat = re.compile(r"^\s*(?:import|from)\s+(" +
                     "|".join(re.escape(m) for m in g["modules"]) + r")\b")
    for i, line in enumerate(open(path, "r", encoding="utf-8",
                                  errors="replace"), 1):
        if pat.match(line):
            return False, f"{g['file']}:{i} imports a banned module"
    return True, ""


def gate_runtime(g: dict) -> tuple[bool, str]:
    total = sum(SUITE_WALL)
    if total > g["max_total_suite_seconds"]:
        return False, (f"suites took {total:.1f}s total, budget "
                       f"{g['max_total_suite_seconds']}s")
    return True, ""


# ---------------- ETL reference (used by gate_etl) ----------------

def _etl_metrics(csv_path: str) -> dict:
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)
    header, data = rows[0], rows[1:]
    data = [(r + [""] * len(header))[:len(header)] for r in data]
    cols: dict = {}
    for j, name in enumerate(header):
        cells = [r[j] for r in data]
        non_empty = [c for c in cells if c != ""]
        numeric = bool(non_empty)
        vals = []
        for c in non_empty:
            try:
                vals.append(float(c))
            except ValueError:
                numeric = False
                break
        info: dict = {"non_empty": len(non_empty),
                      "type": "numeric" if numeric else "text"}
        if numeric:
            info["mean"] = round(sum(vals) / len(vals), 6)
            info["min"] = round(min(vals), 6)
            info["max"] = round(max(vals), 6)
        else:
            info["distinct"] = len(set(non_empty))
        cols[name] = info
    return {"row_count": len(data), "columns": cols}


def _etl_serialize(obj: dict) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n"


def _gen_probe_csv(seed: int, rows: int, path: str) -> None:
    rng = random.Random(seed)
    regions = ["north", "south", "east", "west", ""]
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["id", "region", "score", "qty", "note"])
        for i in range(rows):
            region = rng.choice(regions)
            score = "" if rng.random() < 0.1 else str(
                round(rng.uniform(-50, 150), 3))
            qty = str(rng.randint(0, 999))
            note = rng.choice(["ok", "check", "n/a", "", "priority"])
            w.writerow([str(i + 1), region, score, qty, note])


def _run_pipeline(pipeline: str, csv_in: str, out_path: str,
                  timeout: int = 120) -> tuple[bool, str]:
    try:
        r = subprocess.run([sys.executable, pipeline, csv_in, out_path],
                           cwd=REPO, env=runner_env(), capture_output=True,
                           text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return False, "pipeline timed out"
    if r.returncode != 0:
        return False, f"pipeline exit {r.returncode}: {r.stderr[-200:]}"
    if not os.path.isfile(out_path):
        return False, "pipeline produced no output file"
    return True, ""


def gate_etl(g: dict) -> tuple[bool, str]:
    pipeline = os.path.join(REPO, g["pipeline"])
    if not os.path.isfile(pipeline):
        return False, f"{g['pipeline']} missing"
    with tempfile.TemporaryDirectory() as tmp:
        mode = g["mode"]
        if mode in ("dataset", "double_run"):
            csv_in = os.path.join(REPO, g["csv"])
            out1 = os.path.join(tmp, "out1.json")
            ok, why = _run_pipeline(pipeline, csv_in, out1)
            if not ok:
                return False, why
            got = open(out1, "r", encoding="utf-8").read()
            want = _etl_serialize(_etl_metrics(csv_in))
            if got != want:
                return False, "output does not byte-match the sealed metric spec"
            if mode == "double_run":
                out2 = os.path.join(tmp, "out2.json")
                ok, why = _run_pipeline(pipeline, csv_in, out2)
                if not ok:
                    return False, why
                if open(out2, "rb").read() != open(out1, "rb").read():
                    return False, "two identical runs differ (non-deterministic)"
            return True, ""
        if mode == "probe":
            csv_in = os.path.join(tmp, "probe.csv")
            _gen_probe_csv(g["seed"], g["rows"], csv_in)
            out1 = os.path.join(tmp, "out.json")
            ok, why = _run_pipeline(pipeline, csv_in, out1)
            if not ok:
                return False, why
            got = open(out1, "r", encoding="utf-8").read()
            want = _etl_serialize(_etl_metrics(csv_in))
            if got != want:
                return False, "probe dataset output mismatch (hard-coded goldens?)"
            return True, ""
    return False, f"unknown etl mode {g.get('mode')!r}"


# ---------------- log-probe reference (used by gate_logprobe) ----------------

def _gen_probe_log(seed: int, lines: int, path: str) -> None:
    rng = random.Random(seed)
    levels = ["info", "warn", "error", "debug"]
    with open(path, "w", encoding="utf-8", newline="") as f:
        for i in range(lines):
            level = rng.choice(levels)
            byts = rng.randint(0, 50000)
            svc = rng.choice(["api", "worker", "cron"])
            f.write(f'ts=2026-01-{rng.randint(1, 28):02d} level={level} '
                    f'service={svc} bytes={byts} msg="event {i}"\n')


def gate_logprobe(g: dict) -> tuple[bool, str]:
    cli = os.path.join(REPO, g["cli"])
    if not os.path.isfile(cli):
        return False, f"{g['cli']} missing"
    with tempfile.TemporaryDirectory() as tmp:
        log_path = os.path.join(tmp, "probe.log")
        _gen_probe_log(g["seed"], g["lines"], log_path)
        counts: dict[str, int] = {}
        for line in open(log_path, "r", encoding="utf-8"):
            m = re.search(r"level=(\w+)", line)
            counts[m.group(1)] = counts.get(m.group(1), 0) + 1
        want = "".join(f"{k} {counts[k]}\n"
                       for k in sorted(counts, key=lambda k: (-counts[k], k)))
        try:
            r = subprocess.run([sys.executable, cli, "count-by", "level",
                                log_path], cwd=REPO, env=runner_env(),
                               capture_output=True, text=True, timeout=120)
        except subprocess.TimeoutExpired:
            return False, "cli timed out on probe log"
        if r.returncode != 0:
            return False, f"cli exit {r.returncode} on probe log"
        if r.stdout != want:
            return False, "cli count-by output mismatch on generated probe"
    return True, ""


GATE_FNS = {"plan": gate_plan, "chain": gate_chain, "suite": gate_suite,
            "mutation": gate_mutation, "ledger": gate_ledger,
            "runslog": gate_runslog, "cost": gate_cost,
            "import_ban": gate_import_ban, "runtime": gate_runtime,
            "etl": gate_etl, "logprobe": gate_logprobe}


def main() -> None:
    cfg = load_config()
    for rel, sha in cfg.get("sealed_files", {}).items():
        path = os.path.join(REPO, rel)
        if not os.path.isfile(path):
            hard_fail(f"sealed asset {rel} missing")
        if sha256_file(path) != sha:
            hard_fail(f"sealed asset {rel} was modified")
    ensure_pytest(cfg.get("pytest_version", "8.3.4"))
    for g in cfg["gates"]:
        fn = GATE_FNS.get(g["type"])
        if fn is None:
            hard_fail(f"unknown gate type {g['type']!r}")
        try:
            ok, detail = fn(g)
        except Exception as exc:  # fail-closed, never a false pass
            ok, detail = False, f"gate crashed: {type(exc).__name__}: {exc}"
        GATES.append((g["name"], ok, detail))
    score = sum(1 for _n, ok, _d in GATES if ok)
    emit(score, len(cfg["gates"]))


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:
        hard_fail(f"grader internal error: {type(exc).__name__}: {exc}")
