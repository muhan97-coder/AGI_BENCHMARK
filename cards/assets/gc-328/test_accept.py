"""Sealed acceptance suite for gc-328 (MARBLE coding task_id=4: PriceTrackerCollaborator).

Loads the agent's solution from workspace/gc-328/solution.py relative to the
benchmark repo root. Graders run the pinned copy of this file; do not modify it.
"""
import importlib.util
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_SOLUTION = _ROOT / "workspace" / "gc-328" / "solution.py"


def _load():
    spec = importlib.util.spec_from_file_location("solution_gc328", _SOLUTION)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def pt():
    p = _load().PriceTracker()
    for u in ("uma", "vic", "wes"):
        p.register(u)
    return p


@pytest.fixture()
def cam(pt):
    return pt.add_product("uma", "camera", "https://shop.example/cam")


def test_register_duplicate(pt):
    with pytest.raises(ValueError):
        pt.register("uma")


def test_product_ids_and_url_validation(pt):
    assert pt.add_product("uma", "a", "http://x.example/a") == 1
    assert pt.add_product("vic", "b", "https://x.example/b") == 2
    with pytest.raises(ValueError):
        pt.add_product("uma", "c", "ftp://x.example/c")
    with pytest.raises(KeyError):
        pt.add_product("ghost", "d", "https://x.example/d")


def test_set_alert_validation(pt, cam):
    with pytest.raises(ValueError):
        pt.set_alert("uma", cam, 0)
    with pytest.raises(KeyError):
        pt.set_alert("uma", 999, 50)


def test_record_price_validation(pt, cam):
    with pytest.raises(ValueError):
        pt.record_price(cam, "shopA", -1, 1)
    with pytest.raises(KeyError):
        pt.record_price(999, "shopA", 10, 1)


def test_history_order(pt, cam):
    pt.record_price(cam, "shopA", 100, 1)
    pt.record_price(cam, "shopA", 90, 3)
    pt.record_price(cam, "shopB", 95, 2)
    assert [list(h) for h in pt.history(cam, "shopA")] == [[1, 100], [3, 90]]
    assert [list(h) for h in pt.history(cam, "shopB")] == [[2, 95]]


def test_latest_prices_by_ts(pt, cam):
    pt.record_price(cam, "shopA", 100, 5)
    pt.record_price(cam, "shopA", 80, 2)
    pt.record_price(cam, "shopB", 90, 9)
    assert pt.latest_prices(cam) == {"shopA": 100, "shopB": 90}


def test_best_offer_and_tie(pt, cam):
    pt.record_price(cam, "shopB", 90, 1)
    pt.record_price(cam, "shopA", 90, 2)
    pt.record_price(cam, "shopC", 95, 3)
    assert tuple(pt.best_offer(cam)) == ("shopA", 90)


def test_best_offer_empty(pt, cam):
    with pytest.raises(RuntimeError):
        pt.best_offer(cam)


def test_price_drop_notification_once_per_event(pt, cam):
    pt.set_alert("uma", cam, 95)
    pt.set_alert("uma", cam, 120)
    pt.record_price(cam, "shopA", 90, 1)
    assert pt.notifications("uma") == [f"price_drop:{cam}:shopA:90"]
    pt.record_price(cam, "shopA", 99, 2)  # below 120 only
    assert pt.notifications("uma") == [
        f"price_drop:{cam}:shopA:90", f"price_drop:{cam}:shopA:99"]
    pt.record_price(cam, "shopA", 130, 3)  # above all thresholds
    assert len(pt.notifications("uma")) == 2
    assert pt.notifications("vic") == []


def test_trend_stats(pt, cam):
    for retailer, price, ts in [("shopA", 100, 1), ("shopA", 80, 2), ("shopB", 120, 3)]:
        pt.record_price(cam, retailer, price, ts)
    t = pt.trend(cam)
    assert t["min"] == 80 and t["max"] == 120
    assert abs(t["avg"] - 100.0) < 1e-9
    with pytest.raises(RuntimeError):
        pt.trend(pt.add_product("uma", "empty", "https://x.example/e"))


def test_good_buy(pt, cam):
    pt.record_price(cam, "shopA", 100, 1)
    pt.record_price(cam, "shopA", 140, 2)
    assert pt.good_buy(cam) is False  # best current 140 > avg 120
    pt.record_price(cam, "shopB", 100, 3)
    assert pt.good_buy(cam) is True  # best current 100 <= avg ~113.33


def test_groups_membership(pt):
    pt.create_group("deals")
    with pytest.raises(ValueError):
        pt.create_group("deals")
    with pytest.raises(KeyError):
        pt.join_group("uma", "ghost-group")
    with pytest.raises(KeyError):
        pt.join_group("ghost", "deals")


def test_share_alert_requires_membership(pt, cam):
    pt.create_group("deals")
    pt.join_group("vic", "deals")
    with pytest.raises(PermissionError):
        pt.share_alert("uma", "deals", cam)


def test_share_alert_copies_thresholds(pt, cam):
    pt.create_group("deals")
    for u in ("uma", "vic", "wes"):
        pt.join_group(u, "deals")
    pt.set_alert("uma", cam, 95)
    pt.share_alert("uma", "deals", cam)
    assert f"shared_alert:{cam}:uma" in pt.notifications("vic")
    assert f"shared_alert:{cam}:uma" in pt.notifications("wes")
    assert f"shared_alert:{cam}:uma" not in pt.notifications("uma")
    pt.record_price(cam, "shopA", 90, 1)
    for u in ("uma", "vic", "wes"):
        assert f"price_drop:{cam}:shopA:90" in pt.notifications(u)


def test_notifications_unknown_user(pt):
    with pytest.raises(KeyError):
        pt.notifications("ghost")
