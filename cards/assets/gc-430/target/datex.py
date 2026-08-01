"""Proleptic Gregorian date arithmetic from first principles (no datetime).

Dates are (year, month, day) tuples with year >= 1. Ordinal day 1 is
0001-01-01. Weekday 0 is Monday. ISO week numbering follows ISO 8601.
"""

DAYS_IN_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def is_leap(year):
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def days_in_month(year, month):
    if month < 1 or month > 12:
        raise ValueError("month out of range")
    if month == 2 and is_leap(year):
        return 29
    return DAYS_IN_MONTH[month - 1]


def validate(year, month, day):
    if year < 1:
        raise ValueError("year out of range")
    if day < 1 or day > days_in_month(year, month):
        raise ValueError("day out of range")


def to_ordinal(year, month, day):
    """Days since 0000-12-31; 0001-01-01 is ordinal 1."""
    validate(year, month, day)
    y = year - 1
    n = y * 365 + y // 4 - y // 100 + y // 400
    for m in range(1, month):
        n += days_in_month(year, m)
    return n + day


def from_ordinal(n):
    """Inverse of to_ordinal."""
    if n < 1:
        raise ValueError("ordinal must be >= 1")
    year = (n * 400) // 146097 + 1
    while to_ordinal(year, 1, 1) > n:
        year -= 1
    while to_ordinal(year, 12, 31) < n:
        year += 1
    month = 1
    while to_ordinal(year, month, days_in_month(year, month)) < n:
        month += 1
    day = n - to_ordinal(year, month, 1) + 1
    return (year, month, day)


def weekday(year, month, day):
    """0 = Monday ... 6 = Sunday."""
    return (to_ordinal(year, month, day) - 1) % 7


def add_days(year, month, day, n):
    return from_ordinal(to_ordinal(year, month, day) + n)


def add_months(year, month, day, n):
    """Shift by n calendar months, clamping the day to the month end."""
    validate(year, month, day)
    idx = (year * 12 + (month - 1)) + n
    y, m = idx // 12, idx % 12 + 1
    if y < 1:
        raise ValueError("resulting year out of range")
    d = min(day, days_in_month(y, m))
    return (y, m, d)


def diff_days(a, b):
    """Signed day count b minus a; both are (y, m, d) tuples."""
    return to_ordinal(*b) - to_ordinal(*a)


def iso_week(year, month, day):
    """ISO 8601 (iso_year, iso_week) for the date."""
    ordinal = to_ordinal(year, month, day)
    wd = (ordinal - 1) % 7
    thursday = ordinal - wd + 3
    iso_year, _, _ = from_ordinal(thursday)
    jan4 = to_ordinal(iso_year, 1, 4)
    week1_monday = jan4 - ((jan4 - 1) % 7)
    week = (ordinal - week1_monday) // 7 + 1
    return (iso_year, week)


def parse_iso(s):
    """Parse 'YYYY-MM-DD' into a validated (y, m, d) tuple."""
    parts = s.split("-")
    if len(parts) != 3 or len(parts[0]) != 4 or len(parts[1]) != 2 or len(parts[2]) != 2:
        raise ValueError("expected YYYY-MM-DD")
    if not all(p.isdigit() for p in parts):
        raise ValueError("expected digits")
    y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
    validate(y, m, d)
    return (y, m, d)


def format_iso(year, month, day):
    validate(year, month, day)
    return f"{year:04d}-{month:02d}-{day:02d}"


def business_days_between(a, b):
    """Count weekdays (Mon-Fri) in the half-open range [a, b)."""
    start, end = to_ordinal(*a), to_ordinal(*b)
    if end < start:
        raise ValueError("b before a")
    count = 0
    for n in range(start, end):
        if (n - 1) % 7 < 5:
            count += 1
    return count
