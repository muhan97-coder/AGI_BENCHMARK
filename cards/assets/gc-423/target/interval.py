"""Closed-interval arithmetic on (lo, hi) tuples (mutation target for gc-423).

An interval is a tuple (lo, hi) with lo <= hi, closed on both ends.
All functions treat inputs as immutable and return new structures.
"""
from __future__ import annotations

Interval = tuple[float, float]


def validate(iv: Interval) -> Interval:
    """Return iv unchanged; raise ValueError when malformed."""
    lo, hi = iv
    if lo > hi:
        raise ValueError(f"malformed interval: {iv}")
    return iv


def normalize(ivs: list[Interval]) -> list[Interval]:
    """Sort and merge overlapping or touching intervals."""
    if not ivs:
        return []
    s = sorted(validate(iv) for iv in ivs)
    merged = [s[0]]
    for lo, hi in s[1:]:
        mlo, mhi = merged[-1]
        if lo <= mhi:
            if hi > mhi:
                merged[-1] = (mlo, hi)
        else:
            merged.append((lo, hi))
    return merged


def contains(ivs: list[Interval], x: float) -> bool:
    """True when x lies inside any interval (closed ends)."""
    for lo, hi in ivs:
        if lo <= x <= hi:
            return True
    return False


def intersect(a: Interval, b: Interval) -> Interval | None:
    """Intersection of two intervals, or None when disjoint."""
    validate(a)
    validate(b)
    lo = max(a[0], b[0])
    hi = min(a[1], b[1])
    if lo > hi:
        return None
    return (lo, hi)


def total_length(ivs: list[Interval]) -> float:
    """Total covered length after merging."""
    return sum(hi - lo for lo, hi in normalize(ivs))


def clip(ivs: list[Interval], lo: float, hi: float) -> list[Interval]:
    """Restrict a normalized view of ivs to the window [lo, hi]."""
    if lo > hi:
        raise ValueError("empty clip window")
    out = []
    for a, b in normalize(ivs):
        c = intersect((a, b), (lo, hi))
        if c is not None:
            out.append(c)
    return out


def gaps(ivs: list[Interval]) -> list[Interval]:
    """Uncovered intervals strictly between consecutive merged intervals."""
    merged = normalize(ivs)
    out = []
    for (al, ah), (bl, bh) in zip(merged, merged[1:]):
        if bl > ah:
            out.append((ah, bl))
    return out


def coverage_ratio(ivs: list[Interval], window: Interval) -> float:
    """Fraction of the window covered by ivs; 0.0 for a zero-width window."""
    wlo, whi = validate(window)
    if whi == wlo:
        return 0.0
    covered = total_length(clip(ivs, wlo, whi))
    return covered / (whi - wlo)
