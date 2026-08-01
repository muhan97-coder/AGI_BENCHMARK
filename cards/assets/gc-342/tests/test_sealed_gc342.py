# Sealed acceptance tests for gc-342 (cachetools: TLRUCache).
# Do not edit: the grader overwrites the copy in the workspace with this file.

import pytest


def make_cache(maxsize, ttu, clock):
    from cachetools import TLRUCache

    return TLRUCache(maxsize=maxsize, ttu=ttu, timer=lambda: clock[0])


def test_items_expire_at_ttu_time():
    clock = [0]
    cache = make_cache(2, lambda key, value, now: now + 4, clock)
    cache["a"] = 1
    clock[0] = 1
    cache["b"] = 2
    assert len(cache) == 2 and "a" in cache and "b" in cache
    clock[0] = 4
    assert "a" not in cache
    assert "b" in cache
    clock[0] = 5
    assert "b" not in cache


def test_expired_key_raises_keyerror():
    clock = [0]
    cache = make_cache(2, lambda key, value, now: now + 4, clock)
    cache["a"] = 1
    clock[0] = 10
    with pytest.raises(KeyError):
        cache["a"]


def test_per_item_ttu_from_value():
    clock = [0]
    cache = make_cache(10, lambda key, value, now: now + value, clock)
    cache["x"] = 1
    cache["y"] = 10
    clock[0] = 2
    assert "x" not in cache
    assert "y" in cache


def test_non_positive_ttu_not_stored():
    clock = [0]
    cache = make_cache(10, lambda key, value, now: now, clock)
    cache["k"] = 9
    assert "k" not in cache
    assert len(cache) == 0


def test_lru_eviction_respects_recent_use():
    clock = [0]
    cache = make_cache(2, lambda key, value, now: now + 100, clock)
    cache["a"] = 1
    cache["b"] = 2
    assert cache["a"] == 1  # touch "a" so "b" becomes LRU
    cache["c"] = 3
    assert sorted(cache.keys()) == ["a", "c"]


def test_expire_method_exists():
    clock = [0]
    cache = make_cache(4, lambda key, value, now: now + 3, clock)
    cache["a"] = 1
    clock[0] = 5
    cache.expire()
    assert len(cache) == 0
