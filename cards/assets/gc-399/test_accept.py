"""Sealed acceptance suite for gc-399 (jsonpick). Run from benchmark repo root."""
import importlib.util
import json
import os
import subprocess
import sys

import pytest

_DIR = os.path.join(os.getcwd(), "workspace", "gc-399")
_PATH = os.path.join(_DIR, "jsonpick.py")
_spec = importlib.util.spec_from_file_location("jsonpick_under_test", _PATH)
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)

DOC = {
    "store": {
        "book": [
            {"title": "A", "price": 5},
            {"title": "B", "price": 15},
            {"title": "C"},
        ],
        "count": 3,
    },
    "x.y": {"deep": [1, 2, 3]},
    "arr": [[1, 2], [3], []],
}


def cli(args, stdin=""):
    return subprocess.run(
        [sys.executable, _PATH, *args],
        input=stdin, capture_output=True, text=True, timeout=60,
    )


def test_root_alone():
    assert M.pick({"a": 1}, "$") == [{"a": 1}]


def test_dot_key():
    assert M.pick(DOC, "$.store.count") == [3]


def test_index():
    assert M.pick(DOC, "$.store.book[1].title") == ["B"]


def test_negative_index():
    assert M.pick(DOC, "$.store.book[-1].title") == ["C"]


def test_out_of_range_index_no_match():
    assert M.pick(DOC, "$.store.book[99]") == []


def test_missing_key_no_match():
    assert M.pick(DOC, "$.store.missing.deeper") == []


def test_wildcard_on_list():
    assert M.pick(DOC, "$.store.book[*].price") == [5, 15]


def test_wildcard_on_dict_sorted_keys():
    assert M.pick({"b": 2, "a": 1, "c": 3}, "$[*]") == [1, 2, 3]


def test_chained_wildcards():
    assert M.pick(DOC, "$.arr[*][*]") == [1, 2, 3]


def test_slice_basic():
    assert M.pick(DOC, "$.store.book[0:2][*].title") == ["A", "B"]


def test_slice_open_ends():
    assert M.pick([10, 20, 30, 40], "$[1:]") == [[20, 30, 40]]
    assert M.pick([10, 20, 30, 40], "$[:2]") == [[10, 20]]


def test_slice_negative():
    assert M.pick([10, 20, 30, 40], "$[-2:]") == [[30, 40]]


def test_slice_on_non_list_no_match():
    assert M.pick({"a": 1}, "$[0:2]") == []


def test_quoted_key_with_dot():
    assert M.pick(DOC, '$["x.y"].deep[0]') == [1]


def test_quoted_key_escapes():
    assert M.pick({'he said "hi"': 1, "back\\slash": 2}, '$["he said \\"hi\\""]') == [1]
    assert M.pick({"back\\slash": 2}, '$["back\\\\slash"]') == [2]


def test_index_on_dict_no_match():
    assert M.pick({"0": "zero"}, "$[0]") == []


def test_key_on_list_no_match():
    assert M.pick([1, 2, 3], "$.length") == []


def test_wildcard_on_scalar_no_match():
    assert M.pick(42, "$[*]") == []


def test_syntax_errors_raise_valueerror():
    for bad in ["", "a.b", "$.", "$.9lives", "$[", "$[]", "$['x']",
                "$[1", '$["a\\b"]', "$ .a", "$.a b", "$[1.5]"]:
        with pytest.raises(ValueError):
            M.pick(DOC, bad)


def test_cli_success():
    p = cli(["$.store.book[*].price"], json.dumps(DOC))
    assert p.returncode == 0
    assert json.loads(p.stdout.strip()) == {"count": 2, "matches": [5, 15]}


def test_cli_single_line_output():
    p = cli(["$"], "{}")
    lines = [ln for ln in p.stdout.splitlines() if ln.strip()]
    assert len(lines) == 1
    assert json.loads(lines[0]) == {"count": 1, "matches": [{}]}


def test_cli_bad_path():
    p = cli(["$["], "{}")
    assert p.returncode == 2
    assert json.loads(p.stdout.strip()) == {"error": "path"}


def test_cli_bad_json():
    p = cli(["$"], "{not json")
    assert p.returncode == 3
    assert json.loads(p.stdout.strip()) == {"error": "json"}


def test_cli_usage():
    p = cli([], "{}")
    assert p.returncode == 4
    assert json.loads(p.stdout.strip()) == {"error": "usage"}
