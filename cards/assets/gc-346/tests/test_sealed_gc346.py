# Sealed acceptance tests for gc-346 (networkx: undirected simple_cycles).
# Do not edit: the grader overwrites the copy in the workspace with this file.

import networkx as nx


def canon(cycles):
    return sorted(sorted(c) for c in cycles)


def test_undirected_triangle():
    G = nx.Graph([(0, 1), (1, 2), (2, 0)])
    assert canon(nx.simple_cycles(G)) == [[0, 1, 2]]


def test_undirected_self_loop():
    G = nx.Graph()
    G.add_edge(0, 0)
    assert canon(nx.simple_cycles(G)) == [[0]]


def test_undirected_tree_has_no_cycles():
    G = nx.path_graph(5)
    assert list(nx.simple_cycles(G)) == []


def test_complete_graph_k4_cycle_count():
    K4 = nx.complete_graph(4)
    cycles = list(nx.simple_cycles(K4))
    assert len(cycles) == 7  # 4 triangles + 3 four-cycles


def test_length_bound_limits_cycle_size():
    K4 = nx.complete_graph(4)
    bounded = list(nx.simple_cycles(K4, length_bound=3))
    assert len(bounded) == 4
    assert all(len(c) <= 3 for c in bounded)


def test_directed_behavior_unchanged():
    D = nx.DiGraph([(0, 1), (1, 0), (1, 2), (2, 1)])
    assert canon(nx.simple_cycles(D)) == [[0, 1], [1, 2]]
