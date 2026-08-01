"""Sealed acceptance suite for gc-327 (MARBLE coding task_id=12: BudgetSync).

Loads the agent's solution from workspace/gc-327/solution.py relative to the
benchmark repo root. Graders run the pinned copy of this file; do not modify it.
"""
import importlib.util
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_SOLUTION = _ROOT / "workspace" / "gc-327" / "solution.py"


def _load():
    spec = importlib.util.spec_from_file_location("solution_gc327", _SOLUTION)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def bs():
    b = _load().BudgetSync()
    for u in ("ann", "ben", "cleo"):
        b.register(u, f"pw-{u}")
    return b


@pytest.fixture()
def home(bs):
    bid = bs.create_budget("ann", "home")
    bs.invite("ann", bid, "ben", "editor")
    bs.invite("ann", bid, "cleo", "viewer")
    return bid


def test_register_duplicate(bs):
    with pytest.raises(ValueError):
        bs.register("ann", "other")


def test_login(bs):
    assert bs.login("ann", "pw-ann") is True
    assert bs.login("ann", "wrong") is False
    assert bs.login("ghost", "pw") is False


def test_create_budget_ids_and_unknown_owner(bs):
    assert bs.create_budget("ann", "a") == 1
    assert bs.create_budget("ben", "b") == 2
    with pytest.raises(KeyError):
        bs.create_budget("ghost", "c")


def test_invite_owner_only(bs, home):
    with pytest.raises(PermissionError):
        bs.invite("ben", home, "cleo", "editor")


def test_invite_validation(bs, home):
    with pytest.raises(ValueError):
        bs.invite("ann", home, "ben", "admin")
    with pytest.raises(KeyError):
        bs.invite("ann", home, "ghost", "viewer")
    with pytest.raises(ValueError):
        bs.invite("ann", home, "ben", "editor")


def test_invite_notifies_existing_members(bs):
    bid = bs.create_budget("ann", "trip")
    bs.invite("ann", bid, "ben", "editor")
    assert f"member_added:ben:{bid}" in bs.notifications("ann")
    assert f"member_added:ben:{bid}" not in bs.notifications("ben")
    bs.invite("ann", bid, "cleo", "viewer")
    assert f"member_added:cleo:{bid}" in bs.notifications("ben")


def test_amount_validation(bs, home):
    with pytest.raises(ValueError):
        bs.add_expense("ann", home, 0, "food")
    with pytest.raises(ValueError):
        bs.add_income("ann", home, -5, "salary")


def test_viewer_cannot_write(bs, home):
    with pytest.raises(PermissionError):
        bs.add_expense("cleo", home, 10, "food")


def test_nonmember_cannot_write_or_view(bs, home):
    outsider_budget = bs.create_budget("ben", "solo")
    with pytest.raises(PermissionError):
        bs.add_expense("cleo", outsider_budget, 10, "food")
    with pytest.raises(PermissionError):
        bs.dashboard("cleo", outsider_budget)


def test_dashboard_totals(bs, home):
    bs.add_income("ann", home, 3000, "salary")
    bs.add_income("ben", home, 1000, "salary")
    bs.add_expense("ann", home, 400, "food")
    bs.add_expense("ben", home, 250, "transport")
    bs.add_expense("ben", home, 100, "food")
    d = bs.dashboard("cleo", home)
    assert d["total_income"] == 4000
    assert d["total_expense"] == 750
    assert d["net"] == 3250
    assert d["by_category"] == {"food": 500, "transport": 250}


def test_set_limit_permissions(bs, home):
    bs.set_limit("ben", home, "food", 300)
    with pytest.raises(PermissionError):
        bs.set_limit("cleo", home, "food", 300)
    with pytest.raises(ValueError):
        bs.set_limit("ann", home, "food", 0)


def test_limit_exceeded_notifications(bs, home):
    bs.set_limit("ann", home, "food", 300)
    bs.add_expense("ben", home, 200, "food")
    assert not any(n.startswith("limit_exceeded:") for n in bs.notifications("cleo"))
    bs.add_expense("ben", home, 200, "food")
    msg = f"limit_exceeded:food:{home}"
    for u in ("ann", "ben", "cleo"):
        assert bs.notifications(u).count(msg) == 1
    bs.add_expense("ben", home, 50, "food")
    assert bs.notifications("cleo").count(msg) == 2


def test_suggestions_overshoot(bs, home):
    bs.set_limit("ann", home, "food", 300)
    bs.set_limit("ann", home, "fun", 100)
    bs.add_expense("ben", home, 450, "food")
    bs.add_expense("ben", home, 90, "fun")
    assert bs.suggestions(home) == {"food": 150}


def test_budget_isolation(bs, home):
    other = bs.create_budget("ann", "second")
    bs.add_income("ann", home, 100, "salary")
    bs.add_income("ann", other, 7, "salary")
    assert bs.dashboard("ann", other)["total_income"] == 7
    assert bs.dashboard("ann", home)["total_income"] == 100
    bs.set_limit("ann", other, "food", 5)
    bs.add_expense("ann", home, 50, "food")
    assert bs.suggestions(other) == {}


def test_notifications_unknown_user(bs):
    with pytest.raises(KeyError):
        bs.notifications("ghost")
