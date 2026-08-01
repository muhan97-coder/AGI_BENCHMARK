#!/usr/bin/env python3
"""Sealed mutation-testing grader (AGI_BENCHMARK, mutation band).

Reads config.json sitting next to this file. Re-runs the full mutation
analysis from scratch against pinned PyPI packages, scoring ONLY the
agent-authored test suite found under the configured tests_dir
(work/gc-NNN/tests relative to the benchmark repo root, which is the cwd).

Contract:
  - Prints exactly one JSON object as the LAST line of stdout. The card's
    metric key is always present in that object.
  - Fail-closed: any setup, integrity, or determinism failure yields a
    disqualifying metric value (-1 for >= metrics, 999999999 for <= metrics)
    instead of a crash, so the verdict is always FAIL, never a false PASS.
  - Deterministic: every package version is pinned and verified after
    install; the mutant total per target file is compared against the
    sealed expected count. Any drift disqualifies the run.

Anti-gaming guards:
  - Test files are scanned for source-introspection tokens (reading the
    mutated file's text instead of testing behavior).
  - Integrity probe: a comment is appended to each target file and the
    suite is re-run. A suite that fails on this semantically identical
    variant is disqualified (it depends on source text, not behavior).
  - After mutation runs, target files must be byte-identical to the
    originals (mutmut restores them; a mismatch disqualifies).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = json.load(open(os.path.join(HERE, "config.json")))

METRIC = CONFIG["metric_name"]
FAIL_VALUE = -1 if CONFIG["fail_direction"] == "low" else 999999999

BANNED_TOKENS = [
    "__file__", "__spec__", "__loader__", "find_spec", "get_source",
    "getsource", "getsourcefile", "getfile", "co_filename", "linecache",
    "hashlib", "mutmut", "MUTANT", "site-packages",
]

REPORT: dict = {"card": CONFIG["card"], METRIC: FAIL_VALUE}


def emit_and_exit() -> None:
    print(json.dumps(REPORT, sort_keys=True))
    sys.exit(0)


def disqualify(reason: str) -> None:
    REPORT["disqualified"] = reason
    REPORT[METRIC] = FAIL_VALUE
    emit_and_exit()


def sh(cmd: list[str], cwd: str | None = None, timeout: int = 600,
       env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, env=env, timeout=timeout,
                          capture_output=True, text=True)


def runner_env() -> dict:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    return env


def main() -> None:
    t0 = time.time()

    # 1. Install pinned packages, then verify the exact versions are live.
    pip = sh([sys.executable, "-m", "pip", "install", "--quiet",
              "--disable-pip-version-check", *CONFIG["pins"]], timeout=420)
    if pip.returncode != 0:
        disqualify("pip_install_failed: " + pip.stderr[-400:])
    probe = sh([sys.executable, "-c",
                "import importlib.metadata as m, json, sys;"
                "print(json.dumps({d: m.version(d) for d in sys.argv[1:]}))",
                *CONFIG["verify_versions"].keys()])
    if probe.returncode != 0:
        disqualify("version_probe_failed")
    live = json.loads(probe.stdout.strip())
    if live != CONFIG["verify_versions"]:
        disqualify(f"version_mismatch: {live}")

    # 2. Locate installed target files.
    files: dict[str, str] = {}
    originals: dict[str, bytes] = {}
    for grp in CONFIG["groups"]:
        loc = sh([sys.executable, "-c",
                  f"import {grp['module']}, os;"
                  f"print(os.path.dirname({grp['module']}.__file__))"])
        if loc.returncode != 0:
            disqualify(f"import_failed: {grp['module']}")
        path = os.path.join(loc.stdout.strip(), grp["file"])
        if not os.path.isfile(path):
            disqualify(f"target_file_missing: {grp['name']}")
        files[grp["name"]] = path
        originals[grp["name"]] = open(path, "rb").read()

    # 3. Collect the agent-authored test suite.
    tests_src = os.path.abspath(CONFIG["tests_dir"])
    if not os.path.isdir(tests_src):
        disqualify(f"tests_dir_missing: {CONFIG['tests_dir']}")
    names = sorted(f for f in os.listdir(tests_src) if f.endswith(".py"))
    if not any(f.startswith("test_") for f in names):
        disqualify("no_test_files")
    if len(names) > 40:
        disqualify("too_many_test_files")
    stage = tempfile.mkdtemp(prefix="mutgrade_")
    tests_dir = os.path.join(stage, "tests")
    os.makedirs(tests_dir)
    for f in names:
        src = os.path.join(tests_src, f)
        if os.path.getsize(src) > 200_000:
            disqualify(f"test_file_too_large: {f}")
        text = open(src, encoding="utf-8", errors="replace").read()
        for tok in BANNED_TOKENS:
            if re.search(re.escape(tok), text):
                disqualify(f"banned_token:{tok}:{f}")
        shutil.copy(src, os.path.join(tests_dir, f))

    runner = f"{sys.executable} -m pytest -x -q -p no:cacheprovider {tests_dir}"
    env = runner_env()

    # 4. Baseline: agent suite must be green and fast on the unmutated code.
    tb0 = time.time()
    base = sh(runner.split(), cwd=stage, timeout=CONFIG["max_suite_seconds"] + 60,
              env=env)
    suite_s = round(time.time() - tb0, 2)
    if base.returncode != 0:
        disqualify("baseline_red: " + (base.stdout + base.stderr)[-400:])
    if suite_s > CONFIG["max_suite_seconds"]:
        disqualify(f"suite_too_slow: {suite_s}s > {CONFIG['max_suite_seconds']}s")
    REPORT["baseline_suite_seconds"] = suite_s

    # 5. Integrity probe: append a comment to each target; suite must stay green.
    for name, path in files.items():
        with open(path, "ab") as fh:
            fh.write(b"\n# integrity-probe: semantically identical variant\n")
        rc = sh(runner.split(), cwd=stage, timeout=CONFIG["max_suite_seconds"] + 60,
                env=env).returncode
        with open(path, "wb") as fh:
            fh.write(originals[name])
        if rc != 0:
            disqualify(f"suite_depends_on_source_text: {name}")

    # 6. Mutation runs (one isolated run per target group).
    groups_out = []
    for grp in CONFIG["groups"]:
        gdir = os.path.join(stage, "run_" + re.sub(r"\W", "_", grp["name"]))
        os.makedirs(gdir)
        try:
            run = sh([os.path.dirname(sys.executable) + "/mutmut", "run",
                      "--paths-to-mutate", files[grp["name"]],
                      "--tests-dir", tests_dir,
                      "--runner", runner,
                      "--test-time-multiplier", "4.0",
                      "--test-time-base", "2.0",
                      "--simple-output", "--no-progress", "--CI"],
                     cwd=gdir, timeout=CONFIG["max_mutmut_seconds"], env=env)
        except subprocess.TimeoutExpired:
            disqualify(f"mutmut_timeout: {grp['name']}")
        if run.returncode != 0:
            disqualify(f"mutmut_fatal:{grp['name']}: "
                       + (run.stdout + run.stderr)[-400:])
        if open(files[grp["name"]], "rb").read() != originals[grp["name"]]:
            with open(files[grp["name"]], "wb") as fh:
                fh.write(originals[grp["name"]])
            disqualify(f"target_not_restored: {grp['name']}")
        counts = {}
        for status in ("killed", "survived", "timeout", "suspicious",
                       "skipped", "untested"):
            ids = sh([os.path.dirname(sys.executable) + "/mutmut",
                      "result-ids", status], cwd=gdir, env=env)
            counts[status] = len(ids.stdout.split())
        if counts["skipped"] or counts["untested"]:
            disqualify(f"incomplete_run: {grp['name']} {counts}")
        total = sum(counts.values())
        if total != grp["expected_mutants"]:
            disqualify(f"mutant_total_drift: {grp['name']} "
                       f"got {total} expected {grp['expected_mutants']}")
        killed_eff = counts["killed"] + counts["timeout"]
        survived_eff = counts["survived"] + counts["suspicious"]
        groups_out.append({"name": grp["name"], "total": total,
                           "killed": killed_eff, "survived": survived_eff,
                           "kill_rate": round(killed_eff / total, 4)})
    REPORT["groups"] = groups_out
    REPORT["wall_seconds"] = round(time.time() - t0, 1)

    # 7. Metric.
    mode = CONFIG["mode"]
    if mode == "kill_rate":
        REPORT[METRIC] = groups_out[0]["kill_rate"]
    elif mode == "min_module_kill_rate":
        REPORT[METRIC] = min(g["kill_rate"] for g in groups_out)
    elif mode == "survived_total":
        REPORT[METRIC] = sum(g["survived"] for g in groups_out)
    else:
        disqualify(f"bad_mode: {mode}")
    emit_and_exit()


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 - fail closed, never crash open
        disqualify(f"grader_exception: {type(exc).__name__}: {exc}")
