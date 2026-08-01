"""numio: small integer parsing/arithmetic library (pure stdlib). Sealed mutation target."""


def parse_int(s):
    """Parse an int; accepts 0x/0o/0b prefixes and _ separators. ValueError otherwise."""
    return int(s.strip().replace("_", ""), 0)


_ROMAN = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"),
          (90, "XC"), (50, "L"), (40, "XL"), (10, "X"), (9, "IX"),
          (5, "V"), (4, "IV"), (1, "I")]


def int_to_roman(n):
    """Roman numeral for 1..3999; ValueError outside that range."""
    if n < 1 or n > 3999:
        raise ValueError("out of range")
    out = []
    for value, sym in _ROMAN:
        while n >= value:
            out.append(sym)
            n -= value
    return "".join(out)


def roman_to_int(s):
    """Value of a roman numeral (subtractive rule); ValueError on bad chars/empty."""
    values = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    if not s:
        raise ValueError("empty")
    total = 0
    prev = 0
    for ch in reversed(s):
        if ch not in values:
            raise ValueError("bad char")
        v = values[ch]
        if v < prev:
            total -= v
        else:
            total += v
            prev = v
    return total


def gcd_list(xs):
    """GCD of a non-empty list of non-negative ints; ValueError on empty."""
    if not xs:
        raise ValueError("empty")
    g = 0
    for x in xs:
        a, b = g, x
        while b:
            a, b = b, a % b
        g = a
    return g


def lcm(a, b):
    """Least common multiple of abs(a) and abs(b); 0 if either is 0."""
    if a == 0 or b == 0:
        return 0
    x, y = abs(a), abs(b)
    g = x
    h = y
    while h:
        g, h = h, g % h
    return x // g * y


def clamp(x, lo, hi):
    """Clamp x into [lo, hi]; ValueError if lo > hi."""
    if lo > hi:
        raise ValueError("empty interval")
    return lo if x < lo else hi if x > hi else x


def saturating_add(a, b, lo, hi):
    """a + b clamped into [lo, hi]."""
    return clamp(a + b, lo, hi)


def fib(n):
    """n-th Fibonacci number, fib(0)=0, fib(1)=1; ValueError for n < 0."""
    if n < 0:
        raise ValueError("negative")
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def prime_factors(n):
    """Sorted prime factors of n with multiplicity; [] for n < 2."""
    out = []
    d = 2
    while d * d <= n:
        while n % d == 0:
            out.append(d)
            n //= d
        d += 1
    if n > 1:
        out.append(n)
    return out


def to_base(n, base):
    """Digits of non-negative n in the given base (2..36), as a string."""
    if base < 2 or base > 36:
        raise ValueError("bad base")
    if n < 0:
        raise ValueError("negative")
    if n == 0:
        return "0"
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    out = []
    while n:
        out.append(digits[n % base])
        n //= base
    return "".join(reversed(out))
