"""Sealed stage-3 suite for gc-419 (read-only)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.getcwd(), "work", "gc-419"))

import logquery  # noqa: E402

RECORDS = [{"level": "info", "bytes": "100"},
           {"level": "warn", "bytes": "50"},
           {"level": "info", "bytes": "10"},
           {"level": "error", "bytes": "x"},
           {"other": 1},
           {"level": "info", "flag": True}]


def test_count_by_basic():
    assert logquery.count_by(RECORDS, "level") == {"info": 3, "warn": 1,
                                                  "error": 1}


def test_count_by_missing_key_excluded():
    assert logquery.count_by(RECORDS, "nope") == {}


def test_count_by_stringifies_values():
    assert logquery.count_by(RECORDS, "flag") == {"True": 1}


def test_stats_basic():
    got = logquery.stats(RECORDS, "bytes")
    assert got == {"count": 3, "mean": round(160 / 3, 6), "min": 10.0,
                   "max": 100.0}


def test_stats_skips_non_numeric():
    assert logquery.stats(RECORDS, "bytes")["count"] == 3


def test_stats_no_values_raises():
    with pytest.raises(ValueError):
        logquery.stats(RECORDS, "level")


def test_stats_rounding():
    recs = [{"v": "1"}, {"v": "2"}]
    assert logquery.stats(recs, "v")["mean"] == 1.5


def test_top_order():
    assert logquery.top(RECORDS, "level", 2) == [("info", 3), ("error", 1)]


def test_top_tie_breaks_alphabetically():
    recs = [{"k": "b"}, {"k": "a"}, {"k": "c"}, {"k": "a"}, {"k": "b"}]
    assert logquery.top(recs, "k", 3) == [("a", 2), ("b", 2), ("c", 1)]


def test_top_cutoff():
    assert len(logquery.top(RECORDS, "level", 1)) == 1
