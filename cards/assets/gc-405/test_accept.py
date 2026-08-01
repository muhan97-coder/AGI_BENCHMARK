"""Sealed acceptance suite for gc-405 (globby). Run from benchmark repo root."""
import importlib.util
import os
import re

_PATH = os.path.join(os.getcwd(), "workspace", "gc-405", "globby.py")
_spec = importlib.util.spec_from_file_location("globby_under_test", _PATH)
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)


def test_source_purity():
    src = open(_PATH, encoding="utf-8").read()
    assert not re.search(r"^\s*import\s+fnmatch\b", src, re.M)
    assert not re.search(r"^\s*from\s+fnmatch\b", src, re.M)
    assert not re.search(r"^\s*import\s+pathlib\b", src, re.M)
    assert not re.search(r"^\s*from\s+pathlib\b", src, re.M)


def test_literal_full_match():
    assert M.match("a/b.txt", "a/b.txt")
    assert not M.match("a/b.txt", "a/b.txt.bak")
    assert not M.match("a/b.txt", "x/a/b.txt")


def test_empty_pattern():
    assert M.match("", "")
    assert not M.match("", "a")


def test_star_within_segment():
    assert M.match("*.py", "main.py")
    assert M.match("src/*.py", "src/app.py")
    assert not M.match("src/*.py", "src/sub/app.py")
    assert M.match("a*", "a")


def test_star_does_not_cross_slash():
    assert not M.match("a/*", "a/b/c")
    assert M.match("a/*", "a/b")
    assert not M.match("*", "a/b")


def test_question_mark():
    assert M.match("?.txt", "a.txt")
    assert not M.match("?.txt", "ab.txt")
    assert not M.match("a?b", "a/b")


def test_class_basic():
    assert M.match("[abc].txt", "b.txt")
    assert not M.match("[abc].txt", "d.txt")
    assert M.match("file[0-9]", "file7")
    assert not M.match("file[0-9]", "filex")


def test_class_mixed_ranges():
    assert M.match("[a-cx-z0]", "y")
    assert M.match("[a-cx-z0]", "0")
    assert not M.match("[a-cx-z0]", "m")


def test_class_negation():
    assert M.match("[!abc]", "d")
    assert not M.match("[!abc]", "a")


def test_class_never_matches_slash():
    assert not M.match("a[/]b", "a/b")
    assert not M.match("a[!x]b", "a/b")


def test_class_bracket_first_is_literal():
    assert M.match("[]a]", "]")
    assert M.match("[]a]", "a")
    assert not M.match("[]a]", "b")


def test_class_negated_bracket_first():
    assert not M.match("[!]a]", "]")
    assert not M.match("[!]a]", "a")
    assert M.match("[!]a]", "z")


def test_class_dash_literal():
    assert M.match("[a-]", "-")
    assert M.match("[a-]", "a")
    assert M.match("[-a]", "-")
    assert not M.match("[a-]", "b")


def test_unclosed_bracket_is_literal():
    assert M.match("a[b", "a[b")
    assert not M.match("a[b", "ab")


def test_reversed_range_matches_nothing_extra():
    assert not M.match("[z-a]", "m")
    assert M.match("[z-ax]", "x")


def test_globstar_alone():
    assert M.match("**", "")
    assert M.match("**", "a")
    assert M.match("**", "a/b/c")


def test_globstar_leading_zero_segments():
    assert M.match("**/foo.txt", "foo.txt")
    assert M.match("**/foo.txt", "a/foo.txt")
    assert M.match("**/foo.txt", "a/b/foo.txt")
    assert not M.match("**/foo.txt", "a/b/foo.txt.bak")


def test_globstar_trailing_excludes_bare_head():
    assert M.match("head/**", "head/x")
    assert M.match("head/**", "head/x/y")
    assert not M.match("head/**", "head")
    assert not M.match("head/**", "heads/x")


def test_globstar_middle():
    assert M.match("a/**/b", "a/b")
    assert M.match("a/**/b", "a/x/b")
    assert M.match("a/**/b", "a/x/y/b")
    assert not M.match("a/**/b", "a/x/y")


def test_globstar_inside_segment_is_plain_star():
    assert M.match("a**b", "axxb")
    assert not M.match("a**b", "ax/xb")
    assert M.match("x**", "xyz")
    assert not M.match("x**", "x/y")


def test_multiple_globstars():
    assert M.match("**/a/**", "a/b")
    assert M.match("**/a/**", "x/a/b/c")
    assert not M.match("**/a/**", "a")
    assert not M.match("**/a/**", "x/y/b")


def test_no_escape_char_class_workaround():
    assert M.match("[*].txt", "*.txt")
    assert not M.match("[*].txt", "a.txt")
    assert M.match("what[?]", "what?")
    assert not M.match("what[?]", "whata")


def test_regex_metachars_are_literal():
    assert M.match("a.b+c(d)e", "a.b+c(d)e")
    assert not M.match("a.b", "axb")
    assert M.match("we ird$", "we ird$")


def test_case_sensitive():
    assert M.match("Readme.md", "Readme.md")
    assert not M.match("readme.md", "Readme.md")


def test_any_match():
    pats = ["*.py", "src/**", "**/*.md"]
    assert M.any_match(pats, "tool.py")
    assert M.any_match(pats, "src/deep/x.bin")
    assert M.any_match(pats, "docs/guide.md")
    assert not M.any_match(pats, "bin/app.exe")
    assert not M.any_match([], "anything")
