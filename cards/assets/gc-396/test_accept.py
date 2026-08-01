"""Sealed acceptance suite for gc-396 (wordtally). Run from benchmark repo root."""
import json
import os
import subprocess
import sys

TOOL = os.path.join(os.getcwd(), "workspace", "gc-396", "wordtally.py")


def run(args=(), stdin=""):
    return subprocess.run(
        [sys.executable, TOOL, *args],
        input=stdin, capture_output=True, text=True, timeout=60,
    )


def out(args=(), stdin=""):
    p = run(args, stdin)
    assert p.returncode == 0, f"exit={p.returncode} stderr={p.stderr[:500]}"
    return json.loads(p.stdout.strip())


def test_basic_count():
    d = out(stdin="apple banana apple")
    assert d == {"total_tokens": 3, "entries": [["apple", 2], ["banana", 1]]}


def test_case_folding():
    d = out(stdin="The the THE tHe")
    assert d["entries"] == [["the", 4]]
    assert d["total_tokens"] == 4


def test_tie_break_alphabetical():
    d = out(stdin="b a c b a c")
    assert d["entries"] == [["a", 2], ["b", 2], ["c", 2]]


def test_top_limits_entries():
    d = out(["--top", "2"], stdin="x y z x y x")
    assert d["entries"] == [["x", 3], ["y", 2]]
    assert d["total_tokens"] == 6


def test_default_top_is_ten():
    words = " ".join(f"w{i:02d}" for i in range(12))
    d = out(stdin=words)
    assert len(d["entries"]) == 10
    assert d["total_tokens"] == 12


def test_interior_apostrophe_kept():
    d = out(stdin="don't don't rock'n'roll")
    assert ["don't", 2] in d["entries"]
    assert ["rock'n'roll", 1] in d["entries"]


def test_edge_apostrophes_stripped():
    d = out(stdin="'tis ''quoted'' plain")
    words = [e[0] for e in d["entries"]]
    assert "tis" in words and "quoted" in words and "plain" in words
    assert all(not w.startswith("'") and not w.endswith("'") for w in words)


def test_apostrophe_only_token_discarded():
    d = out(stdin="a '' ''' b")
    assert d["total_tokens"] == 2
    assert [e[0] for e in d["entries"]] == ["a", "b"]


def test_digits_are_token_chars():
    d = out(stdin="abc123 4ever 42")
    words = sorted(e[0] for e in d["entries"])
    assert words == ["42", "4ever", "abc123"]


def test_punctuation_separates():
    d = out(stdin="foo,bar;baz!foo?bar.foo")
    assert d["entries"][0] == ["foo", 3]
    assert d["total_tokens"] == 6


def test_non_ascii_is_separator():
    d = out(stdin="café café")
    assert d["entries"] == [["caf", 2]]


def test_min_len_filters_and_total():
    d = out(["--min-len", "3"], stdin="a bb ccc dddd a")
    assert d["total_tokens"] == 2
    assert d["entries"] == [["ccc", 1], ["dddd", 1]]


def test_min_count_filters_entries_not_total():
    d = out(["--min-count", "2"], stdin="a a b")
    assert d["total_tokens"] == 3
    assert d["entries"] == [["a", 2]]


def test_top_zero_empty_entries():
    d = out(["--top", "0"], stdin="a b a")
    assert d["entries"] == []
    assert d["total_tokens"] == 3


def test_empty_input():
    d = out(stdin="")
    assert d == {"total_tokens": 0, "entries": []}


def test_usage_error_non_integer():
    p = run(["--top", "xyz"], stdin="a")
    assert p.returncode == 2
    assert json.loads(p.stdout.strip()) == {"error": "usage"}


def test_usage_error_negative_top():
    p = run(["--top", "-1"], stdin="a")
    assert p.returncode == 2
    assert json.loads(p.stdout.strip()) == {"error": "usage"}


def test_usage_error_min_len_zero():
    p = run(["--min-len", "0"], stdin="a")
    assert p.returncode == 2
    assert json.loads(p.stdout.strip()) == {"error": "usage"}


def test_usage_error_unknown_flag():
    p = run(["--frobnicate"], stdin="a")
    assert p.returncode == 2
    assert json.loads(p.stdout.strip()) == {"error": "usage"}


def test_output_is_single_json_line():
    p = run((), stdin="a b c")
    assert p.returncode == 0
    lines = [ln for ln in p.stdout.splitlines() if ln.strip()]
    assert len(lines) == 1
    json.loads(lines[0])


def test_larger_input_consistency():
    text = " ".join(["alpha"] * 400 + ["beta"] * 300 + ["gamma"] * 300)
    d = out(["--top", "3"], stdin=text)
    assert d["total_tokens"] == 1000
    assert d["entries"] == [["alpha", 400], ["beta", 300], ["gamma", 300]]
