"""PASS_TO_PASS for demoorg__tinycalc-101 (sealed: copied in by the harness)."""

from tinycalc import mean, percent_change


def test_increase():
    assert percent_change(100, 150) == 50.0


def test_decrease():
    assert percent_change(50, 25) == -50.0


def test_negative_baseline():
    assert percent_change(-100, -50) == -50.0


def test_mean_of_empty_series_is_none():
    assert mean([]) is None


def test_mean_of_values():
    assert mean([1, 2, 3]) == 2
