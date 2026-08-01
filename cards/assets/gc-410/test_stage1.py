"""Sealed stage-1 acceptance suite for gc-410 (read-only)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.getcwd(), "work", "gc-410"))

from iniread import parse  # noqa: E402


def test_simple_section():
    assert parse("[db]\nhost = local\nport = 5432\n") == {
        "db": {"host": "local", "port": "5432"}}


def test_top_level_keys_in_empty_section():
    assert parse("x = 1\n[a]\ny = 2\n") == {"": {"x": "1"}, "a": {"y": "2"}}


def test_no_empty_section_without_top_level_keys():
    assert "" not in parse("[a]\nx = 1\n")


def test_comments_and_blanks_ignored():
    assert parse("; c\n# c2\n\n[a]\nx = 1\n") == {"a": {"x": "1"}}


def test_split_on_first_equals():
    assert parse("[a]\nk = v = w\n") == {"a": {"k": "v = w"}}


def test_whitespace_stripped():
    assert parse("[ a ]\n  k  =  v  \n") == {"a": {"k": "v"}}


def test_duplicate_key_last_wins():
    assert parse("[a]\nk = 1\nk = 2\n") == {"a": {"k": "2"}}


def test_duplicate_section_merges():
    assert parse("[a]\nx = 1\n[b]\ny = 2\n[a]\nz = 3\n") == {
        "a": {"x": "1", "z": "3"}, "b": {"y": "2"}}


def test_empty_section_kept():
    assert parse("[empty]\n") == {"empty": {}}


def test_invalid_line_raises():
    with pytest.raises(ValueError):
        parse("[a]\nnot a pair\n")


def test_empty_key_raises():
    with pytest.raises(ValueError):
        parse("[a]\n= v\n")
