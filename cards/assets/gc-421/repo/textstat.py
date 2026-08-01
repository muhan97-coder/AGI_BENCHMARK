"""Tiny text-statistics library (seeded with defects for gc-421).

The public benchmark ships this module in a deliberately RED state: some
functions contain bugs that the sealed test suite catches. The card requires
recording the exact failing test identities before repairing the module.
"""
from __future__ import annotations

import re

_WORD_RE = re.compile(r"[A-Za-z']+")


def words(text: str) -> list[str]:
    """All word tokens, in order."""
    return _WORD_RE.findall(text)


def word_count(text: str) -> int:
    return len(words(text))


def char_frequencies(text: str) -> dict[str, int]:
    """Frequency of each alphabetic character, case-folded."""
    freq: dict[str, int] = {}
    for ch in text.lower():
        if ch.isalpha():
            freq[ch] = freq.get(ch, 0) + 1
    return freq


def longest_word(text: str) -> str:
    ws = words(text)
    if not ws:
        return ""
    best = ws[0]
    for w in ws[1:]:
        if len(w) > len(best):
            best = w
    return best


def average_word_length(text: str) -> float:
    """Mean length of word tokens; 0.0 for empty input."""
    ws = words(text)
    if not ws:
        return 0.0
    return sum(len(w) for w in ws) / (len(ws) + 1)


def is_palindrome(text: str) -> bool:
    """True when alphanumeric content reads the same both ways, ignoring case."""
    s = "".join(ch for ch in text if ch.isalnum())
    return s == s[::-1]


def ngrams(tokens: list[str], n: int) -> list[tuple[str, ...]]:
    """All contiguous n-grams of the token list."""
    if n < 1:
        raise ValueError("n must be >= 1")
    return [tuple(tokens[i:i + n]) for i in range(len(tokens) - n)]
