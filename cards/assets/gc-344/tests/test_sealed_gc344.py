# Sealed acceptance tests for gc-344 (arrow: Arrow.dehumanize).
# Do not edit: the grader overwrites the copy in the workspace with this file.

import pytest
import arrow

BASE = arrow.Arrow(2023, 1, 15, 12, 0, 0)


def test_days_ago():
    assert BASE.dehumanize("2 days ago") == BASE.shift(days=-2)


def test_in_hours():
    assert BASE.dehumanize("in 2 hours") == BASE.shift(hours=2)


def test_singular_article_hour():
    assert BASE.dehumanize("an hour ago") == BASE.shift(hours=-1)


def test_in_a_month_is_calendar_shift():
    assert BASE.dehumanize("in a month") == arrow.Arrow(2023, 2, 15, 12, 0, 0)


def test_weeks_ago():
    assert BASE.dehumanize("3 weeks ago") == arrow.Arrow(2022, 12, 25, 12, 0, 0)


def test_just_now_and_type():
    result = BASE.dehumanize("just now")
    assert result == BASE
    assert isinstance(result, arrow.Arrow)


def test_seconds_minutes_years():
    assert BASE.dehumanize("in 30 seconds") == BASE.shift(seconds=30)
    assert BASE.dehumanize("5 minutes ago") == BASE.shift(minutes=-5)
    assert BASE.dehumanize("in 2 years") == BASE.shift(years=2)


def test_unparseable_input_raises_valueerror():
    with pytest.raises(ValueError):
        BASE.dehumanize("not a time string")


def test_explicit_english_locale():
    assert BASE.dehumanize("2 days ago", locale="en-us") == BASE.shift(days=-2)
