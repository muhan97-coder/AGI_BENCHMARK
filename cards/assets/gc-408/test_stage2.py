"""Sealed stage-2 acceptance suite for gc-408 (read-only)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.getcwd(), "work", "gc-408"))

import csvprof  # noqa: E402


def _table(tmp_path, text):
    p = tmp_path / "t.csv"
    p.write_text(text, encoding="utf-8")
    return csvprof.read_table(str(p))


def test_numeric_true(tmp_path):
    t = _table(tmp_path, "a,b\n1,x\n2.5,y\n")
    assert csvprof.is_numeric_column(t, "a") is True


def test_numeric_false_for_text(tmp_path):
    t = _table(tmp_path, "a,b\n1,x\n2,y\n")
    assert csvprof.is_numeric_column(t, "b") is False


def test_numeric_ignores_empty_cells(tmp_path):
    t = _table(tmp_path, "a\n1\n\n3\n")
    assert csvprof.is_numeric_column(t, "a") is True


def test_all_empty_column_not_numeric(tmp_path):
    t = _table(tmp_path, "a,b\n,1\n,2\n")
    assert csvprof.is_numeric_column(t, "a") is False


def test_unknown_column_keyerror(tmp_path):
    t = _table(tmp_path, "a\n1\n")
    with pytest.raises(KeyError):
        csvprof.is_numeric_column(t, "nope")


def test_scientific_notation_is_numeric(tmp_path):
    t = _table(tmp_path, "a\n1e3\n-2.5E-2\n")
    assert csvprof.is_numeric_column(t, "a") is True


def test_stats_basic(tmp_path):
    t = _table(tmp_path, "a\n1\n2\n3\n")
    assert csvprof.numeric_stats(t, "a") == {"mean": 2.0, "min": 1.0,
                                             "max": 3.0}


def test_stats_rounding(tmp_path):
    t = _table(tmp_path, "a\n1\n2\n")
    s = csvprof.numeric_stats(t, "a")
    assert s["mean"] == 1.5


def test_stats_skips_empty(tmp_path):
    t = _table(tmp_path, "a\n10\n\n20\n")
    assert csvprof.numeric_stats(t, "a")["mean"] == 15.0


def test_stats_third_mean_rounded(tmp_path):
    t = _table(tmp_path, "a\n1\n1\n0\n")
    assert csvprof.numeric_stats(t, "a")["mean"] == round(2 / 3, 6)


def test_stats_on_text_column_valueerror(tmp_path):
    t = _table(tmp_path, "a\nx\ny\n")
    with pytest.raises(ValueError):
        csvprof.numeric_stats(t, "a")


def test_stats_unknown_column_keyerror(tmp_path):
    t = _table(tmp_path, "a\n1\n")
    with pytest.raises(KeyError):
        csvprof.numeric_stats(t, "missing")
