"""Sealed acceptance suite for gc-401 (tably). Run from benchmark repo root."""
import importlib.util
import os

import pytest

_PATH = os.path.join(os.getcwd(), "workspace", "gc-401", "tably.py")
_spec = importlib.util.spec_from_file_location("tably_under_test", _PATH)
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)


def test_golden_basic():
    got = M.render(["name", "qty"], [["apple", 3], ["kiwi", 12]])
    assert got == "| name  | qty |\n|-------|-----|\n| apple | 3   |\n| kiwi  | 12  |"


def test_golden_right_align():
    got = M.render(["name", "qty"], [["apple", 3], ["kiwi", 12]], aligns="lr")
    assert got == "| name  | qty |\n|-------|-----|\n| apple |   3 |\n| kiwi  |  12 |"


def test_golden_truncation():
    got = M.render(["h"], [["abcdefghij"]], max_col=6)
    assert got == "| h      |\n|--------|\n| abc... |"


def test_golden_short_row_and_center():
    got = M.render(["a", "b"], [[1]], aligns="cc")
    assert got == "| a | b |\n|---|---|\n| 1 |   |"


def test_golden_headers_only():
    assert M.render(["col"], []) == "| col |\n|-----|"


def test_no_trailing_newline():
    assert not M.render(["a"], [["x"]]).endswith("\n")


def test_header_sets_width():
    got = M.render(["longheader"], [["x"]])
    lines = got.split("\n")
    assert lines[0] == "| longheader |"
    assert lines[2] == "| x          |"


def test_cell_sets_width():
    got = M.render(["h"], [["wide-cell"]])
    assert got.split("\n")[0] == "| h         |"


def test_center_extra_space_goes_right():
    # width 4, cell "ab" -> pad 2 -> 1 left, 1 right; cell "abc" -> 0 left, 1 right
    got = M.render(["hhhh"], [["ab"], ["abc"]], aligns="c")
    lines = got.split("\n")
    assert lines[2] == "|  ab  |"
    assert lines[3] == "| abc  |"


def test_right_align_column():
    got = M.render(["n"], [[5], [500]], aligns="r")
    lines = got.split("\n")
    assert lines[2] == "|   5 |"
    assert lines[3] == "| 500 |"


def test_none_and_int_cells_via_str():
    got = M.render(["a", "b"], [[None, 7]])
    assert got.split("\n")[2] == "| None | 7 |"


def test_header_truncated_by_max_col():
    got = M.render(["abcdefgh"], [["x"]], max_col=5)
    lines = got.split("\n")
    assert lines[0] == "| ab... |"
    assert lines[1] == "|-------|"


def test_separator_geometry():
    got = M.render(["ab", "c"], [["ab", "c"]])
    assert got.split("\n")[1] == "|----|---|"


def test_all_lines_equal_length():
    got = M.render(["one", "two", "three"], [[1, 22, 333], ["a", "bb", "ccc"]],
                   aligns="lrc")
    lens = {len(ln) for ln in got.split("\n")}
    assert len(lens) == 1


def test_aligns_shorter_padded_left():
    got = M.render(["a", "b"], [["x", "y"]], aligns="r")
    lines = got.split("\n")
    assert lines[2] == "| x | y |"


def test_empty_headers_raises():
    with pytest.raises(ValueError):
        M.render([], [])


def test_row_too_long_raises():
    with pytest.raises(ValueError):
        M.render(["a"], [[1, 2]])


def test_bad_align_char_raises():
    with pytest.raises(ValueError):
        M.render(["a"], [], aligns="x")


def test_aligns_too_long_raises():
    with pytest.raises(ValueError):
        M.render(["a"], [], aligns="ll")


def test_max_col_too_small_raises():
    for bad in [3, 0, -1]:
        with pytest.raises(ValueError):
            M.render(["a"], [], max_col=bad)


def test_exact_fit_not_truncated():
    got = M.render(["abcd"], [["abcd"]], max_col=4)
    assert got.split("\n")[2] == "| abcd |"


def test_multi_column_mixed():
    got = M.render(["id", "name", "score"],
                   [[1, "alpha", 9.5], [2, "b", 10]], aligns="rlc")
    lines = got.split("\n")
    assert lines[0] == "| id | name  | score |"
    assert lines[2] == "|  1 | alpha |  9.5  |"
    assert lines[3] == "|  2 | b     |  10   |"
