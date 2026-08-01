"""romanx: strict canonical Roman numerals (sealed reference)."""

_VALS = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"),
         (90, "XC"), (50, "L"), (40, "XL"), (10, "X"), (9, "IX"),
         (5, "V"), (4, "IV"), (1, "I")]


def to_roman(n):
    if not isinstance(n, int) or isinstance(n, bool):
        raise ValueError(f"not an integer: {n!r}")
    if n < 1 or n > 3999:
        raise ValueError(f"out of range 1..3999: {n}")
    out = []
    for value, symbol in _VALS:
        while n >= value:
            out.append(symbol)
            n -= value
    return "".join(out)


def from_roman(s):
    if not isinstance(s, str) or not s:
        raise ValueError(f"not a numeral: {s!r}")
    total = 0
    i = 0
    for value, symbol in _VALS:
        while s[i:i + len(symbol)] == symbol:
            total += value - 1
            i += len(symbol)
    if total < 1 or total > 3999 or to_roman(total) != s:
        raise ValueError(f"invalid numeral: {s!r}")
    return total
