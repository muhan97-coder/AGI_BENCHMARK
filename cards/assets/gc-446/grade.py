#!/usr/bin/env python3
"""Fail-closed grader for gc-446 (ARC-AGI-2 at a pinned commit).

Reads the sealed task-id list next to this script, downloads the gold task
JSONs for those ids from the pinned commit of github.com/arcprize/ARC-AGI-2,
and scores the agent predictions file cell-exactly. No LLM judgment.

Prediction contract (path relative to the repo root the command runs from):
    runs/gc-446/predictions.json
        {"<task_id>": [<per-test-entry>, ...], ...}
    One per-test-entry per test input, in task-file order. Each entry is ONE
    of: a grid, a list of at most two attempt grids, or a dict
    {"attempt_1": grid, "attempt_2": grid}. A grid is a non-empty list of
    equal-length non-empty rows of integers 0..9. For single-test tasks a
    bare grid or a bare list of at most two attempt grids is also accepted.

Scoring (ARC rules): a test output is matched when any of its at most two
attempts equals the gold grid cell-exactly; a task is solved only when every
one of its test outputs is matched. Missing, unreadable, or malformed
predictions -> {"solved": 0}. Gold that cannot be fetched -> {"solved": 0}
(fail-closed: nothing is certified without gold). The final stdout line is
always the JSON verdict {"solved": N}.
"""
import json
import os
import sys
import urllib.error
import urllib.request

CARD = "gc-446"
PINNED_COMMIT = "f3283f727488ad98fe575ea6a5ac981e4a188e49"
RAW_BASE = "https://raw.githubusercontent.com/arcprize/ARC-AGI-2/" + PINNED_COMMIT
SPLITS = ("training", "evaluation")
HERE = os.path.dirname(os.path.abspath(__file__))
TASK_IDS_PATH = os.path.join(HERE, "task_ids.txt")
PREDICTIONS_PATH = os.path.join("runs", CARD, "predictions.json")
GOLD_CACHE_DIR = os.path.join("runs", CARD, "gold_cache")
MAX_ATTEMPTS = 2


def note(msg):
    sys.stderr.write("[grade %s] %s\n" % (CARD, msg))


def finish(solved):
    print(json.dumps({"solved": int(solved)}))
    sys.exit(0)


def load_task_ids():
    with open(TASK_IDS_PATH) as fh:
        ids = [line.strip() for line in fh if line.strip()]
    if not ids:
        raise RuntimeError("sealed task-id list is empty")
    return ids


def fetch_gold(task_id):
    os.makedirs(GOLD_CACHE_DIR, exist_ok=True)
    cached = os.path.join(GOLD_CACHE_DIR, task_id + ".json")
    if os.path.exists(cached):
        try:
            with open(cached) as fh:
                return json.load(fh)
        except ValueError:
            os.remove(cached)
    last_err = None
    for split in SPLITS:
        url = "%s/data/%s/%s.json" % (RAW_BASE, split, task_id)
        for _ in range(3):
            try:
                with urllib.request.urlopen(url, timeout=60) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                with open(cached, "w") as fh:
                    json.dump(data, fh)
                return data
            except urllib.error.HTTPError as err:
                last_err = err
                if err.code == 404:
                    break  # wrong split for this id; try the next split
            except Exception as err:  # transient network error: retry
                last_err = err
    raise RuntimeError(
        "could not fetch gold task %s at pinned commit: %r" % (task_id, last_err))


def as_grid(obj):
    if not isinstance(obj, list) or not obj:
        return None
    rows, width = [], None
    for row in obj:
        if not isinstance(row, list) or not row:
            return None
        vals = []
        for cell in row:
            if isinstance(cell, bool) or not isinstance(cell, int) or not 0 <= cell <= 9:
                return None
            vals.append(cell)
        if width is None:
            width = len(vals)
        elif len(vals) != width:
            return None
        rows.append(vals)
    return rows


def attempts_from_entry(entry):
    """Normalize one per-test prediction entry to a list of at most two grids."""
    grid = as_grid(entry)
    if grid is not None:
        return [grid]
    if isinstance(entry, dict):
        candidates = [entry.get("attempt_1"), entry.get("attempt_2")]
    elif isinstance(entry, list):
        candidates = entry
    else:
        return []
    attempts = []
    for cand in candidates:
        grid = as_grid(cand)
        if grid is not None:
            attempts.append(grid)
        if len(attempts) == MAX_ATTEMPTS:
            break
    return attempts


def task_solved(pred_value, gold_tests):
    if len(gold_tests) == 1:
        if as_grid(pred_value) is not None:
            pred_value = [pred_value]
        elif isinstance(pred_value, list) and 1 <= len(pred_value) <= MAX_ATTEMPTS \
                and all(as_grid(x) is not None for x in pred_value):
            pred_value = [pred_value]
    if not isinstance(pred_value, list) or len(pred_value) != len(gold_tests):
        return False
    for entry, test_case in zip(pred_value, gold_tests):
        gold = test_case.get("output")
        attempts = attempts_from_entry(entry)
        if not attempts or not any(a == gold for a in attempts):
            return False
    return True


def main():
    try:
        task_ids = load_task_ids()
    except Exception as err:
        note("failed to read sealed task ids: %r" % err)
        finish(0)
    if not os.path.exists(PREDICTIONS_PATH):
        note("predictions file missing: %s" % PREDICTIONS_PATH)
        finish(0)
    try:
        with open(PREDICTIONS_PATH) as fh:
            predictions = json.load(fh)
    except Exception as err:
        note("predictions file unreadable: %r" % err)
        finish(0)
    if not isinstance(predictions, dict):
        note("predictions root must be an object mapping task_id -> entries")
        finish(0)
    solved = 0
    for task_id in task_ids:
        try:
            gold = fetch_gold(task_id)
        except Exception as err:
            note(str(err))
            finish(0)
        ok = task_id in predictions and task_solved(predictions[task_id], gold["test"])
        note("%s %s" % (task_id, "SOLVED" if ok else "not-solved"))
        if ok:
            solved += 1
    finish(solved)


if __name__ == "__main__":
    main()
