"""Sealed acceptance suite for gc-397 (csvcast). Run from benchmark repo root."""
import json
import os
import subprocess
import sys

TOOL = os.path.join(os.getcwd(), "workspace", "gc-397", "csvcast.py")


def run(args=(), stdin=""):
    return subprocess.run(
        [sys.executable, TOOL, *args],
        input=stdin, capture_output=True, text=True, timeout=60,
    )


def rows(stdin, args=()):
    p = run(args, stdin)
    assert p.returncode == 0, f"exit={p.returncode} stderr={p.stderr[:500]}"
    return [json.loads(ln) for ln in p.stdout.splitlines() if ln.strip()]


def test_basic_types():
    r = rows("a,b,c,d\n1,2.5,true,hello\n")
    assert r == [{"a": 1, "b": 2.5, "c": True, "d": "hello"}]


def test_int_type_is_int():
    r = rows("a\n42\n")
    assert isinstance(r[0]["a"], int) and r[0]["a"] == 42


def test_leading_zero_stays_string():
    r = rows("a,b\n007,0\n")
    assert r == [{"a": "007", "b": 0}]


def test_plus_sign_stays_string():
    r = rows("a\n+1\n")
    assert r[0]["a"] == "+1"


def test_scientific_notation_stays_string():
    r = rows("a\n1e5\n")
    assert r[0]["a"] == "1e5"


def test_bool_case_insensitive():
    r = rows("a,b,c\nTRUE,False,tRuE\n")
    assert r == [{"a": True, "b": False, "c": True}]


def test_null_word_and_empty_cell():
    r = rows("a,b,c\nNULL,null,\n")
    assert r == [{"a": None, "b": None, "c": None}]


def test_negative_zero_int():
    r = rows("a\n-0\n")
    assert r[0]["a"] == 0 and isinstance(r[0]["a"], int)


def test_float_edge_forms_stay_string():
    r = rows("a,b,c,d\n1.,.5,00.5,-0.5\n")
    assert r == [{"a": "1.", "b": ".5", "c": "00.5", "d": -0.5}]


def test_whitespace_not_trimmed():
    r = rows('a\n" 42"\n')
    assert r[0]["a"] == " 42"


def test_quoted_comma():
    r = rows('a,b\n"x,y",2\n')
    assert r == [{"a": "x,y", "b": 2}]


def test_quoted_embedded_newline():
    r = rows('a,b\n"line1\nline2",ok\n')
    assert r == [{"a": "line1\nline2", "b": "ok"}]


def test_quoting_does_not_change_inference():
    r = rows('a,b\n"007","3"\n')
    assert r == [{"a": "007", "b": 3}]


def test_duplicate_headers():
    r = rows("a,a,a\n1,2,3\n")
    assert r == [{"a": 1, "a.2": 2, "a.3": 3}]


def test_empty_header_named_by_index():
    r = rows("a,,c\n1,2,3\n")
    assert r == [{"a": 1, "col2": 2, "c": 3}]


def test_key_order_matches_header():
    r = run((), "z,y,x\n1,2,3\n")
    obj = json.loads(r.stdout.splitlines()[0])
    assert list(obj.keys()) == ["z", "y", "x"]


def test_short_row_padded_null():
    r = rows("a,b,c\n1\n")
    assert r == [{"a": 1, "b": None, "c": None}]


def test_long_row_extra_raw_strings():
    r = rows("a,b\n1,2,003,true\n")
    assert r == [{"a": 1, "b": 2, "_extra": ["003", "true"]}]


def test_strict_ragged_aborts():
    p = run(["--strict"], "a,b\n1,2\n1,2,3\n9,9\n")
    assert p.returncode == 3
    lines = [ln for ln in p.stdout.splitlines() if ln.strip()]
    assert json.loads(lines[0]) == {"a": 1, "b": 2}
    assert json.loads(lines[-1]) == {"error": "ragged", "row": 2}


def test_strict_short_row_also_aborts():
    p = run(["--strict"], "a,b\n1\n")
    assert p.returncode == 3
    assert json.loads(p.stdout.splitlines()[-1]) == {"error": "ragged", "row": 1}


def test_strict_clean_input_ok():
    r = rows("a,b\n1,2\n", args=["--strict"])
    assert r == [{"a": 1, "b": 2}]


def test_empty_input():
    p = run((), "")
    assert p.returncode == 0 and p.stdout.strip() == ""


def test_header_only():
    p = run((), "a,b,c\n")
    assert p.returncode == 0 and p.stdout.strip() == ""


def test_multiple_rows_are_json_lines():
    p = run((), "n\n1\n2\n3\n")
    lines = [ln for ln in p.stdout.splitlines() if ln.strip()]
    assert [json.loads(ln)["n"] for ln in lines] == [1, 2, 3]
