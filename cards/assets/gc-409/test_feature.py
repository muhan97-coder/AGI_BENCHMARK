"""Sealed stage-2 feature suite for gc-409 (read-only)."""
import os
import sys

sys.path.insert(0, os.path.join(os.getcwd(), "work", "gc-409"))

from globlite import expand_braces, match  # noqa: E402


def test_expand_basic():
    assert expand_braces("a{b,c}d") == ["abd", "acd"]


def test_expand_no_comma_is_literal():
    assert expand_braces("a{bc}d") == ["a{bc}d"]


def test_expand_unmatched_brace_literal():
    assert expand_braces("a{b,c") == ["a{b,c"]


def test_expand_empty_alternative():
    assert expand_braces("a{,b}") == ["a", "ab"]


def test_expand_two_groups_cartesian():
    assert expand_braces("{a,b}{1,2}") == ["a1", "a2", "b1", "b2"]


def test_expand_dedupes_preserving_order():
    assert expand_braces("x{a,a}y") == ["xay"]


def test_match_uses_expansion():
    assert match("*.{py,txt}", "notes.txt") is True
    assert match("*.{py,txt}", "notes.md") is False


def test_match_literal_braces_still_work():
    assert match("{x}", "{x}") is True
