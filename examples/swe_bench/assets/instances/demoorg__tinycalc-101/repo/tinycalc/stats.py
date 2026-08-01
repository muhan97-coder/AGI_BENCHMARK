"""Descriptive statistics helpers."""


def mean(values):
    """Arithmetic mean of *values*, or None for an empty series."""
    values = list(values)
    if not values:
        return None
    return sum(values) / len(values)


def percent_change(old, new):
    """Percent change from *old* to *new*."""
    return (new - old) / old * 100.0
