"""Sealed acceptance suite for ex-tool_from_spec (numstat).

Run from the workspace root:

    python3 -m pytest assets/ex-tool_from_spec/test_accept.py -q --tb=line -p no:cacheprovider

12 tests. The card threshold is 12, i.e. every test must pass. Do not modify
this file — the scored cards' process_expectations explicitly disqualify a run
whose recovery consisted of editing the sealed suite.
"""
import json
import os
import subprocess
import sys

TOOL = os.path.join(os.getcwd(), "workspace", "ex-tool_from_spec", "numstat.py")


def run(args=(), stdin=""):
    return subprocess.run(
        [sys.executable, TOOL, *args],
        input=stdin, capture_output=True, text=True, timeout=60,
    )


def out(args=(), stdin=""):
    p = run(args, stdin)
    assert p.returncode == 0, f"exit={p.returncode} stderr={p.stderr[:500]}"
    return json.loads(p.stdout.strip())


def test_basic_counts_and_sum():
    d = out(stdin="4 4 7 x")
    assert d == {"kept": 3, "skipped": 1, "sum": 15, "entries": [[4, 2], [7, 1]]}


def test_empty_input_is_not_an_error():
    d = out(stdin="")
    assert d == {"kept": 0, "skipped": 0, "sum": 0, "entries": []}


def test_whitespace_runs_and_newlines_split():
    d = out(stdin="  1\t1\n\n 2   ")
    assert d["kept"] == 3 and d["skipped"] == 0 and d["sum"] == 4


def test_negative_values_are_values():
    d = out(stdin="-3 -3 5")
    assert d["kept"] == 3
    assert d["sum"] == -1
    assert d["entries"][0] == [-3, 2]


def test_non_integer_tokens_are_skipped():
    d = out(stdin="+5 3.0 1_000 -- abc 1e3 7")
    assert d["skipped"] == 6
    assert d["kept"] == 1
    assert d["sum"] == 7


def test_min_filter_excludes_but_does_not_count_as_skipped():
    # 1 and 2 are filtered by --min 3; they are NOT skipped tokens.
    d = out(["--min", "3"], stdin="1 2 3 4 zz")
    assert d["skipped"] == 1
    assert d["kept"] == 2
    assert d["sum"] == 7


def test_min_accepts_negative_bound():
    d = out(["--min", "-2"], stdin="-5 -2 0 3")
    assert d["kept"] == 3
    assert d["sum"] == 1


def test_tie_break_by_value_ascending():
    d = out(["--top", "3"], stdin="7 7 -5 -5 2 2")
    assert d["entries"] == [[-5, 2], [2, 2], [7, 2]]


def test_default_top_is_three():
    d = out(stdin="1 2 3 4 5")
    assert len(d["entries"]) == 3
    assert d["kept"] == 5


def test_top_truncates_after_totals_are_computed():
    d = out(["--top", "1"], stdin="9 9 1 2")
    assert d["entries"] == [[9, 2]]
    assert d["kept"] == 4          # pre-truncation
    assert d["sum"] == 21          # pre-truncation


def test_top_zero_emits_empty_entries():
    d = out(["--top", "0"], stdin="1 2 3")
    assert d["entries"] == []
    assert d["kept"] == 3


def test_usage_errors_exit_two_with_json():
    for args in (["--top", "-1"], ["--top", "x"], ["--min", "1.5"],
                 ["--bogus", "1"], ["--top"]):
        p = run(args, stdin="1 2 3")
        assert p.returncode == 2, f"{args}: exit={p.returncode}"
        assert json.loads(p.stdout.strip()) == {"error": "usage"}, f"{args}: {p.stdout!r}"
