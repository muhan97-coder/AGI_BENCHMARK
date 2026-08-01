"""PASS_TO_PASS for demoorg__tinypath-102 (sealed: copied in by the harness)."""

from tinypath import normalize


def test_relative_parent_is_collapsed():
    assert normalize("a/b/../c") == "a/c"


def test_leading_relative_parent_is_preserved():
    assert normalize("../a/b") == "../a/b"


def test_dots_and_duplicate_separators():
    assert normalize("./a//b/") == "a/b"


def test_root_is_root():
    assert normalize("/") == "/"


def test_empty_path_is_here():
    assert normalize("") == "."
