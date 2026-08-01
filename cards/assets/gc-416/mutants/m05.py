"""calweeks: ISO-8601 week calculus, pure arithmetic (sealed)."""

_DIM = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def _is_leap(y):
    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)


def _days_in_month(y, m):
    if m == 2 and _is_leap(y):
        return 29
    return _DIM[m - 1]


def _day_of_year(y, m, d):
    total = d
    for i in range(1, m):
        total += _days_in_month(y, i)
    return total


def _days_before_year(y):
    yy = y - 1
    return yy * 365 + yy // 4 - yy // 100 + yy // 400


def _weekday(y, m, d):
    """1=Monday .. 7=Sunday."""
    return (_days_before_year(y) + _day_of_year(y, m, d) - 1) % 7 + 1


def _weeks_in_year(y):
    jan1 = _weekday(y, 1, 1)
    return 53 if jan1 == 4 or (_is_leap(y) and jan1 == 3) else 52


def iso_week(y, m, d):
    """Return (iso_year, iso_week, iso_weekday) for a Gregorian date."""
    if not (1 <= m <= 12) or not (1 <= d <= _days_in_month(y, m)):
        raise ValueError(f"invalid date: {y}-{m}-{d}")
    wd = _weekday(y, m, d)
    week = (_day_of_year(y, m, d) - wd + 10) // 7
    if week < 1:
        return (y - 1, _weeks_in_year(y - 1), wd)
    if week > _weeks_in_year(y):
        return (y + 1, 1, wd)
    return (y, week, wd)
