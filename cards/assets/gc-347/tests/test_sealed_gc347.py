# Sealed acceptance tests for gc-347 (more-itertools: 9.0.0 API additions).
# Do not edit: the grader overwrites the copy in the workspace with this file.

import pytest
import more_itertools as mi


def as_lists(batches):
    return [list(b) for b in batches]


def test_batched_with_remainder():
    assert as_lists(mi.batched("ABCDEFG", 3)) == [
        ["A", "B", "C"],
        ["D", "E", "F"],
        ["G"],
    ]


def test_batched_exact_division():
    assert as_lists(mi.batched([1, 2, 3, 4], 2)) == [[1, 2], [3, 4]]


def test_constrained_batches_by_weight():
    items = [b"12345", b"123", b"12345678", b"1", b"1", b"12", b"1"]
    assert as_lists(mi.constrained_batches(items, 10)) == [
        [b"12345", b"123"],
        [b"12345678", b"1", b"1"],
        [b"12", b"1"],
    ]


def test_constrained_batches_max_count():
    items = [b"1", b"1", b"12", b"1"]
    assert as_lists(mi.constrained_batches(items, 10, max_count=2)) == [
        [b"1", b"1"],
        [b"12", b"1"],
    ]


def test_constrained_batches_strict_overflow_raises():
    with pytest.raises(ValueError):
        list(mi.constrained_batches([b"123456"], 5))


def test_polynomial_from_roots():
    assert list(mi.polynomial_from_roots([5, -4, 3])) == [1, -4, -17, 60]
    assert list(mi.polynomial_from_roots([2])) == [1, -2]


def test_sieve_primes():
    assert list(mi.sieve(30)) == [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
    assert list(mi.sieve(2)) == []


def test_existing_api_unchanged():
    assert as_lists(mi.chunked([1, 2, 3, 4, 5], 2)) == [[1, 2], [3, 4], [5]]
    assert mi.first([9, 8]) == 9
