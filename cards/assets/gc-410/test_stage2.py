"""Sealed stage-2 adversarial suite for gc-410 (read-only)."""
import os
import sys

sys.path.insert(0, os.path.join(os.getcwd(), "work", "gc-410"))

from iniread import parse, serialize  # noqa: E402


def test_crlf_input():
    assert parse("[a]\r\nk = v\r\n") == {"a": {"k": "v"}}


def test_tabs_are_whitespace():
    assert parse("[a]\n\tk\t=\tv\t\n") == {"a": {"k": "v"}}


def test_inline_semicolon_kept_in_value():
    assert parse("[a]\npath = C:;x\n") == {"a": {"path": "C:;x"}}


def test_indented_comment_is_comment():
    assert parse("[a]\n   ; note\nk = v\n") == {"a": {"k": "v"}}


def test_empty_brackets_name_empty_section():
    assert parse("[]\nk = v\n") == {"": {"k": "v"}}


def test_empty_value():
    assert parse("[a]\nk =\n") == {"a": {"k": ""}}


def test_unicode_keys_values():
    assert parse("[a]\nnaeme = strasse\ncafe = creme\n") == {
        "a": {"naeme": "strasse", "cafe": "creme"}}


def test_continuation_basic():
    assert parse("[a]\nk = hello\\\nworld\n") == {"a": {"k": "helloworld"}}


def test_continuation_strips_leading_ws_of_next_line():
    assert parse("[a]\nk = hello\\\n    world\n") == {"a": {"k": "helloworld"}}


def test_continuation_chain():
    assert parse("[a]\nk = a\\\nb\\\nc\n") == {"a": {"k": "abc"}}


def test_serialize_canonical_form():
    got = serialize({"b": {"k": "v", "a": "1"}, "": {"top": "yes"}})
    assert got == "top = yes\n\n[b]\na = 1\nk = v\n"


def test_serialize_empty():
    assert serialize({}) == ""


def test_round_trip():
    d = {"": {"x": "1"}, "db": {"host": "h", "port": "1"}, "z": {}}
    assert parse(serialize(d)) == d
