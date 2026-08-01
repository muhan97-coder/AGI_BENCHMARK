"""A tiny key=value configuration format (ex-campaign reference solution).

Stage 1 shipped `parse`. Stage 2 added `render` and `merge` without touching
`parse`, which is what keeps the stage-1 suite green.
"""
from __future__ import annotations


def parse(text: str) -> dict[str, str]:
    """Parse `key=value` lines; blank and `#` lines are ignored."""
    result: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"line without '=': {raw!r}")
        key, _, value = line.partition("=")
        key = key.strip()
        if not key:
            raise ValueError(f"empty key: {raw!r}")
        result[key] = value.strip()
    return result


def render(mapping: dict[str, str]) -> str:
    """Emit `key=value` lines sorted by key; the inverse of `parse`."""
    return "".join(f"{key}={mapping[key]}\n" for key in sorted(mapping))


def merge(a: dict[str, str], b: dict[str, str]) -> dict[str, str]:
    """Return a new mapping where `b` wins on conflicting keys."""
    merged = dict(a)
    merged.update(b)
    return merged
