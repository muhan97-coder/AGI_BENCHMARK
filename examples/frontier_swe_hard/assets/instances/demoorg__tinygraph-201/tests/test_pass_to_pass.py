"""PASS_TO_PASS for demoorg__tinygraph-201 (sealed: copied in by the harness)."""

from tinygraph import Graph, topo_sort


def test_linear_chain():
    g = Graph()
    g.add_edge("a", "b")
    g.add_edge("b", "c")
    assert topo_sort(g) == ["a", "b", "c"]


def test_diamond_respects_every_edge():
    g = Graph()
    for src, dst in [("a", "b"), ("a", "c"), ("b", "d"), ("c", "d")]:
        g.add_edge(src, dst)
    order = topo_sort(g)
    assert len(order) == 4
    for src, dst in [("a", "b"), ("a", "c"), ("b", "d"), ("c", "d")]:
        assert order.index(src) < order.index(dst)


def test_empty_graph():
    assert topo_sort(Graph()) == []


def test_single_isolated_node():
    g = Graph()
    g.add_node("a")
    assert topo_sort(g) == ["a"]


def test_add_edge_registers_both_endpoints():
    g = Graph()
    g.add_edge("a", "b")
    assert sorted(g.nodes) == ["a", "b"]
    assert g.successors("a") == ["b"]
