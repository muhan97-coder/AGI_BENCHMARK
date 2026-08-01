"""Sealed stage-3 recurrence suite for gc-416 (read-only)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.getcwd(), "work", "gc-416"))

import datex  # noqa: E402


def test_next_weekday_basic():
    # 2026-07-31 is a Friday (4); next Monday (0) is 2026-08-03
    assert datex.next_weekday(2026, 7, 31, 0) == (2026, 8, 3)


def test_next_weekday_same_day_goes_forward_a_week():
    assert datex.next_weekday(2026, 7, 31, 4) == (2026, 8, 7)


def test_next_weekday_across_year():
    # 2025-12-31 is a Wednesday (2); next Thursday is 2026-01-01
    assert datex.next_weekday(2025, 12, 31, 3) == (2026, 1, 1)


def test_next_weekday_bad_target():
    with pytest.raises(ValueError):
        datex.next_weekday(2026, 7, 31, 7)
    with pytest.raises(ValueError):
        datex.next_weekday(2026, 7, 31, -1)


def test_nth_weekday_first():
    # first Monday of 2026-07 is 2026-07-06
    assert datex.nth_weekday_of_month(2026, 7, 0, 1) == (2026, 7, 6)


def test_nth_weekday_third():
    # third Friday of 2026-07 is 2026-07-17
    assert datex.nth_weekday_of_month(2026, 7, 4, 3) == (2026, 7, 17)


def test_nth_weekday_last():
    # last Friday of 2026-07 is 2026-07-31
    assert datex.nth_weekday_of_month(2026, 7, 4, -1) == (2026, 7, 31)


def test_nth_weekday_last_february_leap():
    # last day of 2024-02 is thursday 2024-02-29; last Thursday is the 29th
    assert datex.nth_weekday_of_month(2024, 2, 3, -1) == (2024, 2, 29)


def test_nth_weekday_missing_fifth_raises():
    with pytest.raises(ValueError):
        datex.nth_weekday_of_month(2026, 7, 0, 5)


def test_nth_weekday_bad_n_raises():
    with pytest.raises(ValueError):
        datex.nth_weekday_of_month(2026, 7, 0, 0)
    with pytest.raises(ValueError):
        datex.nth_weekday_of_month(2026, 7, 0, -2)
