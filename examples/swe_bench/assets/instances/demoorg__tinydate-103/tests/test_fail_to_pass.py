"""FAIL_TO_PASS for demoorg__tinydate-103 (sealed: copied in by the harness)."""

from tinydate import format_duration


def test_zero_renders_as_zero_seconds():
    assert format_duration(0) == "0s"


def test_sub_second_renders_as_zero_seconds():
    assert format_duration(0.4) == "0s"
