"""Sealed stage-1 acceptance suite for gc-408 (read-only)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.getcwd(), "work", "gc-408"))

import csvprof  # noqa: E402


def _write(tmp_path, text, name="t.csv"):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return str(p)


def test_header_parsed(tmp_path):
    t = csvprof.read_table(_write(tmp_path, "a,b,c\n1,2,3\n"))
    assert t["header"] == ["a", "b", "c"]


def test_rows_parsed(tmp_path):
    t = csvprof.read_table(_write(tmp_path, "a,b\n1,2\n3,4\n"))
    assert t["rows"] == [["1", "2"], ["3", "4"]]


def test_short_rows_padded(tmp_path):
    t = csvprof.read_table(_write(tmp_path, "a,b,c\n1\n"))
    assert t["rows"] == [["1", "", ""]]


def test_long_rows_truncated(tmp_path):
    t = csvprof.read_table(_write(tmp_path, "a,b\n1,2,3,4\n"))
    assert t["rows"] == [["1", "2"]]


def test_quoted_comma_cell(tmp_path):
    t = csvprof.read_table(_write(tmp_path, 'a,b\n"x,y",2\n'))
    assert t["rows"] == [["x,y", "2"]]


def test_empty_file_raises(tmp_path):
    with pytest.raises(ValueError):
        csvprof.read_table(_write(tmp_path, ""))


def test_header_only(tmp_path):
    t = csvprof.read_table(_write(tmp_path, "a,b\n"))
    assert t["rows"] == []


def test_profile_row_count(tmp_path):
    t = csvprof.read_table(_write(tmp_path, "a,b\n1,2\n3,4\n5,6\n"))
    assert csvprof.profile(t)["row_count"] == 3


def test_profile_column_order(tmp_path):
    t = csvprof.read_table(_write(tmp_path, "z,a,m\n1,2,3\n"))
    assert [c["name"] for c in csvprof.profile(t)["columns"]] == ["z", "a", "m"]


def test_profile_non_empty_counts(tmp_path):
    t = csvprof.read_table(_write(tmp_path, "a,b\n1,\n,2\n3,4\n"))
    cols = {c["name"]: c["non_empty"] for c in csvprof.profile(t)["columns"]}
    assert cols == {"a": 2, "b": 2}


def test_profile_counts_padded_as_empty(tmp_path):
    t = csvprof.read_table(_write(tmp_path, "a,b,c\n1\n2,3\n"))
    cols = {c["name"]: c["non_empty"] for c in csvprof.profile(t)["columns"]}
    assert cols == {"a": 2, "b": 1, "c": 0}
