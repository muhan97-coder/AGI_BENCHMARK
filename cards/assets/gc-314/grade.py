#!/usr/bin/env python3
"""Sealed grader for gc-314 (AGI_BENCHMARK swebench_scale band).

Run from the benchmark repo root: python3 assets/gc-314/grade.py
Prints exactly one JSON line. Fail-closed: any missing, unreadable or
inconsistent artifact prints an error object WITHOUT the metric key and
exits non-zero, which the harness records as EXTRACT_FAIL (RED).
"""
import hashlib
import json
import os
import sys


def die(msg):
    print(json.dumps({"error": msg}))
    sys.exit(2)


def read_lines(path):
    if not os.path.isfile(path):
        die("missing sealed asset: " + path)
    with open(path) as f:
        ids = [ln.strip() for ln in f if ln.strip()]
    if not ids:
        die("empty sealed asset: " + path)
    return ids


def load_json(path):
    if not os.path.isfile(path):
        die("missing artifact: " + path)
    try:
        with open(path) as f:
            return json.load(f)
    except Exception as exc:
        die("unparseable JSON " + path + ": " + str(exc))


def id_set(report, key, where):
    v = report.get(key)
    if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
        die(where + " missing string-list key: " + key)
    return set(v)


def opt_set(report, key):
    v = report.get(key)
    return set(v) if isinstance(v, list) and all(isinstance(x, str) for x in v) else set()


def check_report(report, sealed, where, require_coverage):
    if not isinstance(report, dict):
        die(where + " is not a JSON object")
    res = id_set(report, "resolved_ids", where)
    unres = opt_set(report, "unresolved_ids")
    empty = opt_set(report, "empty_patch_ids")
    err = opt_set(report, "error_ids")
    if not res <= sealed:
        die(where + ": resolved_ids outside the sealed instance set")
    if res & (unres | empty | err):
        die(where + ": status id lists overlap")
    if require_coverage and (res | unres | empty | err) != sealed:
        die(where + ": union of status id lists must equal the sealed set")
    ri = report.get("resolved_instances")
    if isinstance(ri, int) and ri != len(res):
        die(where + ": resolved_instances count inconsistent with resolved_ids")
    return res, unres, empty, err


def load_preds(path, sealed):
    if not os.path.isfile(path):
        die("missing predictions file: " + path)
    preds = {}
    with open(path) as f:
        for n, ln in enumerate(f, 1):
            ln = ln.strip()
            if not ln:
                continue
            try:
                obj = json.loads(ln)
            except Exception as exc:
                die(path + " line " + str(n) + " is not valid JSON: " + str(exc))
            iid = obj.get("instance_id")
            if not isinstance(iid, str):
                die(path + " line " + str(n) + " has no instance_id")
            if iid in preds:
                die("duplicate prediction for " + iid)
            patch = obj.get("model_patch")
            preds[iid] = patch if isinstance(patch, str) else ""
    if not set(preds) <= sealed:
        die(path + ": prediction instance_ids outside the sealed set")
    return preds


def resolved_have_patches(res, preds):
    for iid in sorted(res):
        if not preds.get(iid, "").strip():
            die("resolved instance has an empty model_patch: " + iid)


def orgs(ids):
    return set(i.split("__")[0] for i in ids)


sealed = set(read_lines("assets/gc-314/instances.txt"))
preds_path = "runs/gc-314/predictions.jsonl"
preds = load_preds(preds_path, sealed)
baseline = load_json("runs/gc-314/sealed_baseline.json")
if not isinstance(baseline, dict):
    die("sealed_baseline.json is not a JSON object")
base = id_set(baseline, "resolved_ids", "sealed_baseline")
if not base <= sealed:
    die("baseline resolved_ids outside the sealed instance set")
want_sha = baseline.get("predictions_sha256")
if not isinstance(want_sha, str) or len(want_sha) != 64:
    die("sealed_baseline.json missing 64-hex predictions_sha256")
with open(preds_path, "rb") as f:
    got_sha = hashlib.sha256(f.read()).hexdigest()
if got_sha != want_sha.lower():
    die("predictions.jsonl sha256 does not match the sealed baseline snapshot")
regrade = load_json("runs/gc-314/report_regrade.json")
res = check_report(regrade, sealed, "report_regrade", True)[0]
resolved_have_patches(res, preds)
value = len(base) if res == base else -1
print(json.dumps({"sealed_regrade_resolved": value,
                  "baseline_size": len(base), "regrade_resolved": len(res)}))
