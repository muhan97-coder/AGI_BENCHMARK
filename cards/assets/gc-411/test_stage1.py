"""Sealed stage-1 acceptance suite for gc-411 (read-only)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.getcwd(), "work", "gc-411"))

import unitconv  # noqa: E402


def test_identity():
    assert unitconv.convert(7.25, "m", "m") == 7.25


def test_km_to_m():
    assert unitconv.convert(2.5, "km", "m") == 2500.0


def test_mi_to_ft_exact():
    assert unitconv.convert(1, "mi", "ft") == 5280.0


def test_ft_to_m():
    assert unitconv.convert(10, "ft", "m") == 3.048


def test_kg_to_lb_rounded():
    assert unitconv.convert(1, "kg", "lb") == round(1 / 0.45359237, 9)


def test_oz_to_lb_exact():
    assert unitconv.convert(16, "oz", "lb") == 1.0


def test_g_to_kg():
    assert unitconv.convert(250, "g", "kg") == 0.25


def test_h_to_s():
    assert unitconv.convert(1.5, "h", "s") == 5400.0


def test_min_to_h():
    assert unitconv.convert(45, "min", "h") == 0.75


def test_negative_value():
    assert unitconv.convert(-2, "km", "m") == -2000.0


def test_zero():
    assert unitconv.convert(0, "mi", "ft") == 0.0


def test_incompatible_dimensions():
    with pytest.raises(ValueError):
        unitconv.convert(1, "kg", "s")


def test_unknown_unit_keyerror():
    with pytest.raises(KeyError):
        unitconv.convert(1, "furlong", "m")


def test_dimension_of():
    assert unitconv.dimension_of("mi") == "length"
    assert unitconv.dimension_of("oz") == "mass"
    assert unitconv.dimension_of("min") == "time"


def test_dimension_of_unknown():
    with pytest.raises(KeyError):
        unitconv.dimension_of("nope")
