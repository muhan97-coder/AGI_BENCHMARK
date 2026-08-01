"""Sealed stage-1 regression suite for gc-413 (read-only).

Test names carry the seeded-defect identities D01..D05.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.getcwd(), "work", "gc-413"))

import textindex  # noqa: E402


def test_basic_tokenize():
    assert textindex.tokenize("red fox") == ["red", "fox"]


def test_basic_index_and_lookup():
    idx = textindex.build_index(["apple pie", "banana apple"])
    assert textindex.lookup(idx, "apple") == [0, 1]
    assert textindex.lookup(idx, "banana") == [1]


def test_keys_sorted_and_aligned():
    idx = textindex.build_index(["b a", "c a"])
    assert idx["keys"] == ["a", "b", "c"]
    assert idx["postings"] == [[0, 1], [0], [1]]


def test_D01_tokenize_lowercases():
    assert textindex.tokenize("Apple APPLE") == ["apple", "apple"]
    idx = textindex.build_index(["Apple"])
    assert textindex.lookup(idx, "apple") == [0]


def test_D02_postings_deduplicated():
    idx = textindex.build_index(["cat cat cat"])
    assert textindex.lookup(idx, "cat") == [0]


def test_D03_no_empty_tokens():
    assert textindex.tokenize("...dog!!!") == ["dog"]
    idx = textindex.build_index(["...dog!!!"])
    assert "" not in idx["keys"]


def test_D04_missing_lookup_returns_empty_list():
    idx = textindex.build_index(["something"])
    assert textindex.lookup(idx, "absent") == []


def test_D05_digits_kept_in_tokens():
    assert textindex.tokenize("log4j v2") == ["log4j", "v2"]
    idx = textindex.build_index(["error log4j"])
    assert textindex.lookup(idx, "log4j") == [0]


def test_empty_docs_list():
    assert textindex.build_index([]) == {"keys": [], "postings": []}


def test_doc_with_no_tokens():
    idx = textindex.build_index(["!!!", "ok"])
    assert idx["keys"] == ["ok"]
    assert textindex.lookup(idx, "ok") == [1]


def test_mixed_case_merge():
    idx = textindex.build_index(["Dog dog", "DOG"])
    assert textindex.lookup(idx, "dog") == [0, 1]
