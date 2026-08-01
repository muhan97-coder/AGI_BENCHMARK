"""Sealed stage-2 suite for gc-415 (read-only)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.getcwd(), "work", "gc-415"))

from tableform import render  # noqa: E402


def test_basic_grid():
    got = render(["name", "qty"], [["ab", "1"], ["c", "22"]])
    assert got == ("| name | qty |\n"
                   "| ---- | --- |\n"
                   "| ab   | 1   |\n"
                   "| c    | 22  |\n")


def test_cell_wider_than_header():
    got = render(["x"], [["wide-cell"]])
    assert got == ("| x         |\n"
                   "| --------- |\n"
                   "| wide-cell |\n")


def test_header_only():
    got = render(["a", "bb"], [])
    assert got == "| a | bb |\n| - | -- |\n"


def test_single_trailing_newline():
    got = render(["a"], [["1"]])
    assert got.endswith("|\n") and not got.endswith("\n\n")


def test_empty_headers_raise():
    with pytest.raises(ValueError):
        render([], [])


def test_row_length_mismatch_raises():
    with pytest.raises(ValueError):
        render(["a", "b"], [["only-one"]])


def test_empty_string_cells():
    got = render(["k"], [[""]])
    assert got == "| k |\n| - |\n|   |\n"


def test_widths_independent_per_column():
    got = render(["a", "long"], [["xxxx", "y"]])
    assert got == ("| a    | long |\n"
                   "| ---- | ---- |\n"
                   "| xxxx | y    |\n")
