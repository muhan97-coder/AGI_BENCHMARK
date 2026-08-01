#!/usr/bin/env python3
"""Fail-closed grader for ex-frontier_arc (offline teaching example).

Same contract and same cell-exact scoring as the scored frontier_arc graders
(cf. cards/assets/gc-440/grade.py). The single difference: the scored cards
download the gold task files from a pinned commit of the public ARC-AGI-2
repository at grade time, so the gold outputs never sit in the agent's
workspace. This example is offline by design, so its three HAND-MADE puzzles
carry their gold next to the grader in gold/ -- which is exactly why the card
is marked "scored": false.

Prediction contract (path relative to the workspace root the command runs from):
    runs/ex-frontier_arc/predictions.json
        {"<task_id>": [<per-test-entry>, ...], ...}
    One per-test-entry per test input, in task-file order. Each entry is ONE
    of: a grid, a list of at most two attempt grids, or a dict
    {"attempt_1": grid, "attempt_2": grid}. A grid is a non-empty list of
    equal-length non-empty rows of integers 0..9. For single-test tasks a
    bare grid or a bare list of at most two attempt grids is also accepted.

Scoring (ARC rules): a test output is matched when any of its at most two
attempts equals the gold grid cell-exactly; a task is solved only when every
one of its test outputs is matched. Missing, unreadable, or malformed
predictions -> {"solved": 0}. Gold that cannot be read -> {"solved": 0}
(fail-closed: nothing is certified without gold). The final stdout line is
always the JSON verdict {"solved": N}.
"""
import json
import os
import sys

CARD = "ex-frontier_arc"
HERE = os.path.dirname(os.path.abspath(__file__))
TASK_IDS_PATH = os.path.join(HERE, "task_ids.txt")
GOLD_DIR = os.path.join(HERE, "gold")
PREDICTIONS_PATH = os.path.join("runs", CARD, "predictions.json")
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


def load_gold(task_id):
    path = os.path.join(GOLD_DIR, task_id + ".json")
    with open(path) as fh:
        gold = json.load(fh)
    tests = gold.get("test")
    if not isinstance(tests, list) or not tests:
        raise RuntimeError("gold for %s has no test cases" % task_id)
    for case in tests:
        if as_grid(case.get("output")) is None:
            raise RuntimeError("gold for %s has an unreadable output grid" % task_id)
    return tests


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
            gold = load_gold(task_id)
        except Exception as err:
            note("could not read gold for %s: %r" % (task_id, err))
            finish(0)
        ok = task_id in predictions and task_solved(predictions[task_id], gold)
        note("%s %s" % (task_id, "SOLVED" if ok else "not-solved"))
        if ok:
            solved += 1
    finish(solved)


if __name__ == "__main__":
    main()
