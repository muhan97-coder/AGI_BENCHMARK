"""Sealed acceptance suite for gc-335 (MARBLE coding task_id=53: MultiTrackRacers).

Loads the agent's solution from workspace/gc-335/solution.py relative to the
benchmark repo root. Graders run the pinned copy of this file; do not modify it.
"""
import importlib.util
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_SOLUTION = _ROOT / "workspace" / "gc-335" / "solution.py"


def _load():
    spec = importlib.util.spec_from_file_location("solution_gc335", _SOLUTION)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def mod():
    return _load()


def _track(mod, segments, name="t"):
    t = mod.Track(name)
    for kind, length in segments:
        t.add_segment(kind, length)
    t.finalize()
    return t


def test_track_segment_validation(mod):
    t = mod.Track("t")
    with pytest.raises(ValueError):
        t.add_segment("loop", 5)
    with pytest.raises(ValueError):
        t.add_segment("straight", 0)


def test_track_finalize_min_length(mod):
    t = mod.Track("t")
    t.add_segment("straight", 4)
    with pytest.raises(ValueError):
        t.finalize()
    assert t.finalized is False
    t.add_segment("curve", 6)
    t.finalize()
    assert t.finalized is True
    assert t.length == 10
    assert [tuple(s) for s in t.segments] == [("straight", 4), ("curve", 6)]


def test_track_frozen_after_finalize(mod):
    t = _track(mod, [("straight", 10)])
    with pytest.raises(RuntimeError):
        t.add_segment("straight", 5)


def test_vehicle_budget_cap(mod):
    mod.Vehicle("ok", 4, 4, 4)
    with pytest.raises(ValueError):
        mod.Vehicle("fat", 5, 4, 4)
    with pytest.raises(ValueError):
        mod.Vehicle("zero", 0, 6, 6)


def test_vehicle_upgrade_rules(mod):
    v = mod.Vehicle("v", 4, 3, 3)
    v.upgrade("speed", 2)
    assert v.speed == 6
    with pytest.raises(ValueError):
        v.upgrade("speed", 1)  # sum would be 13
    assert v.speed == 6
    with pytest.raises(ValueError):
        v.upgrade("luck", 1)
    with pytest.raises(ValueError):
        v.upgrade("speed", 0)


def test_vehicle_single_ability(mod):
    v = mod.Vehicle("v", 4, 4, 4)
    assert v.ability is None
    v.add_ability("boost")
    assert v.ability == "boost"
    with pytest.raises(RuntimeError):
        v.add_ability("shield")
    with pytest.raises(ValueError):
        mod.Vehicle("w", 4, 4, 4).add_ability("wings")


def test_time_straight(mod):
    t = _track(mod, [("straight", 12)])
    v = mod.Vehicle("v", 4, 4, 4)
    res = mod.race(t, [v])
    assert res[0]["time"] == pytest.approx(3.0, abs=1e-9)


def test_time_curve_formula(mod):
    t = _track(mod, [("curve", 10)])
    v = mod.Vehicle("v", 5, 1, 6)
    # 10 / (5 * (0.5 + 6/20)) = 10 / 4.0 = 2.5
    res = mod.race(t, [v])
    assert res[0]["time"] == pytest.approx(2.5, abs=1e-9)


def test_time_jump_formula(mod):
    t = _track(mod, [("jump", 10)])
    v = mod.Vehicle("v", 5, 3, 4)
    # 10/5 + 3/3 = 3.0
    res = mod.race(t, [v])
    assert res[0]["time"] == pytest.approx(3.0, abs=1e-9)


def test_time_obstacle_and_shield(mod):
    t = _track(mod, [("obstacle", 10)])
    plain = mod.Vehicle("plain", 5, 2, 5)
    shielded = mod.Vehicle("shielded", 5, 2, 5)
    shielded.add_ability("shield")
    res = {r["name"]: r["time"] for r in mod.race(t, [plain, shielded])}
    assert res["plain"] == pytest.approx(2.0 + 1.0, abs=1e-9)   # 10/5 + 5/5
    assert res["shielded"] == pytest.approx(2.0, abs=1e-9)


def test_boost_reduces_total(mod):
    t = _track(mod, [("straight", 12)])
    v = mod.Vehicle("v", 4, 4, 4)
    v.add_ability("boost")
    res = mod.race(t, [v])
    assert res[0]["time"] == pytest.approx(2.7, abs=1e-9)


def test_race_sorting_and_ties(mod):
    t = _track(mod, [("straight", 12)])
    fast = mod.Vehicle("fast", 6, 3, 3)
    zed = mod.Vehicle("zed", 4, 4, 4)
    alf = mod.Vehicle("alf", 4, 5, 3)  # same speed as zed -> tie, name order
    res = mod.race(t, [zed, fast, alf])
    assert [r["name"] for r in res] == ["fast", "alf", "zed"]


def test_race_requires_finalized_and_vehicles(mod):
    t = mod.Track("open")
    t.add_segment("straight", 12)
    v = mod.Vehicle("v", 4, 4, 4)
    with pytest.raises(RuntimeError):
        mod.race(t, [v])
    t.finalize()
    with pytest.raises(ValueError):
        mod.race(t, [])


def test_mixed_track_total(mod):
    t = _track(mod, [("straight", 6), ("curve", 8), ("jump", 5), ("obstacle", 4)])
    v = mod.Vehicle("v", 4, 4, 4)
    # 6/4 + 8/(4*0.7) + (5/4 + 3/4) + (4/4 + 5/4)
    expected = 1.5 + 8 / 2.8 + 2.0 + 2.25
    res = mod.race(t, [v])
    assert res[0]["time"] == pytest.approx(round(expected, 6), abs=1e-6)


def test_league_points_and_standings(mod):
    t = _track(mod, [("straight", 12)])
    a = mod.Vehicle("a", 6, 3, 3)
    b = mod.Vehicle("b", 5, 4, 3)
    c = mod.Vehicle("c", 4, 4, 4)
    d = mod.Vehicle("d", 3, 5, 4)
    league = mod.League()
    league.record(mod.race(t, [a, b, c, d]))  # a=3, b=2, c=1, d=0
    league.record(mod.race(t, [a, b, c, d]))  # a=6, b=4, c=2, d=0
    st = [tuple(s) for s in league.standings()]
    assert st == [("a", 6), ("b", 4), ("c", 2), ("d", 0)]


def test_league_short_field_and_tie_order(mod):
    t = _track(mod, [("straight", 12)])
    a = mod.Vehicle("a", 6, 3, 3)
    b = mod.Vehicle("b", 6, 3, 3)
    league = mod.League()
    league.record(mod.race(t, [b, a]))  # tie on time -> a first: a=3, b=2
    st = [tuple(s) for s in league.standings()]
    assert st == [("a", 3), ("b", 2)]


def test_track_sharing(mod):
    league = mod.League()
    t1 = _track(mod, [("straight", 12)], name="alpha")
    t2 = _track(mod, [("curve", 15)], name="beta")
    league.share_track("agent1", t1)
    league.share_track("agent2", t2)
    assert [tuple(s) for s in league.shared_tracks()] == [
        ("agent1", "alpha"), ("agent2", "beta")]
