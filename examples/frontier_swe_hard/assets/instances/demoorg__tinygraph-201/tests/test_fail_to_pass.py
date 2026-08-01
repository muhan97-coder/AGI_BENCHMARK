"""FAIL_TO_PASS for demoorg__tinygraph-201 (sealed: copied in by the harness)."""

import pytest

from tinygraph import CycleError, Graph, topo_sort


def test_cycle_raises_cycle_error():
    g = Graph()
    g.add_edge("a", "b")
    g.add_edge("b", "a")
    with pytest.raises(CycleError):
        topo_sort(g)


def test_cycle_error_is_a_value_error():
    assert issubclass(CycleError, ValueError)


def test_cycle_error_names_the_unordered_nodes():
    g = Graph()
    g.add_edge("a", "b")
    g.add_edge("b", "a")
    g.add_edge("c", "a")
    with pytest.raises(CycleError) as excinfo:
        topo_sort(g)
    assert sorted(excinfo.value.nodes) == ["a", "b"]
