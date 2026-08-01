"""Sealed suite for gc-417 stage 3 (read-only). Defect ids T01..T04."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.getcwd(), "work", "gc-417", "pkgs"))

import proj_tmpl as pt  # noqa: E402


def test_plain_text():
    assert pt.render("hello world", {}) == "hello world"


def test_simple_placeholder():
    assert pt.render("hi {name}", {"name": "sam"}) == "hi sam"


def test_multiple_placeholders():
    assert pt.render("{a}-{b}-{a}", {"a": "x", "b": "y"}) == "x-y-x"


def test_missing_key_raises_keyerror():
    with pytest.raises(KeyError):
        pt.render("{nope}", {"a": 1})


def test_T01_brace_escapes():
    assert pt.render("{{literal}}", {}) == "{literal}"
    assert pt.render("a{{b}}c {x}", {"x": "y"}) == "a{b}c y"


def test_T02_dotted_access():
    ctx = {"user": {"name": "kim", "addr": {"city": "oslo"}}}
    assert pt.render("{user.name} in {user.addr.city}", ctx) == "kim in oslo"


def test_T02_dotted_missing_raises():
    with pytest.raises(KeyError):
        pt.render("{user.age}", {"user": {"name": "kim"}})


def test_T03_non_string_values():
    assert pt.render("n={n} f={f} b={b}", {"n": 42, "f": 1.5,
                                           "b": True}) == "n=42 f=1.5 b=True"


def test_T04_unmatched_braces_raise():
    with pytest.raises(ValueError):
        pt.render("hello {name", {"name": "x"})
    with pytest.raises(ValueError):
        pt.render("hello } there", {})
    with pytest.raises(ValueError):
        pt.render("empty {} here", {})


def test_adjacent_placeholders():
    assert pt.render("{a}{b}", {"a": "1", "b": "2"}) == "12"
