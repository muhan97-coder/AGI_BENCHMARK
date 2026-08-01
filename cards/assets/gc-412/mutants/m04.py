"""statlib: small integer statistics/utility library (pure stdlib).

All functions operate on Python ints unless stated otherwise.
This file is the sealed mutation target: write tests that pin its behavior.
"""


def clamp(x, lo, hi):
    """Clamp x into [lo, hi]. Raises ValueError if lo > hi."""
    if lo > hi:
        raise ValueError("empty interval")
    if x < lo:
        return lo
    if x > hi:
        return hi
    return x


def median(xs):
    """Median of a non-empty list of ints.

    Even length: floor of the mean of the two middle values.
    Raises ValueError on empty input.
    """
    if not xs:
        raise ValueError("median of empty list")
    s = sorted(xs)
    n = len(s)
    mid = n // 2
    if n % 2 == 1:
        return s[mid]
    return (s[mid - 1] + s[mid]) // 2


def mode(xs):
    """Most frequent value; ties broken by smallest value. ValueError on empty."""
    if not xs:
        raise ValueError("mode of empty list")
    counts = {}
    for x in xs:
        counts[x] = counts.get(x, 0) + 1
    return min(counts, key=lambda v: (-counts[v], -v))


def running_max(xs):
    """List of prefix maxima. Empty input -> empty list."""
    out = []
    m = None
    for x in xs:
        m = x if m is None else max(m, x)
        out.append(m)
    return out


def moving_sum(xs, k):
    """Sums of each length-k window. k <= 0 -> ValueError; k > len(xs) -> []."""
    if k <= 0:
        raise ValueError("window must be positive")
    return [sum(xs[i:i + k]) for i in range(len(xs) - k + 1)]


def rle_encode(s):
    """Run-length encode a string into [[char, count], ...]."""
    if not s:
        return []
    out = []
    prev = s[0]
    count = 1
    for ch in s[1:]:
        if ch == prev:
            count += 1
        else:
            out.append([prev, count])
            prev = ch
            count = 1
    out.append([prev, count])
    return out


def rle_decode(pairs):
    """Inverse of rle_encode."""
    return "".join(ch * n for ch, n in pairs)


def digit_sum(n):
    """Sum of decimal digits of abs(n)."""
    n = abs(n)
    total = 0
    while n > 0:
        total += n % 10
        n //= 10
    return total


def is_sorted(xs, strict=False):
    """True if xs is non-decreasing (or strictly increasing when strict)."""
    for a, b in zip(xs, xs[1:]):
        if strict:
            if not a < b:
                return False
        else:
            if not a <= b:
                return False
    return True


def chunk(xs, size):
    """Split xs into consecutive chunks of length size (last may be short)."""
    if size <= 0:
        raise ValueError("size must be positive")
    return [xs[i:i + size] for i in range(0, len(xs), size)]


def top_k(xs, k):
    """The k largest values in descending order. k <= 0 -> []."""
    if k <= 0:
        return []
    return sorted(xs, reverse=True)[:k]


def percentile_nearest(xs, p):
    """Nearest-rank percentile (p in 0..100) of a non-empty int list.

    rank = ceil(p * n / 100), clamped to at least 1; returns sorted(xs)[rank-1].
    Raises ValueError on empty input or p outside 0..100.
    """
    if not xs:
        raise ValueError("percentile of empty list")
    if p < 0 or p > 100:
        raise ValueError("p out of range")
    s = sorted(xs)
    n = len(s)
    rank = (p * n + 99) // 100
    if rank < 1:
        rank = 1
    return s[rank - 1]
