"""Sealed suite for gc-417 stage 1 (read-only). Defect ids A01..A04."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.getcwd(), "work", "gc-417", "pkgs"))

import proj_jsonl as pj  # noqa: E402


def test_parse_two_objects():
    assert pj.parse_lines('{"a": 1}\n{"b": 2}\n') == [{"a": 1}, {"b": 2}]


def test_parse_empty_text():
    assert pj.parse_lines("") == []


def test_parse_invalid_json_raises():
    with pytest.raises(ValueError):
        pj.parse_lines('{"a": 1}\nnot json\n')


def test_A01_blank_lines_skipped():
    assert pj.parse_lines('{"a": 1}\n\n   \n{"b": 2}\n') == [{"a": 1},
                                                            {"b": 2}]


def test_A02_non_object_line_raises():
    with pytest.raises(ValueError):
        pj.parse_lines("[1, 2]\n")
    with pytest.raises(ValueError):
        pj.parse_lines("42\n")


def test_filter_matches():
    recs = [{"k": 1}, {"k": 2}, {"k": 1}]
    assert pj.filter_records(recs, "k", 1) == [{"k": 1}, {"k": 1}]


def test_A03_filter_ignores_missing_key():
    recs = [{"k": 1}, {"other": 9}, {"k": 2}]
    assert pj.filter_records(recs, "k", 2) == [{"k": 2}]


def test_summarize_counts():
    recs = [{"k": "x"}, {"k": "y"}, {"nope": 1}]
    assert pj.summarize(recs, "k") == {"count": 3, "missing": 1,
                                       "distinct": 2}


def test_summarize_distinct_collapses_repeats():
    recs = [{"k": "x"}, {"k": "x"}, {"k": "x"}]
    assert pj.summarize(recs, "k")["distinct"] == 1


def test_A04_falsy_values_are_present():
    recs = [{"k": 0}, {"k": ""}, {"k": None}, {}]
    got = pj.summarize(recs, "k")
    assert got["count"] == 4
    assert got["missing"] == 1
    assert got["distinct"] == 3
