"""Sealed acceptance suite for gc-326 (MARBLE coding task_id=51: MealMaster).

Loads the agent's solution from workspace/gc-326/solution.py relative to the
benchmark repo root. Graders run the pinned copy of this file; do not modify it.
"""
import importlib.util
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_SOLUTION = _ROOT / "workspace" / "gc-326" / "solution.py"


def _load():
    spec = importlib.util.spec_from_file_location("solution_gc326", _SOLUTION)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _r(name, meal_type, cal, tags, allergens, protein=10, carbs=30, fat=8, fiber=4):
    return {"name": name, "meal_type": meal_type, "tags": list(tags),
            "allergens": list(allergens), "calories": cal, "protein": protein,
            "carbs": carbs, "fat": fat, "fiber": fiber,
            "ingredients": ["ing1", "ing2"], "instructions": "mix and serve"}


RECIPES = [
    _r("oat_bowl", "breakfast", 400, ["vegan", "gluten_free"], ["oats"]),
    _r("nut_granola", "breakfast", 450, ["vegan"], ["nuts"]),
    _r("egg_toast", "breakfast", 500, ["vegetarian"], ["eggs", "gluten"]),
    _r("quinoa_salad", "lunch", 600, ["vegan", "gluten_free"], []),
    _r("rice_bowl", "lunch", 550, ["vegan", "gluten_free"], []),
    _r("peanut_noodles", "lunch", 650, ["vegan"], ["peanuts"]),
    _r("veg_curry", "dinner", 700, ["vegan", "gluten_free"], []),
    _r("cheese_pizza", "dinner", 900, ["vegetarian"], ["gluten", "dairy"]),
    _r("fruit_cup", "snack", 200, ["vegan", "gluten_free"], []),
    _r("trail_mix", "snack", 300, ["vegan"], ["nuts"]),
]

BY_NAME = {r["name"]: r for r in RECIPES}


@pytest.fixture()
def mm():
    m = _load().MealMaster([dict(r) for r in RECIPES])
    m.set_profile("vera", preferences=["vegan"], allergies=["nuts", "peanuts"],
                  goal="maintenance", daily_calories=2000)
    return m


def test_invalid_meal_type_rejected():
    mod = _load()
    bad = [_r("mystery", "brunch", 400, ["vegan"], [])]
    with pytest.raises(ValueError):
        mod.MealMaster(bad)


def test_invalid_goal_rejected(mm):
    with pytest.raises(ValueError):
        mm.set_profile("x", [], [], "bulk", 2000)


def test_nonpositive_calories_rejected(mm):
    with pytest.raises(ValueError):
        mm.set_profile("x", [], [], "maintenance", 0)


def test_candidates_filters_preferences(mm):
    assert mm.candidates("vera", "dinner") == ["veg_curry"]


def test_candidates_excludes_allergens(mm):
    assert "nut_granola" not in mm.candidates("vera", "breakfast")
    assert "peanut_noodles" not in mm.candidates("vera", "lunch")


def test_candidates_unknown_user(mm):
    with pytest.raises(KeyError):
        mm.candidates("ghost", "lunch")


def test_plan_structure(mm):
    plan = mm.generate_week_plan("vera")
    assert sorted(plan.keys()) == [f"day{i}" for i in range(1, 8)]
    for day in plan.values():
        assert set(day.keys()) == {"breakfast", "lunch", "dinner", "snack"}


def test_plan_respects_constraints(mm):
    plan = mm.generate_week_plan("vera")
    for day in plan.values():
        for slot, name in day.items():
            r = BY_NAME[name]
            assert r["meal_type"] == slot
            assert "vegan" in r["tags"]
            assert not set(r["allergens"]) & {"nuts", "peanuts"}


def test_plan_calories_within_tolerance(mm):
    plan = mm.generate_week_plan("vera", tolerance=0.2)
    for day in plan.values():
        total = sum(BY_NAME[n]["calories"] for n in day.values())
        assert 1600 <= total <= 2400


def test_infeasible_plan_raises(mm):
    mm.set_profile("noel", preferences=["vegan"],
                   allergies=["oats", "nuts", "peanuts"],
                   goal="weight_loss", daily_calories=1800)
    with pytest.raises(RuntimeError):
        mm.generate_week_plan("noel")


def test_day_nutrition_sums(mm):
    plan = mm.generate_week_plan("vera")
    nut = mm.day_nutrition("vera", "day1")
    expect = {k: sum(BY_NAME[n][k] for n in plan["day1"].values())
              for k in ("calories", "protein", "carbs", "fat", "fiber")}
    assert nut == expect


def test_day_nutrition_requires_plan(mm):
    mm.set_profile("pat", [], [], "maintenance", 2000)
    with pytest.raises(RuntimeError):
        mm.day_nutrition("pat", "day1")


def test_swap_rejects_allergen(mm):
    mm.generate_week_plan("vera")
    with pytest.raises(ValueError):
        mm.swap("vera", "day1", "lunch", "peanut_noodles")


def test_swap_rejects_wrong_slot_and_unknown(mm):
    mm.generate_week_plan("vera")
    with pytest.raises(ValueError):
        mm.swap("vera", "day1", "lunch", "veg_curry")
    with pytest.raises(KeyError):
        mm.swap("vera", "day1", "lunch", "unicorn_stew")


def test_swap_valid_updates_plan(mm):
    plan = mm.generate_week_plan("vera")
    current = plan["day2"]["lunch"]
    other = "rice_bowl" if current != "rice_bowl" else "quinoa_salad"
    mm.swap("vera", "day2", "lunch", other)
    nut = mm.day_nutrition("vera", "day2")
    names = [v for k, v in plan["day2"].items() if k != "lunch"] + [other]
    assert nut["calories"] == sum(BY_NAME[n]["calories"] for n in names)
