"""Sealed stage-1 regression suite for gc-409 (read-only).

Test names carry the seeded-defect identities B01..B04.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.getcwd(), "work", "gc-409"))

from globlite import match  # noqa: E402


def test_literal_exact():
    assert match("abc", "abc") is True


def test_literal_mismatch():
    assert match("abc", "abd") is False


def test_star_spans_middle():
    assert match("a*c", "abbbc") is True


def test_qmark_single_char():
    assert match("a?c", "abc") is True


def test_class_member():
    assert match("[abc]x", "ax") is True


def test_class_nonmember():
    assert match("[abc]x", "dx") is False


def test_mixed_pattern():
    assert match("d*.[ch]", "data.c") is True


def test_case_sensitive():
    assert match("A", "a") is False


def test_B01_qmark_requires_one_char():
    assert match("?", "") is False
    assert match("a?", "a") is False


def test_B02_negated_class():
    assert match("[!abc]", "d") is True
    assert match("[!abc]", "a") is False


def test_B03_star_matches_empty_run():
    assert match("a*", "a") is True
    assert match("a*b", "ab") is True


def test_B04_unclosed_bracket_is_literal():
    assert match("a[b", "a[b") is True
    assert match("[", "[") is True
