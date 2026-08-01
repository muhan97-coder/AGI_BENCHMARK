"""Sealed acceptance suite for gc-406 (taskgraph). Run from benchmark repo root."""
import importlib.util
import os

import pytest

_PATH = os.path.join(os.getcwd(), "workspace", "gc-406", "taskgraph.py")
_spec = importlib.util.spec_from_file_location("taskgraph_under_test", _PATH)
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)


def T(**kw):
    return {k: {"deps": v[0], "duration": v[1]} for k, v in kw.items()}


PIPELINE = T(
    build=(["fetch"], 4), fetch=([], 2), lint=(["fetch"], 1),
    test=(["build", "lint"], 3), pack=(["test"], 1),
)


def test_empty():
    assert M.order({}) == []
    assert M.waves({}) == []
    assert M.critical_path({}) == (0, [])


def test_single_task():
    t = T(only=([], 5))
    assert M.order(t) == ["only"]
    assert M.waves(t) == [["only"]]
    assert M.critical_path(t) == (5, ["only"])


def test_order_pipeline():
    assert M.order(PIPELINE) == ["fetch", "build", "lint", "test", "pack"]


def test_order_lexicographic_tiebreak():
    t = T(c=([], 1), a=([], 1), b=([], 1))
    assert M.order(t) == ["a", "b", "c"]


def test_order_tiebreak_after_release():
    # z has no deps but sorts last; releasing m unlocks a which sorts first
    t = T(m=([], 1), a=(["m"], 1), z=([], 1))
    assert M.order(t) == ["m", "a", "z"]


def test_order_is_valid_topologically():
    got = M.order(PIPELINE)
    pos = {n: i for i, n in enumerate(got)}
    for name, meta in PIPELINE.items():
        for d in meta["deps"]:
            assert pos[d] < pos[name]


def test_waves_pipeline():
    assert M.waves(PIPELINE) == [["fetch"], ["build", "lint"], ["test"], ["pack"]]


def test_waves_sorted_inside():
    t = T(b=([], 1), a=([], 1), d=(["a", "b"], 1), c=(["a"], 1))
    assert M.waves(t) == [["a", "b"], ["c", "d"]]


def test_critical_path_pipeline():
    assert M.critical_path(PIPELINE) == (10, ["fetch", "build", "test", "pack"])


def test_critical_path_tiebreak_lexicographic():
    # two chains with equal total 3: a->x and b->x ; a-chain wins
    t = T(a=([], 1), b=([], 1), x=(["a", "b"], 2))
    assert M.critical_path(t) == (3, ["a", "x"])


def test_critical_path_single_heavy_node():
    t = T(light1=([], 1), heavy=([], 10), light2=(["light1"], 2))
    assert M.critical_path(t) == (10, ["heavy"])


def test_critical_path_execution_order():
    total, path = M.critical_path(PIPELINE)
    idx = {n: i for i, n in enumerate(M.order(PIPELINE))}
    assert path == sorted(path, key=lambda n: idx[n])
    assert total == sum(PIPELINE[n]["duration"] for n in path)


def test_duplicate_deps_deduped():
    t = T(a=([], 1), b=(["a", "a", "a"], 1))
    assert M.order(t) == ["a", "b"]
    assert M.waves(t) == [["a"], ["b"]]


def test_unknown_dep_raises_valueerror():
    t = T(a=(["ghost"], 1))
    for fn in (M.order, M.waves, M.critical_path):
        with pytest.raises(ValueError):
            fn(t)


def test_bad_duration_raises_valueerror():
    for bad in [0, -1, "2", 1.5, None, True]:
        t = {"a": {"deps": [], "duration": bad}}
        with pytest.raises(ValueError):
            M.order(t)


def test_self_cycle():
    t = T(a=(["a"], 1))
    with pytest.raises(M.CycleError) as ei:
        M.order(t)
    assert ei.value.cycle == ["a"]


def test_two_cycle_normalized():
    t = T(b=(["a"], 1), a=(["b"], 1))
    with pytest.raises(M.CycleError) as ei:
        M.order(t)
    assert ei.value.cycle == ["a", "b"]


def test_three_cycle_direction_and_normalization():
    # a depends on b, b on c, c on a: cycle [a, b, c]
    t = T(a=(["b"], 1), b=(["c"], 1), c=(["a"], 1))
    with pytest.raises(M.CycleError) as ei:
        M.waves(t)
    cyc = ei.value.cycle
    assert cyc == ["a", "b", "c"]
    # verify it is a real dependency cycle in the stated direction
    for i, name in enumerate(cyc):
        nxt = cyc[(i + 1) % len(cyc)]
        assert nxt in t[name]["deps"]


def test_cycle_in_larger_graph():
    t = T(ok1=([], 1), ok2=(["ok1"], 1),
          p=(["q"], 1), q=(["r"], 1), r=(["p"], 1))
    with pytest.raises(M.CycleError) as ei:
        M.critical_path(t)
    cyc = ei.value.cycle
    assert cyc[0] == min(cyc)
    assert len(cyc) == len(set(cyc))
    for i, name in enumerate(cyc):
        assert cyc[(i + 1) % len(cyc)] in t[name]["deps"]


def test_cycleerror_is_exception_subclass():
    assert issubclass(M.CycleError, Exception)


def test_validation_before_cycle_detection():
    t = {"a": {"deps": ["a"], "duration": 0}}
    with pytest.raises(ValueError):
        M.order(t)


def test_wide_graph_determinism():
    import random
    names = [f"n{i:02d}" for i in range(30)]
    rng = random.Random(1234)
    t = {}
    for i, n in enumerate(names):
        deps = [names[j] for j in range(i) if rng.random() < 0.15]
        t[n] = {"deps": deps, "duration": (i % 7) + 1}
    o1, o2 = M.order(t), M.order(t)
    assert o1 == o2
    pos = {n: i for i, n in enumerate(o1)}
    for n, meta in t.items():
        for d in meta["deps"]:
            assert pos[d] < pos[n]
    w = M.waves(t)
    assert sorted(x for wave in w for x in wave) == sorted(names)
    total, path = M.critical_path(t)
    assert total == sum(t[n]["duration"] for n in path)
    for x, y in zip(path, path[1:]):
        assert x in t[y]["deps"]
