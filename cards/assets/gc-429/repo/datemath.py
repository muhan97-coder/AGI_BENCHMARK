"""Proleptic Gregorian date arithmetic, no stdlib date deps (gc-429 target)."""
from __future__ import annotations

_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
_MONTH_NAMES = ["January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November",
                "December"]


def is_leap(year: int) -> bool:
    if year % 400 == 0:
        return True
    if year % 100 == 0:
        return False
    return year % 4 == 0


def days_in_month(year: int, month: int) -> int:
    if month < 1 or month > 12:
        raise ValueError("month out of range")
    if month == 2 and is_leap(year):
        return 29
    return _DAYS[month - 1]


def validate(year: int, month: int, day: int) -> None:
    if day < 1 or day > days_in_month(year, month):
        raise ValueError("day out of range")


def day_of_year(year: int, month: int, day: int) -> int:
    validate(year, month, day)
    total = day
    for m in range(1, month):
        total += days_in_month(year, m)
    return total


def add_days(year: int, month: int, day: int, n: int) -> tuple[int, int, int]:
    """Date n days after (n >= 0)."""
    if n < 0:
        raise ValueError("n must be >= 0")
    validate(year, month, day)
    while n > 0:
        step = min(n, days_in_month(year, month) - day)
        if step == 0:
            day = 1
            month += 1
            if month > 12:
                month = 1
                year += 1
            n -= 1
        else:
            day += step
            n -= step
    return (year, month, day)


def weekday(year: int, month: int, day: int) -> int:
    """0=Monday .. 6=Sunday (proleptic Gregorian)."""
    validate(year, month, day)
    y = year
    m = month
    if m < 3:
        m += 12
        y -= 1
    k = y % 100
    j = y // 100
    h = (day + 13 * (m + 1) // 5 + k + k // 4 + j // 4 + 5 * j) % 7
    return (h + 5) % 7


def month_name(month: int) -> str:
    if month < 1 or month > 12:
        raise ValueError("month out of range")
    return _MONTH_NAMES[month - 1]
