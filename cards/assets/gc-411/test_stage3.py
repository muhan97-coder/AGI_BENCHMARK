"""Sealed stage-3 acceptance suite for gc-411 (read-only)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.getcwd(), "work", "gc-411"))

import unitconv  # noqa: E402


def test_kmh_to_ms_exact():
    assert unitconv.convert_speed(90, "km/h", "m/s") == 25.0


def test_mph_to_fts_exact():
    assert unitconv.convert_speed(60, "mi/h", "ft/s") == 88.0


def test_identity_speed():
    assert unitconv.convert_speed(12.5, "m/s", "m/s") == 12.5


def test_ms_to_kmh():
    assert unitconv.convert_speed(10, "m/s", "km/h") == 36.0


def test_mph_to_ms():
    assert unitconv.convert_speed(1, "mi/h", "m/s") == 0.44704


def test_negative_speed():
    assert unitconv.convert_speed(-5, "km/h", "m/s") == round(-5 / 3.6, 9)


def test_no_slash_raises():
    with pytest.raises(ValueError):
        unitconv.convert_speed(1, "kmh", "m/s")


def test_two_slashes_raise():
    with pytest.raises(ValueError):
        unitconv.convert_speed(1, "km/h/s", "m/s")


def test_unknown_part_raises():
    with pytest.raises(ValueError):
        unitconv.convert_speed(1, "km/x", "m/s")


def test_wrong_dimension_parts_raise():
    with pytest.raises(ValueError):
        unitconv.convert_speed(1, "kg/h", "m/s")
    with pytest.raises(ValueError):
        unitconv.convert_speed(1, "km/m", "m/s")
