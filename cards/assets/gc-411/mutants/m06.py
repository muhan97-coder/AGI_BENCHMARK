"""siunits: SI prefix arithmetic for single-letter base units (sealed)."""
import re

PREFIXES = {"G": 1e9, "M": 1e6, "k": 1e3, "": 1.0, "c": 1e-2, "m": 1e-3,
            "u": 1e-6, "n": 1e-9}
BASE_UNITS = ("m", "g", "s", "A")

_NUM = re.compile(r"\s*([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)"
                  r"\s*([A-Za-z]*)\s*$")

_FORMAT_ORDER = ("G", "M", "k", "", "m", "u", "n")


def parse_quantity(text):
    """Parse '12.5 km' -> (12.5, 'k', 'm'). Raises ValueError."""
    m = _NUM.match(text)
    if not m:
        raise ValueError(f"cannot parse quantity: {text!r}")
    value = float(m.group(1))
    sym = m.group(2)
    if not sym:
        raise ValueError("missing unit")
    unit = sym[-1]
    prefix = sym[:-1]
    if unit not in BASE_UNITS:
        raise ValueError(f"unknown base unit: {unit!r}")
    if prefix not in PREFIXES:
        raise ValueError(f"unknown prefix: {prefix!r}")
    return (value, prefix, unit)


def to_base(value, prefix):
    """Scale a prefixed value to the base unit."""
    return value * PREFIXES[prefix]


def convert(value, from_prefix, to_prefix):
    """Re-express value from one prefix in another."""
    return value * PREFIXES[to_prefix] / PREFIXES[from_prefix]


def format_quantity(value, unit):
    """Engineering formatting: pick the prefix putting the mantissa in
    [1, 1000). Zero formats as '0 <unit>'. Out-of-range values fall back
    to plain formatting in the base unit."""
    if value == 0:
        return f"0 {unit}"
    for p in _FORMAT_ORDER:
        scaled = value / PREFIXES[p]
        if 1 <= abs(scaled) < 1000:
            return f"{round(scaled, 6):g} {p}{unit}"
    return f"{value:g} {unit}"
