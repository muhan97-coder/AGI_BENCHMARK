#!/usr/bin/env python3
"""Sealed grader for gc-320 (AGI_BENCHMARK swebench_scale band).

Run from the benchmark repo root: python3 assets/gc-320/grade.py
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


sealed = set(read_lines("assets/gc-320/instances.txt"))
preds = load_preds("runs/gc-320/predictions.jsonl", sealed)
if set(preds) != sealed:
    die("predictions must cover every sealed instance exactly once")
report = load_json("runs/gc-320/report.json")
res, unres, empty, err = check_report(report, sealed, "report", True)
resolved_have_patches(res, preds)
empty_n = sum(1 for iid in sealed if not preds[iid].strip())
gates_ok = empty_n <= 12 and len(err) <= 7
value = len(res) if gates_ok else -1
print(json.dumps({"scaled_resolved": value, "resolved": len(res),
                  "empty_count": empty_n, "error_count": len(err)}))
