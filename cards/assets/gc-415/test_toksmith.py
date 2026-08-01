"""Sealed stage-1 suite for gc-415 (read-only)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.getcwd(), "work", "gc-415"))

from toksmith import tokenize  # noqa: E402


def test_empty():
    assert tokenize("") == []


def test_integer():
    assert tokenize("42") == [("NUMBER", 42, 0)]


def test_float():
    assert tokenize("3.14") == [("NUMBER", 3.14, 0)]


def test_word():
    assert tokenize("_hello9") == [("WORD", "_hello9", 0)]


def test_ops():
    assert tokenize("(a,b)") == [("OP", "(", 0), ("WORD", "a", 1),
                                 ("OP", ",", 2), ("WORD", "b", 3),
                                 ("OP", ")", 4)]


def test_string_plain():
    assert tokenize('"hi there"') == [("STRING", "hi there", 0)]


def test_string_escapes():
    assert tokenize(r'"a\"b\\c"') == [("STRING", 'a"b\\c', 0)]


def test_positions_with_whitespace():
    assert tokenize("  a\n b") == [("WORD", "a", 2), ("WORD", "b", 5)]


def test_maximal_munch_number_then_word():
    assert tokenize("12abc") == [("NUMBER", 12, 0), ("WORD", "abc", 2)]


def test_expression():
    assert tokenize("x = 1 + 2.5") == [
        ("WORD", "x", 0), ("OP", "=", 2), ("NUMBER", 1, 4),
        ("OP", "+", 6), ("NUMBER", 2.5, 8)]


def test_unterminated_string_raises():
    with pytest.raises(ValueError):
        tokenize('"abc')


def test_bad_escape_raises():
    with pytest.raises(ValueError):
        tokenize(r'"a\nb"')


def test_unexpected_char_raises():
    with pytest.raises(ValueError):
        tokenize("a @ b")
