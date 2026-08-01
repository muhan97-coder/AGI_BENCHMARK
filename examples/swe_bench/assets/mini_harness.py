#!/usr/bin/env python3
"""Miniature stand-in for the pinned swebench docker harness (teaching demo).

The scored ``swe_bench`` / ``frontier_swe_hard`` cards run

    python3 -m swebench.harness.run_evaluation --dataset_name ... --predictions_path ...

which builds one docker image per instance environment (gigabytes, minutes).
This script is NOT SWE-bench. It reproduces SWE-bench's *grading contract* --
predictions.jsonl in, ``<model>.<run_id>.json`` report out,
``resolved_instances`` as the metric -- against miniature repos, in under a
second, with the standard library plus pytest.

Resolution rule (identical in shape to the real harness):

    resolved  <=>  the prediction's ``model_patch`` applies cleanly
                   AND every FAIL_TO_PASS test passes
                   AND every PASS_TO_PASS test still passes

The sealed tests are copied over the instance work tree *after* the patch is
applied, so a patch that edits tests cannot turn the run green.

Usage:
  python3 mini_harness.py --predictions runs/<id>/predictions.jsonl \
      --instances-dir assets/<id>/instances --instance-ids-file assets/<id>/instances.txt \
      --work-dir work/<id>/harness --report-dir . --run-id <id>

Exit code is 0 whenever the evaluation itself completed (even with zero
resolved instances) -- the numeric threshold, not the exit code, decides
PASS/FAIL. A non-zero exit means the harness could not evaluate at all.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Note: the oss_repair-shaped cards extract with the anchored "^(\d+) passed",
# which deliberately does NOT match "1 failed, 4 passed". Here the count is
# only for the human-readable log line -- resolution is decided by pytest's
# exit code -- so the unanchored form is used to report partial progress.
PASSED_RE = re.compile(r"(\d+) passed")
FAILED_ID_RE = re.compile(r"^(?:FAILED|ERROR) (\S+)", re.MULTILINE)


def run_tests(workdir: Path, rel_test: str) -> dict:
    """Run one sealed test file inside *workdir*; return counts + failure ids."""
    env = dict(os.environ)
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = str(workdir)
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "--noconftest",
             "-p", "no:cacheprovider", rel_test],
            cwd=str(workdir), env=env, capture_output=True, text=True, timeout=120)
        out = (proc.stdout or "") + (proc.stderr or "")
        rc = proc.returncode
    except subprocess.TimeoutExpired:
        out, rc = "harness: pytest timed out\n", -9
    m = PASSED_RE.search(out)
    lines = [ln for ln in out.strip().splitlines() if ln.strip()]
    return {"passed": int(m.group(1)) if m else 0,
            "ok": rc == 0,
            "failed_ids": sorted(set(FAILED_ID_RE.findall(out))),
            "summary": lines[-1] if lines else ""}


def load_predictions(path: Path) -> dict:
    preds: dict[str, dict] = {}
    for lineno, line in enumerate(path.read_text().splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)  # malformed JSONL is a hard error, by design
        iid = obj.get("instance_id")
        if not iid:
            raise ValueError(f"line {lineno}: prediction has no instance_id")
        preds[iid] = obj
    return preds


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--predictions", required=True)
    ap.add_argument("--instances-dir", required=True)
    ap.add_argument("--instance-ids-file", required=True)
    ap.add_argument("--work-dir", default="work/harness")
    ap.add_argument("--report-dir", default=".")
    ap.add_argument("--run-id", required=True)
    args = ap.parse_args()

    pred_path = Path(args.predictions)
    if not pred_path.is_file():
        # Printed on stdout on purpose: the grader keeps stdout as evidence.
        print(f"[harness] ERROR predictions file not found: {args.predictions}")
        return 2
    try:
        preds = load_predictions(pred_path)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"[harness] ERROR malformed predictions file: {exc}")
        return 2

    ids = [ln.strip() for ln in Path(args.instance_ids_file).read_text().splitlines()
           if ln.strip() and not ln.startswith("#")]
    models = sorted({p.get("model_name_or_path") for p in preds.values()} - {None})
    if len(models) > 1:
        print(f"[harness] ERROR predictions mix model_name_or_path values: {models}")
        return 2
    model = models[0] if models else args.run_id

    instances_dir = Path(args.instances_dir)
    work_root = Path(args.work_dir)
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True, exist_ok=True)

    records, resolved_ids, unresolved_ids = {}, [], []
    for iid in ids:
        src = instances_dir / iid
        rec: dict = {"instance_id": iid, "resolved": False}
        if not (src / "repo").is_dir():
            rec["cause"] = "missing_instance_assets"
            records[iid] = rec
            unresolved_ids.append(iid)
            print(f"[harness] {iid} resolved=False cause=missing_instance_assets")
            continue
        work = work_root / iid
        shutil.copytree(src / "repo", work)

        patch = (preds.get(iid) or {}).get("model_patch") or ""
        rec["empty_patch"] = not patch.strip()
        if patch.strip():
            applied = subprocess.run(
                ["git", "apply", "-p1", "--whitespace=nowarn", "-"],
                input=patch, cwd=str(work), capture_output=True, text=True)
            if applied.returncode != 0:
                err = (applied.stderr or "").strip().splitlines()
                rec["cause"] = "patch_apply_failed: " + (err[-1] if err else "unknown")
                records[iid] = rec
                unresolved_ids.append(iid)
                print(f"[harness] {iid} resolved=False cause={rec['cause']}")
                continue

        # Sealed tests land AFTER the patch: test tampering cannot go green.
        shutil.copytree(src / "tests", work / "tests", dirs_exist_ok=True)
        f2p = run_tests(work, "tests/test_fail_to_pass.py")
        p2p = run_tests(work, "tests/test_pass_to_pass.py")
        rec["FAIL_TO_PASS"], rec["PASS_TO_PASS"] = f2p, p2p
        rec["resolved"] = f2p["ok"] and p2p["ok"]
        if not rec["resolved"]:
            if not f2p["ok"]:
                rec["cause"] = "f2p_unfixed: " + (", ".join(f2p["failed_ids"]) or f2p["summary"])
            else:
                rec["cause"] = "p2p_regression: " + (", ".join(p2p["failed_ids"]) or p2p["summary"])
        records[iid] = rec
        (resolved_ids if rec["resolved"] else unresolved_ids).append(iid)
        print(f"[harness] {iid} resolved={rec['resolved']} "
              f"f2p={f2p['passed']} passed, p2p={p2p['passed']} passed"
              + ("" if rec["resolved"] else f" cause={rec['cause']}"))

    report = {
        "harness": "mini_harness.py (demo stand-in for swebench==4.1.0)",
        "run_id": args.run_id, "model": model,
        "total_instances": len(ids), "submitted_instances": len(preds),
        "resolved_instances": len(resolved_ids),
        "unresolved_instances": len(unresolved_ids),
        "resolved_ids": resolved_ids, "unresolved_ids": unresolved_ids,
        "instances": records,
    }
    report_dir = Path(args.report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{model}.{args.run_id}.json"
    report_path.write_text(json.dumps(report, indent=1) + "\n")
    print(f"[harness] report written: {report_path}")
    print(f"[harness] resolved_instances={len(resolved_ids)}/{len(ids)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
