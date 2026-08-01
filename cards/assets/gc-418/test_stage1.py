"""Sealed stage-1 suite for gc-418 (read-only)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.getcwd(), "work", "gc-418"))

from querylang import QueryError, evaluate  # noqa: E402


def test_int_literal():
    assert evaluate("42", {}) == 42


def test_float_literal():
    assert evaluate("3.5", {}) == 3.5


def test_string_literal_with_escapes():
    assert evaluate(r"'it\'s ok\\'", {}) == "it's ok\\"


def test_keyword_literals():
    assert evaluate("true", {}) is True
    assert evaluate("false", {}) is False
    assert evaluate("null", {}) is None


def test_field_lookup():
    assert evaluate("age", {"age": 30}) == 30


def test_missing_field_is_null():
    assert evaluate("ghost", {"age": 30}) is None
    assert evaluate("ghost == null", {"age": 30}) is True


def test_numeric_comparisons():
    rec = {"age": 25}
    assert evaluate("age >= 21", rec) is True
    assert evaluate("age < 21", rec) is False
    assert evaluate("age != 21", rec) is True
    assert evaluate("age == 25", rec) is True


def test_int_float_mix():
    assert evaluate("price < 2.5", {"price": 2}) is True


def test_string_comparison():
    assert evaluate("name < 'm'", {"name": "alice"}) is True
    assert evaluate("name > 'm'", {"name": "zed"}) is True


def test_cross_type_equality_is_false():
    assert evaluate("age == 'x'", {"age": 1}) is False
    assert evaluate("age != 'x'", {"age": 1}) is True


def test_ordering_null_raises():
    with pytest.raises(QueryError):
        evaluate("age < null", {"age": 5})


def test_ordering_bool_raises():
    with pytest.raises(QueryError):
        evaluate("flag < 5", {"flag": True})


def test_trailing_tokens_raise():
    with pytest.raises(QueryError):
        evaluate("1 2", {})


def test_unexpected_character_raises():
    with pytest.raises(QueryError):
        evaluate("age $ 1", {"age": 1})
