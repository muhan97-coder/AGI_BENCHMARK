"""Sealed stage-3 suite for gc-418 (read-only)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.getcwd(), "work", "gc-418"))

from querylang import QueryError, evaluate  # noqa: E402


def test_len():
    assert evaluate("len('abc')", {}) == 3
    assert evaluate("len(name) == 3", {"name": "bob"}) is True


def test_lower_upper():
    assert evaluate("lower('AbC')", {}) == "abc"
    assert evaluate("upper(name)", {"name": "bob"}) == "BOB"


def test_abs_number():
    assert evaluate("abs(delta)", {"delta": -4}) == 4
    assert evaluate("abs(2.5)", {}) == 2.5


def test_contains():
    assert evaluate("contains(name, 'ob')", {"name": "bob"}) is True
    assert evaluate("contains(name, 'zz')", {"name": "bob"}) is False


def test_startswith():
    assert evaluate("startswith(name, 'bo')", {"name": "bob"}) is True
    assert evaluate("startswith(name, 'ob')", {"name": "bob"}) is False


def test_nested_calls():
    assert evaluate("len(lower(upper('abc')))", {}) == 3
    assert evaluate("contains(lower(name), 'ob')", {"name": "BOB"}) is True


def test_functions_in_logic():
    rec = {"name": "widget-pro", "qty": 3}
    assert evaluate("startswith(name, 'widget') and qty > 1", rec) is True


def test_unknown_function_raises():
    with pytest.raises(QueryError):
        evaluate("foo(1)", {})


def test_wrong_arity_raises():
    with pytest.raises(QueryError):
        evaluate("len('a', 'b')", {})
    with pytest.raises(QueryError):
        evaluate("contains('a')", {})


def test_bad_argument_type_raises():
    with pytest.raises(QueryError):
        evaluate("len(5)", {})
    with pytest.raises(QueryError):
        evaluate("abs('x')", {})
