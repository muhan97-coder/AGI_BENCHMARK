"""Sealed stage-2 suite for gc-418 (read-only)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.getcwd(), "work", "gc-418"))

from querylang import QueryError, evaluate  # noqa: E402


def test_and_or_not_basics():
    assert evaluate("true and false", {}) is False
    assert evaluate("true or false", {}) is True
    assert evaluate("not false", {}) is True


def test_precedence_and_binds_tighter_than_or():
    assert evaluate("true or false and false", {}) is True


def test_parens_override():
    assert evaluate("(true or false) and false", {}) is False


def test_not_applies_to_comparison():
    assert evaluate("not age == 1", {"age": 1}) is False
    assert evaluate("not age == 2", {"age": 1}) is True


def test_field_logic():
    rec = {"age": 30, "name": "bob"}
    assert evaluate("age > 18 and name == 'bob'", rec) is True
    assert evaluate("age > 40 or name == 'bob'", rec) is True
    assert evaluate("age > 40 and name == 'bob'", rec) is False


def test_chained_mixed():
    rec = {"a": 1, "b": 2, "c": 3}
    assert evaluate("a == 1 and b == 2 or c == 9", rec) is True
    assert evaluate("a == 9 and b == 2 or c == 3", rec) is True


def test_non_bool_and_operand_raises():
    with pytest.raises(QueryError):
        evaluate("1 and true", {})


def test_not_non_bool_raises():
    with pytest.raises(QueryError):
        evaluate("not 5", {})


def test_short_circuit_and_skips_right_error():
    assert evaluate("false and age < null", {"age": 1}) is False


def test_short_circuit_or_skips_right_error():
    assert evaluate("true or age < null", {"age": 1}) is True
