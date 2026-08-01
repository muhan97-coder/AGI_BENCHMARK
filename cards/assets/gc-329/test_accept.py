"""Sealed acceptance suite for gc-329 (MARBLE coding task_id=50: MultiAgentBudgetOptimizer).

Loads the agent's solution from workspace/gc-329/solution.py relative to the
benchmark repo root. Graders run the pinned copy of this file; do not modify it.
"""
import importlib.util
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_SOLUTION = _ROOT / "workspace" / "gc-329" / "solution.py"


def _load():
    spec = importlib.util.spec_from_file_location("solution_gc329", _SOLUTION)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def bo():
    b = _load().BudgetOptimizer()
    for u in ("kim", "lee", "max"):
        b.add_user(u)
    for cat, lim in (("groceries", 400), ("entertainment", 150), ("utilities", 200)):
        b.set_limit(cat, lim)
    return b


def test_duplicate_user(bo):
    with pytest.raises(ValueError):
        bo.add_user("kim")


def test_limit_validation(bo):
    with pytest.raises(ValueError):
        bo.set_limit("misc", 0)
    with pytest.raises(ValueError):
        bo.set_limit("misc", -10)


def test_expense_unknown_user(bo):
    with pytest.raises(KeyError):
        bo.add_expense("ghost", "groceries", 10)


def test_expense_requires_planned_category(bo):
    with pytest.raises(KeyError):
        bo.add_expense("kim", "unplanned", 10)


def test_expense_amount_validation(bo):
    with pytest.raises(ValueError):
        bo.add_expense("kim", "groceries", 0)
    with pytest.raises(ValueError):
        bo.add_expense("kim", "groceries", -5)
    with pytest.raises(ValueError):
        bo.add_expense("kim", "groceries", "ten")
    with pytest.raises(ValueError):
        bo.add_expense("kim", "groceries", True)


def test_summary_totals(bo):
    bo.add_expense("kim", "groceries", 120)
    bo.add_expense("lee", "groceries", 80)
    bo.add_expense("lee", "entertainment", 40)
    s = bo.summary()
    assert s["total_budget"] == 750
    assert s["total_expenses"] == 240
    assert s["remaining"] == 510
    assert s["contributions"] == {"kim": 120, "lee": 120, "max": 0}


def test_category_status(bo):
    bo.add_expense("kim", "entertainment", 180)
    st = bo.category_status("entertainment")
    assert st == {"limit": 150, "spent": 180, "remaining": -30, "over": True}
    st2 = bo.category_status("utilities")
    assert st2 == {"limit": 200, "spent": 0, "remaining": 200, "over": False}
    with pytest.raises(KeyError):
        bo.category_status("ghost")


def test_reallocate_moves_limits(bo):
    bo.reallocate("groceries", "entertainment", 100)
    assert bo.category_status("groceries")["limit"] == 300
    assert bo.category_status("entertainment")["limit"] == 250
    assert bo.summary()["total_budget"] == 750


def test_reallocate_validation(bo):
    with pytest.raises(KeyError):
        bo.reallocate("ghost", "groceries", 10)
    with pytest.raises(ValueError):
        bo.reallocate("groceries", "utilities", 0)


def test_reallocate_insufficient_headroom(bo):
    bo.add_expense("kim", "groceries", 350)
    with pytest.raises(ValueError):
        bo.reallocate("groceries", "utilities", 100)
    assert bo.category_status("groceries")["limit"] == 400
    assert bo.category_status("utilities")["limit"] == 200


def test_optimize_empty_when_under(bo):
    bo.add_expense("kim", "groceries", 100)
    assert bo.optimize() == []


def test_optimize_order_and_amounts(bo):
    bo.add_expense("kim", "groceries", 460)      # over by 60
    bo.add_expense("lee", "entertainment", 240)  # over by 90
    bo.add_expense("max", "utilities", 260)      # over by 60
    out = [list(x) for x in bo.optimize()]
    assert out == [["entertainment", 90], ["groceries", 60], ["utilities", 60]]


def test_savings_gap(bo):
    bo.add_expense("kim", "groceries", 460)  # overshoot 60
    assert bo.savings_gap(100) == 40
    assert bo.savings_gap(50) == 0
    assert bo.savings_gap(60) == 0


def test_contributions_track_multiple_expenses(bo):
    for amt in (10, 20, 30):
        bo.add_expense("max", "utilities", amt)
    assert bo.summary()["contributions"]["max"] == 60
