"""tinyunits -- a miniature length converter (demo instance repo)."""

__all__ = ["convert", "parse_quantity"]
__version__ = "2.0.1"

_TO_METRES = {
    "m": 1.0,
    "km": 1000.0,
    "cm": 0.01,
    "mi": 1609.0,
    "ft": 0.3048,
    "in": 0.0254,
}


def convert(value, frm, to):
    """Convert *value* from unit *frm* to unit *to*."""
    try:
        factor = _TO_METRES[frm] / _TO_METRES[to]
    except KeyError as exc:
        raise ValueError(f"unknown unit: {exc.args[0]}") from None
    return value * factor


def parse_quantity(text):
    """Parse '3 km' into (3.0, 'km')."""
    parts = text.strip().split()
    if len(parts) != 2:
        raise ValueError(f"cannot parse quantity: {text!r}")
    value, unit = parts
    if unit not in _TO_METRES:
        raise ValueError(f"unknown unit: {unit}")
    return float(value), unit
