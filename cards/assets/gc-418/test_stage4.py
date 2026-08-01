"""Sealed stage-4 error-identity suite for gc-418 (read-only).

Pins QueryError positions exactly. Failure identity, not just failure.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.getcwd(), "work", "gc-418"))

from querylang import QueryError, evaluate  # noqa: E402


def _err(expr, record=None):
    with pytest.raises(QueryError) as excinfo:
        evaluate(expr, record or {})
    return excinfo.value


def test_unterminated_string_pos():
    e = _err("name == 'bo")
    assert e.pos == 8
    assert "unterminated" in e.message


def test_bad_escape_pos():
    e = _err(r"'a\x'")
    assert e.pos == 2


def test_unexpected_character_pos():
    e = _err("age >$ 2", {"age": 1})
    assert e.pos == 5


def test_trailing_token_pos():
    e = _err("1 2")
    assert e.pos == 2


def test_unclosed_paren_pos_is_len():
    e = _err("(1")
    assert e.pos == 2


def test_ordering_null_pos_is_operator():
    e = _err("age < null", {"age": 5})
    assert e.pos == 4


def test_unknown_function_pos():
    e = _err("foo(1)")
    assert e.pos == 0


def test_arity_error_pos():
    e = _err("len('a', 'b')")
    assert e.pos == 0


def test_message_attribute_nonempty():
    e = _err("(1")
    assert isinstance(e.message, str) and e.message
    assert e.message in str(e)
