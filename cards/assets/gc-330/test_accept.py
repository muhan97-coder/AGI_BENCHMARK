"""Sealed acceptance suite for gc-330 (MARBLE coding task_id=90: MultiAgentTaskScheduler).

Loads the agent's solution from workspace/gc-330/solution.py relative to the
benchmark repo root. Graders run the pinned copy of this file; do not modify it.
"""
import importlib.util
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_SOLUTION = _ROOT / "workspace" / "gc-330" / "solution.py"


def _load():
    spec = importlib.util.spec_from_file_location("solution_gc330", _SOLUTION)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def sc():
    s = _load().MultiAgentTaskScheduler()
    s.add_agent("amy", 1)
    s.add_agent("bob", 2)
    return s


def test_agent_validation(sc):
    with pytest.raises(ValueError):
        sc.add_agent("amy", 1)
    with pytest.raises(ValueError):
        sc.add_agent("new", 0)


def test_task_duplicate(sc):
    sc.add_task("t1", 5, 0)
    with pytest.raises(ValueError):
        sc.add_task("t1", 3, 1)


def test_immediate_assignment_least_loaded(sc):
    sc.add_task("t1", 5, 0)
    # amy load 0, bob load 0 -> alphabetical: amy
    assert sc.status("t1") == "in_progress"
    assert sc.assignee("t1") == "amy"
    sc.add_task("t2", 5, 1)
    assert sc.assignee("t2") == "bob"
    sc.add_task("t3", 5, 2)
    assert sc.assignee("t3") == "bob"  # amy full (cap 1), bob load 1 of 2


def test_capacity_respected(sc):
    for i in range(4):
        sc.add_task(f"t{i}", 5, i)
    assert sc.status("t3") == "pending"
    assert sc.assignee("t3") is None


def test_priority_order_on_free_slot(sc):
    for i in range(3):
        sc.add_task(f"fill{i}", 9, 0)
    sc.add_task("low", 1, 1)
    sc.add_task("high", 8, 2)
    assert sc.status("low") == "pending" and sc.status("high") == "pending"
    sc.complete("amy", "fill0", 3)
    assert sc.status("high") == "in_progress"
    assert sc.status("low") == "pending"


def test_fifo_among_equal_priority(sc):
    for i in range(3):
        sc.add_task(f"fill{i}", 9, 0)
    sc.add_task("first", 5, 1)
    sc.add_task("second", 5, 2)
    sc.complete("amy", "fill0", 3)
    assert sc.status("first") == "in_progress"
    assert sc.status("second") == "pending"


def test_complete_wrong_agent(sc):
    sc.add_task("t1", 5, 0)
    with pytest.raises(PermissionError):
        sc.complete("bob", "t1", 1)


def test_complete_not_in_progress(sc):
    sc.add_task("t1", 5, 0)
    sc.complete("amy", "t1", 1)
    with pytest.raises(RuntimeError):
        sc.complete("amy", "t1", 2)


def test_unavailable_requeues_to_other_agent(sc):
    sc.add_task("t1", 5, 0)  # amy
    assert sc.assignee("t1") == "amy"
    sc.set_unavailable("amy", 1)
    assert sc.assignee("t1") == "bob"
    assert sc.status("t1") == "in_progress"


def test_unavailable_agent_gets_nothing_until_available(sc):
    sc.set_unavailable("bob", 0)
    sc.add_task("t1", 5, 1)
    sc.add_task("t2", 5, 2)
    assert sc.assignee("t1") == "amy"
    assert sc.status("t2") == "pending"
    sc.set_available("bob", 3)
    assert sc.assignee("t2") == "bob"


def test_history_event_identities(sc):
    sc.add_task("t1", 5, 0)
    sc.set_unavailable("amy", 1)
    sc.complete("bob", "t1", 2)
    events = [(h["event"], h["task"], h["agent"], h["time"]) for h in sc.history()]
    assert events == [
        ("assigned", "t1", "amy", 0),
        ("requeued", "t1", "amy", 1),
        ("assigned", "t1", "bob", 1),
        ("completed", "t1", "bob", 2),
    ]


def test_messaging(sc):
    sc.send("amy", "bob", "handing off t1")
    sc.send("bob", "amy", "ack")
    assert [list(m) for m in sc.inbox("bob")] == [["amy", "handing off t1"]]
    assert [list(m) for m in sc.inbox("amy")] == [["bob", "ack"]]
    with pytest.raises(KeyError):
        sc.send("amy", "ghost", "x")


def test_tasks_by_status(sc):
    sc.add_task("b-task", 5, 0)
    sc.add_task("a-task", 5, 1)
    sc.complete("amy", "b-task", 2)
    assert sc.tasks_by_status("completed") == ["b-task"]
    assert sc.tasks_by_status("in_progress") == ["a-task"]
    with pytest.raises(ValueError):
        sc.tasks_by_status("done")


def test_find_keyword(sc):
    sc.add_task("deploy-api", 5, 0, description="ship the api service")
    sc.add_task("write-docs", 4, 1, description="document the api")
    sc.add_task("cleanup", 3, 2, description="remove dead code")
    assert sc.find("api") == ["deploy-api", "write-docs"]
    assert sc.find("dead") == ["cleanup"]
    assert sc.find("zzz") == []


def test_unknown_task_lookups(sc):
    with pytest.raises(KeyError):
        sc.status("ghost")
    with pytest.raises(KeyError):
        sc.assignee("ghost")
