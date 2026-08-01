"""FAIL_TO_PASS for demoorg__tinycalc-101 (sealed: copied in by the harness)."""

from tinycalc import percent_change


def test_zero_baseline_returns_none():
    assert percent_change(0, 5) is None


def test_zero_baseline_with_zero_new_returns_none():
    assert percent_change(0, 0) is None
