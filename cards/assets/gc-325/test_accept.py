"""Sealed acceptance suite for gc-325 (MARBLE coding task_id=46: TaskChain).

Loads the agent's solution from workspace/gc-325/solution.py relative to the
benchmark repo root. Graders run the pinned copy of this file; do not modify it.
"""
import importlib.util
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_SOLUTION = _ROOT / "workspace" / "gc-325" / "solution.py"


def _load():
    spec = importlib.util.spec_from_file_location("solution_gc325", _SOLUTION)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def tc():
    return _load().TaskChain()


@pytest.fixture()
def diamond(tc):
    # a -> b, a -> c, b -> d, c -> d
    for n in ("a", "b", "c", "d"):
        tc.add_task(n)
    tc.add_dependency("a", "b")
    tc.add_dependency("a", "c")
    tc.add_dependency("b", "d")
    tc.add_dependency("c", "d")
    return tc


def test_duplicate_task_rejected(tc):
    tc.add_task("a")
    with pytest.raises(ValueError):
        tc.add_task("a")


def test_dependency_unknown_task(tc):
    tc.add_task("a")
    with pytest.raises(KeyError):
        tc.add_dependency("a", "ghost")


def test_cycle_rejected(tc):
    tc.add_task("a")
    tc.add_task("b")
    tc.add_dependency("a", "b")
    with pytest.raises(ValueError):
        tc.add_dependency("b", "a")
    # the rejected edge must not have been added
    tc.start("a", 0)
    tc.complete("a", 1)
    tc.start("b", 2)  # must not raise


def test_self_dependency_rejected(tc):
    tc.add_task("a")
    with pytest.raises(ValueError):
        tc.add_dependency("a", "a")


def test_start_blocked_until_deps_complete(diamond):
    with pytest.raises(RuntimeError):
        diamond.start("b", 0)
    diamond.start("a", 0)
    with pytest.raises(RuntimeError):
        diamond.start("b", 1)
    diamond.complete("a", 1)
    diamond.start("b", 2)
    assert diamond.status("b") == "in_progress"


def test_status_lifecycle(tc):
    tc.add_task("a")
    assert tc.status("a") == "not_started"
    tc.start("a", 0)
    assert tc.status("a") == "in_progress"
    tc.complete("a", 1)
    assert tc.status("a") == "completed"


def test_complete_requires_started(tc):
    tc.add_task("a")
    with pytest.raises(RuntimeError):
        tc.complete("a", 1)


def test_complete_time_before_start(tc):
    tc.add_task("a")
    tc.start("a", 5)
    with pytest.raises(ValueError):
        tc.complete("a", 4)


def test_double_start_rejected(tc):
    tc.add_task("a")
    tc.start("a", 0)
    with pytest.raises(RuntimeError):
        tc.start("a", 1)


def test_ready_tasks_initial(diamond):
    assert diamond.ready_tasks() == ["a"]


def test_ready_tasks_progress(diamond):
    diamond.start("a", 0)
    assert diamond.ready_tasks() == []
    diamond.complete("a", 1)
    assert diamond.ready_tasks() == ["b", "c"]
    diamond.start("b", 2)
    diamond.complete("b", 3)
    assert diamond.ready_tasks() == ["c"]


def test_topological_order_valid(diamond):
    order = diamond.topological_order()
    assert sorted(order) == ["a", "b", "c", "d"]
    pos = {n: i for i, n in enumerate(order)}
    for before, after in [("a", "b"), ("a", "c"), ("b", "d"), ("c", "d")]:
        assert pos[before] < pos[after]


def test_events_completed_and_ready(diamond):
    diamond.start("a", 0)
    diamond.complete("a", 1)
    assert diamond.events() == ["completed:a", "ready:b", "ready:c"]
    diamond.start("b", 2)
    diamond.complete("b", 3)
    diamond.start("c", 4)
    diamond.complete("c", 5)
    assert diamond.events() == [
        "completed:a", "ready:b", "ready:c",
        "completed:b", "completed:c", "ready:d",
    ]


def test_comments(tc):
    tc.add_task("a")
    tc.comment("a", "dev1", "kickoff")
    tc.comment("a", "dev2", "ack")
    assert [list(c) for c in tc.comments("a")] == [["dev1", "kickoff"], ["dev2", "ack"]]
    with pytest.raises(KeyError):
        tc.comment("ghost", "dev1", "x")


def test_report_with_delays(tc):
    tc.add_task("a", deadline=10)
    tc.add_task("b", deadline=3)
    tc.add_task("c")
    tc.start("a", 0)
    tc.complete("a", 2)
    tc.start("b", 2)
    rep = tc.report(now=5)
    assert rep["completed"] == ["a"]
    assert rep["in_progress"] == ["b"]
    assert rep["not_started"] == ["c"]
    assert rep["delayed"] == ["b"]


def test_chain_unlocks_in_sequence(tc):
    for n in ("t1", "t2", "t3", "t4"):
        tc.add_task(n)
    tc.add_dependency("t1", "t2")
    tc.add_dependency("t2", "t3")
    tc.add_dependency("t3", "t4")
    with pytest.raises(RuntimeError):
        tc.start("t4", 0)
    t = 0
    for n in ("t1", "t2", "t3", "t4"):
        tc.start(n, t)
        tc.complete(n, t + 1)
        t += 2
    assert tc.report(now=t)["completed"] == ["t1", "t2", "t3", "t4"]
