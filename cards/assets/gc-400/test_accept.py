"""Sealed acceptance suite for gc-400 (cronnext). Run from benchmark repo root."""
import importlib.util
import os

import pytest

_PATH = os.path.join(os.getcwd(), "workspace", "gc-400", "cronnext.py")
_spec = importlib.util.spec_from_file_location("cronnext_under_test", _PATH)
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)


def test_every_minute_strictly_after():
    assert M.next_fires("* * * * *", "2030-01-01T00:00", 3) == [
        "2030-01-01T00:01", "2030-01-01T00:02", "2030-01-01T00:03"]


def test_exact_minute_hour():
    assert M.next_fires("30 14 * * *", "2030-06-10T14:31", 2) == [
        "2030-06-11T14:30", "2030-06-12T14:30"]


def test_fire_equal_to_start_excluded():
    assert M.next_fires("0 0 * * *", "2030-01-01T00:00", 1) == ["2030-01-02T00:00"]


def test_minute_step_anchors_at_zero():
    assert M.next_fires("*/15 3 * * *", "2030-01-01T03:00", 3) == [
        "2030-01-01T03:15", "2030-01-01T03:30", "2030-01-01T03:45"]


def test_dom_step_anchors_at_one():
    assert M.next_fires("0 0 */10 * *", "2030-01-01T00:00", 4) == [
        "2030-01-11T00:00", "2030-01-21T00:00", "2030-01-31T00:00",
        "2030-02-01T00:00"]


def test_range_and_list():
    assert M.next_fires("0 9-11 * * *", "2030-01-01T08:59", 3) == [
        "2030-01-01T09:00", "2030-01-01T10:00", "2030-01-01T11:00"]
    assert M.next_fires("5,10 0 * * *", "2030-01-01T00:00", 2) == [
        "2030-01-01T00:05", "2030-01-01T00:10"]


def test_range_with_step():
    assert M.next_fires("10-40/15 0 * * *", "2030-01-01T00:00", 3) == [
        "2030-01-01T00:10", "2030-01-01T00:25", "2030-01-01T00:40"]


def test_dom_and_dow_or_semantics():
    # 2030-06-13 is a Thursday; fires on the 13th AND on every Friday.
    got = M.next_fires("0 0 13 * 5", "2030-06-12T00:00", 3)
    assert got == ["2030-06-13T00:00", "2030-06-14T00:00", "2030-06-21T00:00"]


def test_dom_only_no_dow_bleed():
    assert M.next_fires("0 0 13 * *", "2030-06-12T00:00", 2) == [
        "2030-06-13T00:00", "2030-07-13T00:00"]


def test_dow_only():
    # 2030-01-01 is a Tuesday; next Friday is Jan 4.
    assert M.next_fires("0 0 * * 5", "2030-01-01T00:00", 2) == [
        "2030-01-04T00:00", "2030-01-11T00:00"]


def test_step_dow_is_restricted():
    # dow */2 -> {0,2,4,6}; dom 15 restricted -> OR semantics.
    got = M.next_fires("0 0 15 * */2", "2030-01-13T12:00", 3)
    # 2030-01-13 is a Sunday. Next: Jan 14? Mon=1 no. Jan 14 no, Jan 15 (dom).
    assert got[0] == "2030-01-15T00:00"


def test_month_names_and_dow_names():
    assert M.next_fires("0 12 * MAR mon-FRI", "2030-02-27T00:00", 2) == [
        "2030-03-01T12:00", "2030-03-04T12:00"]  # Mar 1 2030 = Friday


def test_sunday_seven_equals_zero():
    a = M.next_fires("0 0 * * 7", "2030-01-01T00:00", 2)
    b = M.next_fires("0 0 * * 0", "2030-01-01T00:00", 2)
    assert a == b == ["2030-01-06T00:00", "2030-01-13T00:00"]  # Sundays


def test_dow_range_through_seven():
    # 5-7 = Fri, Sat, Sun
    got = M.next_fires("0 0 * * 5-7", "2030-01-01T00:00", 3)
    assert got == ["2030-01-04T00:00", "2030-01-05T00:00", "2030-01-06T00:00"]


def test_month_rollover():
    assert M.next_fires("0 0 1 * *", "2030-01-15T00:00", 2) == [
        "2030-02-01T00:00", "2030-03-01T00:00"]


def test_year_rollover():
    assert M.next_fires("30 23 31 12 *", "2030-12-31T23:31", 1) == [
        "2031-12-31T23:30"]


def test_feb_29_leap_only():
    assert M.next_fires("0 0 29 2 *", "2030-01-01T00:00", 1) == [
        "2032-02-29T00:00"]


def test_dom_31_skips_short_months():
    assert M.next_fires("0 0 31 * *", "2030-01-31T00:01", 3) == [
        "2030-03-31T00:00", "2030-05-31T00:00", "2030-07-31T00:00"]


def test_unsatisfiable_raises():
    with pytest.raises(ValueError):
        M.next_fires("0 0 31 4 *", "2030-01-01T00:00", 1)


def test_start_z_suffix_ok():
    assert M.next_fires("0 * * * *", "2030-01-01T05:59Z", 1) == ["2030-01-01T06:00"]


def test_invalid_expressions():
    for bad in ["* * * *", "* * * * * *", "60 * * * *", "* 24 * * *",
                "* * 0 * *", "* * 32 * *", "* * * 13 *", "* * * * 8",
                "5-1 * * * *", "*/0 * * * *", "* * * FOO *", "a * * * *",
                ", * * * *", "1- * * * *"]:
        assert M.is_valid(bad) is False, bad
        with pytest.raises(ValueError):
            M.next_fires(bad, "2030-01-01T00:00", 1)


def test_valid_expressions():
    for good in ["* * * * *", "*/1 * * * *", "0 0 1 1 0", "59 23 31 12 7",
                 "1,2,3 4-6 */2 JAN-MAR SUN", "0 12 * mAr Mon-fri"]:
        assert M.is_valid(good) is True, good


def test_bad_start_raises():
    for bad in ["2030-1-1T00:00", "2030-01-01 00:00", "2030-01-01T00:00:00",
                "garbage", ""]:
        with pytest.raises(ValueError):
            M.next_fires("* * * * *", bad, 1)


def test_bad_n_raises():
    for bad_n in [0, -1, "3"]:
        with pytest.raises(ValueError):
            M.next_fires("* * * * *", "2030-01-01T00:00", bad_n)
