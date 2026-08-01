"""FAIL_TO_PASS for demoorg__tinyunits-202 (sealed: copied in by the harness)."""

from tinyunits import convert


def test_mile_to_kilometre_uses_the_international_mile():
    assert abs(convert(1, "mi", "km") - 1.609344) < 1e-12


def test_mile_to_foot_is_5280():
    assert abs(convert(1, "mi", "ft") - 5280.0) < 1e-9
