"""Sealed acceptance suite for gc-404 (microjson). Run from benchmark repo root."""
import importlib.util
import os
import re

import pytest

_PATH = os.path.join(os.getcwd(), "workspace", "gc-404", "microjson.py")
_spec = importlib.util.spec_from_file_location("microjson_under_test", _PATH)
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)


def test_source_purity_no_json_module():
    src = open(_PATH, encoding="utf-8").read()
    assert not re.search(r"^\s*import\s+json\b", src, re.M)
    assert not re.search(r"^\s*from\s+json\b", src, re.M)
    assert "__import__" not in src
    assert "importlib" not in src


def test_parse_scalars():
    assert M.loads("true") is True
    assert M.loads("false") is False
    assert M.loads("null") is None
    assert M.loads("42") == 42
    assert M.loads('"hi"') == "hi"


def test_parse_nested():
    assert M.loads('{"a": [1, {"b": [true, null]}]}') == \
        {"a": [1, {"b": [True, None]}]}


def test_number_types():
    assert isinstance(M.loads("7"), int)
    v = M.loads("1e2")
    assert isinstance(v, float) and v == 100.0
    assert isinstance(M.loads("1.5"), float)
    v0 = M.loads("-0")
    assert v0 == 0 and isinstance(v0, int)
    assert M.loads("-12.5e-1") == -1.25


def test_string_escapes():
    assert M.loads(r'"a\"b\\c\/d\b\f\n\r\t"') == 'a"b\\c/d\b\f\n\r\t'
    assert M.loads(r'"Aé"') == "Aé"


def test_surrogate_pair_escapes():
    assert M.loads('"\\uD83D\\uDE00"') == "\U0001F600"
    assert M.loads('"x\\ud83d\\ude00y"') == "x\U0001F600y"


def test_astral_raw():
    assert M.loads('"\U0001F600"') == "\U0001F600"


def test_lone_surrogate_rejected():
    for bad in [r'"\uD800"', r'"\uD800x"', r'"\uDC00"', r'"\uD83DA"']:
        with pytest.raises(ValueError):
            M.loads(bad)


def test_duplicate_keys_last_wins():
    assert M.loads('{"a":1,"a":2}') == {"a": 2}


def test_whitespace_tolerance():
    assert M.loads(' \t\r\n [ 1 , 2 ] \n') == [1, 2]


def test_reject_trailing_commas():
    for bad in ["[1,]", '{"a":1,}', "[,]"]:
        with pytest.raises(ValueError):
            M.loads(bad)


def test_reject_bad_numbers():
    for bad in ["01", "-01", "+1", ".5", "5.", "1.", "0x10", "1.e2",
                "NaN", "Infinity", "-Infinity", "- 1", "1e", "1e+"]:
        with pytest.raises(ValueError):
            M.loads(bad)


def test_reject_syntax_garbage():
    for bad in ["", "   ", "{} x", "[1] 2", "{'a':1}", '{a:1}', "[1 2]",
                '{"a" 1}', "tru", "nul", '["a]', "[", '{"a":}', "}"]:
        with pytest.raises(ValueError):
            M.loads(bad)


def test_reject_raw_control_char():
    with pytest.raises(ValueError):
        M.loads('"a\x01b"')
    with pytest.raises(ValueError):
        M.loads('"a\nb"')


def test_reject_bad_escapes():
    for bad in [r'"\x41"', r'"\U0001F600"', r'"\q"', '"\\']:
        with pytest.raises(ValueError):
            M.loads(bad)


def test_error_position_trailing_comma():
    with pytest.raises(ValueError) as ei:
        M.loads('[1,]')
    assert "line 1 col 4" in str(ei.value)


def test_error_position_bad_value():
    with pytest.raises(ValueError) as ei:
        M.loads('{"a": @}')
    assert "line 1 col 7" in str(ei.value)


def test_error_position_multiline():
    with pytest.raises(ValueError) as ei:
        M.loads('[1,\n 2,,')
    assert "line 2 col 4" in str(ei.value)


def test_dumps_compact_sorted():
    assert M.dumps({"b": 1, "a": [1, 2], "c": {"z": None}}) == \
        '{"a":[1,2],"b":1,"c":{"z":null}}'


def test_dumps_scalars():
    assert M.dumps(True) == "true"
    assert M.dumps(False) == "false"
    assert M.dumps(None) == "null"
    assert M.dumps(-5) == "-5"
    assert M.dumps(1.5) == "1.5"


def test_dumps_bool_before_int():
    assert M.dumps([True, 1]) == "[true,1]"


def test_dumps_escapes():
    assert M.dumps('a"b\\c\n\t\x01') == '"a\\"b\\\\c\\n\\t\\u0001"'


def test_dumps_non_ascii_raw():
    assert M.dumps("café\U0001F600") == '"café\U0001F600"'


def test_dumps_tuple_as_array():
    assert M.dumps((1, 2, (3,))) == "[1,2,[3]]"


def test_dumps_type_errors():
    with pytest.raises(TypeError):
        M.dumps({1: "a"})
    with pytest.raises(TypeError):
        M.dumps({"a", "b"})
    with pytest.raises(TypeError):
        M.dumps(b"bytes")


def test_dumps_nonfinite_rejected():
    for bad in [float("nan"), float("inf"), float("-inf")]:
        with pytest.raises(ValueError):
            M.dumps(bad)


def test_round_trip():
    v = {"k": [1, -2.5, "s\n", {"in": [True, False, None]}, "é"],
         "empty": {}, "arr": []}
    assert M.loads(M.dumps(v)) == v


def test_deep_nesting():
    doc = "[" * 60 + "1" + "]" * 60
    v = M.loads(doc)
    for _ in range(60):
        assert isinstance(v, list) and len(v) == 1
        v = v[0]
    assert v == 1
