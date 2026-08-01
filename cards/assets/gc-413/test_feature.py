"""Sealed stage-3 feature suite for gc-413 (read-only)."""
import copy
import os
import sys

sys.path.insert(0, os.path.join(os.getcwd(), "work", "gc-413"))

import textindex  # noqa: E402

DOCS = ["car card care", "cargo bay", "dog cart", "care package", "zebra"]


def _idx():
    return textindex.build_index(DOCS)


def test_prefix_basic():
    assert textindex.prefix_search(_idx(), "car") == [0, 1, 2, 3]


def test_prefix_exact_token_only():
    assert textindex.prefix_search(_idx(), "card") == [0]


def test_prefix_no_match():
    assert textindex.prefix_search(_idx(), "quux") == []


def test_prefix_single_letter():
    assert textindex.prefix_search(_idx(), "z") == [4]


def test_prefix_empty_returns_all_doc_ids():
    assert textindex.prefix_search(_idx(), "") == [0, 1, 2, 3, 4]


def test_prefix_dedupes_across_tokens():
    idx = textindex.build_index(["care card", "care"])
    assert textindex.prefix_search(idx, "car") == [0, 1]


def test_prefix_does_not_mutate_index():
    idx = _idx()
    before = copy.deepcopy(idx)
    textindex.prefix_search(idx, "car")
    assert idx == before


def test_prefix_longer_than_tokens():
    assert textindex.prefix_search(_idx(), "cardboard") == []
