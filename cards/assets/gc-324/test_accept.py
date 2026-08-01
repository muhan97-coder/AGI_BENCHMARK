"""Sealed acceptance suite for gc-324 (MARBLE coding task_id=5: OfficeTaskScheduler).

Loads the agent's solution from workspace/gc-324/solution.py relative to the
benchmark repo root. Graders run the pinned copy of this file; do not modify it.
"""
import importlib.util
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_SOLUTION = _ROOT / "workspace" / "gc-324" / "solution.py"


def _load():
    spec = importlib.util.spec_from_file_location("solution_gc324", _SOLUTION)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def sched():
    mod = _load()
    s = mod.OfficeTaskScheduler()
    for u in ("alice", "bob", "cara"):
        s.add_user(u)
    return s


def test_duplicate_user_rejected(sched):
    with pytest.raises(ValueError):
        sched.add_user("alice")


def test_task_ids_increment(sched):
    t1 = sched.create_task("alice", "write spec", "bob", "2030-01-10", 3, "2030-01-01")
    t2 = sched.create_task("alice", "review spec", "cara", "2030-01-11", 2, "2030-01-01")
    assert (t1, t2) == (1, 2)


def test_unknown_assignee_rejected(sched):
    with pytest.raises(KeyError):
        sched.create_task("alice", "x", "nobody", "2030-01-10", 3, "2030-01-01")


def test_past_deadline_rejected(sched):
    with pytest.raises(ValueError):
        sched.create_task("alice", "x", "bob", "2029-12-31", 3, "2030-01-01")


def test_priority_bounds(sched):
    with pytest.raises(ValueError):
        sched.create_task("alice", "x", "bob", "2030-01-10", 0, "2030-01-01")
    with pytest.raises(ValueError):
        sched.create_task("alice", "x", "bob", "2030-01-10", 6, "2030-01-01")


def test_dashboard_sorted(sched):
    a = sched.create_task("alice", "late", "bob", "2030-02-01", 1, "2030-01-01")
    b = sched.create_task("alice", "soon-lo", "bob", "2030-01-05", 2, "2030-01-01")
    c = sched.create_task("alice", "soon-hi", "bob", "2030-01-05", 5, "2030-01-01")
    rows = sched.dashboard("bob")
    assert [r["task_id"] for r in rows] == [c, b, a]
    assert rows[0]["title"] == "soon-hi"
    assert rows[0]["status"] == "pending"
    assert set(rows[0].keys()) >= {"task_id", "title", "status", "deadline", "priority"}


def test_dashboard_unknown_user(sched):
    with pytest.raises(KeyError):
        sched.dashboard("nobody")


def test_update_status_only_assignee(sched):
    t = sched.create_task("alice", "x", "bob", "2030-01-10", 3, "2030-01-01")
    with pytest.raises(PermissionError):
        sched.update_status("cara", t, "in_progress")


def test_update_status_invalid_value(sched):
    t = sched.create_task("alice", "x", "bob", "2030-01-10", 3, "2030-01-01")
    with pytest.raises(ValueError):
        sched.update_status("bob", t, "done")


def test_status_lifecycle(sched):
    t = sched.create_task("alice", "x", "bob", "2030-01-10", 3, "2030-01-01")
    sched.update_status("bob", t, "in_progress")
    assert sched.dashboard("bob")[0]["status"] == "in_progress"
    sched.update_status("bob", t, "completed")
    assert sched.dashboard("bob")[0]["status"] == "completed"


def test_assignment_notification(sched):
    t = sched.create_task("alice", "x", "bob", "2030-01-10", 3, "2030-01-01")
    assert f"assigned:{t}" in sched.notifications("bob")
    assert sched.notifications("cara") == []


def test_comments_permission_and_order(sched):
    t = sched.create_task("alice", "x", "bob", "2030-01-10", 3, "2030-01-01")
    sched.add_comment("alice", t, "first")
    sched.add_comment("bob", t, "second")
    with pytest.raises(PermissionError):
        sched.add_comment("cara", t, "nope")
    assert [list(c) for c in sched.comments(t)] == [["alice", "first"], ["bob", "second"]]


def test_due_soon_window(sched):
    t1 = sched.create_task("alice", "today", "bob", "2030-01-01", 3, "2030-01-01")
    t2 = sched.create_task("alice", "in2", "bob", "2030-01-03", 3, "2030-01-01")
    sched.create_task("alice", "in5", "bob", "2030-01-06", 3, "2030-01-01")
    t4 = sched.create_task("alice", "done", "bob", "2030-01-02", 3, "2030-01-01")
    sched.update_status("bob", t4, "completed")
    assert sched.due_soon("bob", "2030-01-01", days=2) == sorted([t1, t2])


def test_report_contents(sched):
    t1 = sched.create_task("alice", "a", "bob", "2030-01-02", 3, "2030-01-01")
    t2 = sched.create_task("alice", "b", "cara", "2030-01-03", 3, "2030-01-01")
    sched.create_task("bob", "c", "cara", "2030-02-01", 3, "2030-01-01")
    sched.update_status("bob", t1, "completed")
    rep = sched.report("2030-01-05")
    assert abs(rep["completion_rate"] - (1 / 3)) < 1e-9
    assert rep["overdue"] == [t2]
    assert rep["per_user"] == {"alice": 0, "bob": 1, "cara": 2}


def test_report_empty(sched):
    rep = sched.report("2030-01-01")
    assert rep["completion_rate"] == 0.0
    assert rep["overdue"] == []
