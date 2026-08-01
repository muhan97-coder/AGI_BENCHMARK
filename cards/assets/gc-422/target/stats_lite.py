"""Small pure-python statistics helpers (mutation target for gc-422)."""
from __future__ import annotations


def clamp(x: float, lo: float, hi: float) -> float:
    """Clamp x into [lo, hi]. Raises ValueError when lo > hi."""
    if lo > hi:
        raise ValueError("lo must be <= hi")
    if x < lo:
        return lo
    if x > hi:
        return hi
    return x


def mean(xs: list[float]) -> float:
    """Arithmetic mean. Raises ValueError on empty input."""
    if not xs:
        raise ValueError("mean of empty list")
    return sum(xs) / len(xs)


def median(xs: list[float]) -> float:
    """Median (average of two middles for even length)."""
    if not xs:
        raise ValueError("median of empty list")
    s = sorted(xs)
    n = len(s)
    mid = n // 2
    if n % 2 == 1:
        return s[mid]
    return (s[mid - 1] + s[mid]) / 2


def variance(xs: list[float]) -> float:
    """Population variance. Raises ValueError when fewer than 2 samples."""
    if len(xs) < 2:
        raise ValueError("variance needs >= 2 samples")
    m = mean(xs)
    return sum((x - m) ** 2 for x in xs) / len(xs)


def zscores(xs: list[float]) -> list[float]:
    """Z-score of each sample; all zeros when variance is zero."""
    v = variance(xs)
    if v == 0:
        return [0.0 for _ in xs]
    m = mean(xs)
    sd = v ** 0.5
    return [(x - m) / sd for x in xs]


def percentile(xs: list[float], p: float) -> float:
    """Nearest-rank percentile, p in [0, 100]."""
    if not xs:
        raise ValueError("percentile of empty list")
    if p < 0 or p > 100:
        raise ValueError("p out of range")
    s = sorted(xs)
    if p == 0:
        return s[0]
    rank = max(1, int(-(-p * len(s) // 100)))  # ceil(p*n/100), at least 1
    return s[rank - 1]
