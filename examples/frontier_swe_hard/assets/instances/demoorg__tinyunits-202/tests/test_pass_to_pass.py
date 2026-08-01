"""PASS_TO_PASS for demoorg__tinyunits-202 (sealed: copied in by the harness)."""

import pytest

from tinyunits import convert, parse_quantity


def test_kilometre_to_metre():
    assert convert(1, "km", "m") == 1000.0


def test_inch_to_foot():
    assert abs(convert(12, "in", "ft") - 1.0) < 1e-12


def test_mile_round_trip_is_lossless():
    kilometres = convert(1, "mi", "km")
    assert abs(convert(kilometres, "km", "mi") - 1.0) < 1e-9


def test_unknown_unit_raises_value_error():
    with pytest.raises(ValueError):
        convert(1, "furlong", "m")


def test_parse_quantity():
    assert parse_quantity(" 3 km ") == (3.0, "km")
