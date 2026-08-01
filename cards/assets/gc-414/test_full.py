"""Sealed stage-2 acceptance suite for gc-414 (read-only)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.getcwd(), "work", "gc-414"))

import romanx_full as rf  # noqa: E402


def test_to_roman_basics():
    assert rf.to_roman(1) == "I"
    assert rf.to_roman(14) == "XIV"
    assert rf.to_roman(1987) == "MCMLXXXVII"
    assert rf.to_roman(3999) == "MMMCMXCIX"


def test_to_roman_subtractive_forms():
    assert rf.to_roman(4) == "IV"
    assert rf.to_roman(9) == "IX"
    assert rf.to_roman(40) == "XL"
    assert rf.to_roman(90) == "XC"
    assert rf.to_roman(400) == "CD"
    assert rf.to_roman(900) == "CM"


def test_to_roman_out_of_range():
    for bad in (0, -1, 4000):
        with pytest.raises(ValueError):
            rf.to_roman(bad)


def test_to_roman_rejects_bool_and_nonint():
    with pytest.raises(ValueError):
        rf.to_roman(True)
    with pytest.raises(ValueError):
        rf.to_roman("7")


def test_from_roman_round_trip():
    for n in (1, 4, 9, 42, 90, 444, 999, 1666, 2026, 3999):
        assert rf.from_roman(rf.to_roman(n)) == n


def test_from_roman_strict_rejects_noncanonical():
    for bad in ("IIII", "VX", "IC", "XM", "IL"):
        with pytest.raises(ValueError):
            rf.from_roman(bad)


def test_from_roman_rejects_empty_and_lowercase():
    with pytest.raises(ValueError):
        rf.from_roman("")
    with pytest.raises(ValueError):
        rf.from_roman("xiv")


def test_is_valid():
    assert rf.is_valid("XIV") is True
    assert rf.is_valid("MMMCMXCIX") is True
    assert rf.is_valid("IIII") is False
    assert rf.is_valid("") is False
    assert rf.is_valid("hello") is False


def test_roman_range_basic():
    assert list(rf.roman_range(1, 4)) == ["I", "II", "III"]


def test_roman_range_step():
    assert list(rf.roman_range(10, 41, 10)) == ["X", "XX", "XXX", "XL"]


def test_roman_range_negative_step():
    assert list(rf.roman_range(3, 0, -1)) == ["III", "II", "I"]


def test_roman_range_empty():
    assert list(rf.roman_range(5, 5)) == []


def test_roman_range_zero_step_raises_eagerly():
    with pytest.raises(ValueError):
        rf.roman_range(1, 10, 0)


def test_roman_range_out_of_range_raises_eagerly():
    with pytest.raises(ValueError):
        rf.roman_range(0, 3)
    with pytest.raises(ValueError):
        rf.roman_range(3998, 4001)
