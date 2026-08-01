"""FAIL_TO_PASS for demoorg__tinypath-102 (sealed: copied in by the harness)."""

from tinypath import normalize


def test_extra_parents_clamp_at_root():
    assert normalize("/a/../../b") == "/b"


def test_leading_parent_clamps_at_root():
    assert normalize("/../x") == "/x"


def test_only_parents_collapse_to_root():
    assert normalize("/../..") == "/"
