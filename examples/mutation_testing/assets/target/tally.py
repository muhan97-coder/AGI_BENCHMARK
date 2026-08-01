"""Tiny normalise-and-count helpers (mutation target for ex-mutation_testing).

Deliberately small: five sealed single-site mutants are enough to show the
grading shape. Inputs are lists of strings; keys are compared after
normalisation.
"""
from __future__ import annotations


def normalize(name: str) -> str:
    """Strip surrounding whitespace, then lowercase."""
    return name.strip().lower()


def tally(items: list[str]) -> dict[str, int]:
    """Count items after normalisation, in first-seen key order."""
    counts: dict[str, int] = {}
    for item in items:
        key = normalize(item)
        counts[key] = counts.get(key, 0) + 1
    return counts


def top_k(items: list[str], k: int) -> list[str]:
    """The k most frequent normalised items; ties broken alphabetically.

    k == 0 returns the empty list; k < 0 raises ValueError.
    """
    if k < 0:
        raise ValueError("k must be >= 0")
    ordered = sorted(tally(items).items(), key=lambda kv: (-kv[1], kv[0]))
    return [name for name, _ in ordered[:k]]


def share(items: list[str], name: str) -> float:
    """Fraction of items equal to name after normalisation; 0.0 on empty input."""
    if not items:
        return 0.0
    return tally(items).get(normalize(name), 0) / len(items)
