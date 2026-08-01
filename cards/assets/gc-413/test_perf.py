"""Sealed stage-2 comparison-budget suite for gc-413 (read-only).

Counts rich comparisons on instrumented lookup keys. A linear scan over
the 4096-token index measures around 100k comparisons for the battery;
the sealed budget is 2500.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.getcwd(), "work", "gc-413"))

import textindex  # noqa: E402

COUNTER = {"n": 0}


class CountingStr(str):
    def __lt__(self, other):
        COUNTER["n"] += 1
        return str.__lt__(self, other)

    def __le__(self, other):
        COUNTER["n"] += 1
        return str.__le__(self, other)

    def __gt__(self, other):
        COUNTER["n"] += 1
        return str.__gt__(self, other)

    def __ge__(self, other):
        COUNTER["n"] += 1
        return str.__ge__(self, other)

    def __eq__(self, other):
        COUNTER["n"] += 1
        return str.__eq__(self, other)

    def __ne__(self, other):
        COUNTER["n"] += 1
        return str.__ne__(self, other)

    __hash__ = str.__hash__


def _build():
    docs = [f"tok{i:05d}" for i in range(4096)]
    return textindex.build_index(docs)


def test_lookup_correct_with_instrumented_keys():
    idx = _build()
    assert textindex.lookup(idx, CountingStr("tok00000")) == [0]
    assert textindex.lookup(idx, CountingStr("tok04095")) == [4095]
    assert textindex.lookup(idx, CountingStr("tok02048")) == [2048]
    assert textindex.lookup(idx, CountingStr("zzz")) == []


def test_comparison_budget_hits():
    idx = _build()
    COUNTER["n"] = 0
    for i in range(0, 4096, 128):
        assert textindex.lookup(idx, CountingStr(f"tok{i:05d}")) == [i]
    assert COUNTER["n"] <= 1700, f"used {COUNTER['n']} comparisons for 32 hits"


def test_comparison_budget_mixed():
    idx = _build()
    COUNTER["n"] = 0
    for i in range(9):
        textindex.lookup(idx, CountingStr(f"tok{i * 400:05d}"))
    for miss in ("aaa", "tok99999", "mid", "zz", "tok0", "toz", "t", "u", "v"):
        assert textindex.lookup(idx, CountingStr(miss)) == []
    assert COUNTER["n"] <= 800, f"used {COUNTER['n']} comparisons for 18 lookups"
