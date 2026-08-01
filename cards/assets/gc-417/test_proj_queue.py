"""Sealed suite for gc-417 stage 2 (read-only). Defect ids Q01..Q04."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.getcwd(), "work", "gc-417", "pkgs"))

import proj_queue as pq  # noqa: E402


def test_push_pop_single():
    q = pq.new_queue()
    pq.push(q, "only", 3)
    assert pq.pop(q) == "only"


def test_pop_empty_raises():
    with pytest.raises(IndexError):
        pq.pop(pq.new_queue())


def test_peek_empty_raises():
    with pytest.raises(IndexError):
        pq.peek(pq.new_queue())


def test_qsize_new_queue():
    assert pq.qsize(pq.new_queue()) == 0


def test_Q01_lowest_priority_first():
    q = pq.new_queue()
    pq.push(q, "low-urgency", 5)
    pq.push(q, "urgent", 1)
    pq.push(q, "mid", 3)
    assert pq.pop(q) == "urgent"
    assert pq.pop(q) == "mid"
    assert pq.pop(q) == "low-urgency"


def test_Q02_fifo_among_equal_priorities():
    q = pq.new_queue()
    pq.push(q, "first", 1)
    pq.push(q, "second", 1)
    pq.push(q, "third", 1)
    assert pq.pop(q) == "first"
    assert pq.pop(q) == "second"
    assert pq.pop(q) == "third"


def test_Q03_peek_is_nondestructive():
    q = pq.new_queue()
    pq.push(q, "x", 2)
    assert pq.peek(q) == "x"
    assert pq.qsize(q) == 1
    assert pq.pop(q) == "x"


def test_Q04_qsize_tracks_pops():
    q = pq.new_queue()
    pq.push(q, "a", 1)
    pq.push(q, "b", 2)
    pq.pop(q)
    assert pq.qsize(q) == 1
    pq.pop(q)
    assert pq.qsize(q) == 0


def test_unhashable_noncomparable_items():
    q = pq.new_queue()
    pq.push(q, {"payload": 1}, 2)
    pq.push(q, {"payload": 2}, 2)
    assert pq.pop(q) == {"payload": 1}


def test_interleaved_operations():
    q = pq.new_queue()
    pq.push(q, "a", 4)
    assert pq.pop(q) == "a"
    pq.push(q, "b", 9)
    assert pq.peek(q) == "b"
    assert pq.pop(q) == "b"
    with pytest.raises(IndexError):
        pq.pop(q)
