"""PASS_TO_PASS for demoorg__tinydate-103 (sealed: copied in by the harness)."""

import pytest

from tinydate import format_duration


def test_whole_hour_drops_empty_units():
    assert format_duration(3600) == "1h"


def test_hour_and_minutes():
    assert format_duration(5400) == "1h 30m"


def test_minute_and_seconds():
    assert format_duration(61) == "1m 1s"


def test_seconds_only():
    assert format_duration(45) == "45s"


def test_all_three_units():
    assert format_duration(3661) == "1h 1m 1s"


def test_negative_raises():
    with pytest.raises(ValueError):
        format_duration(-1)
