"""Sealed stage-1 acceptance suite for gc-416 (read-only)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.getcwd(), "work", "gc-416"))

import datex  # noqa: E402


def test_is_leap():
    assert datex.is_leap(2000) is True
    assert datex.is_leap(1900) is False
    assert datex.is_leap(2024) is True
    assert datex.is_leap(2026) is False


def test_days_in_month():
    assert datex.days_in_month(2024, 2) == 29
    assert datex.days_in_month(2025, 2) == 28
    assert datex.days_in_month(2026, 7) == 31
    assert datex.days_in_month(2026, 4) == 30


def test_days_in_month_bad_month():
    with pytest.raises(ValueError):
        datex.days_in_month(2026, 13)
    with pytest.raises(ValueError):
        datex.days_in_month(2026, 0)


def test_ordinal_epoch():
    assert datex.to_ordinal(1, 1, 1) == 1


def test_ordinal_anchors():
    assert datex.to_ordinal(2000, 1, 1) == 730120
    assert datex.to_ordinal(2026, 7, 31) == 739828
    assert datex.to_ordinal(9999, 12, 31) == 3652059


def test_from_ordinal_inverse():
    for triple in ((1, 1, 1), (2000, 1, 1), (2024, 2, 29), (2026, 7, 31),
                   (1900, 3, 1), (9999, 12, 31)):
        assert datex.from_ordinal(datex.to_ordinal(*triple)) == triple


def test_day_of_week_anchors():
    assert datex.day_of_week(1, 1, 1) == 0
    assert datex.day_of_week(2000, 1, 1) == 5
    assert datex.day_of_week(2026, 7, 31) == 4


def test_day_of_year():
    assert datex.day_of_year(2000, 1, 1) == 1
    assert datex.day_of_year(2000, 12, 31) == 366
    assert datex.day_of_year(1900, 3, 1) == 60
    assert datex.day_of_year(2024, 2, 29) == 60


def test_add_days_forward_across_year():
    assert datex.add_days(2025, 12, 30, 3) == (2026, 1, 2)


def test_add_days_backward_across_leap_feb():
    assert datex.add_days(2024, 3, 1, -1) == (2024, 2, 29)


def test_add_days_zero():
    assert datex.add_days(2026, 7, 31, 0) == (2026, 7, 31)


def test_add_days_large():
    assert datex.add_days(2000, 1, 1, 10000) == datex.from_ordinal(730120 + 10000)


def test_diff_days():
    assert datex.diff_days((2026, 7, 31), (2000, 1, 1)) == 739828 - 730120
    assert datex.diff_days((2000, 1, 1), (2026, 7, 31)) == 730120 - 739828


def test_invalid_dates_raise():
    for bad in ((2001, 2, 29), (2026, 13, 1), (2026, 0, 5), (2026, 4, 31),
                (0, 1, 1), (10000, 1, 1)):
        with pytest.raises(ValueError):
            datex.to_ordinal(*bad)


def test_from_ordinal_out_of_range():
    with pytest.raises(ValueError):
        datex.from_ordinal(0)
    with pytest.raises(ValueError):
        datex.from_ordinal(3652060)


def test_add_days_out_of_range_raises():
    with pytest.raises(ValueError):
        datex.add_days(9999, 12, 31, 1)
    with pytest.raises(ValueError):
        datex.add_days(1, 1, 1, -1)
