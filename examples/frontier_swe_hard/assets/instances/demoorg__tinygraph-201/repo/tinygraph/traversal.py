"""Topological ordering (Kahn's algorithm)."""


def topo_sort(graph):
    """Return the nodes of *graph* in dependency order."""
    degree = graph.in_degree()
    ready = sorted(node for node, d in degree.items() if d == 0)
    order = []
    while ready:
        node = ready.pop(0)
        order.append(node)
        for nxt in graph.successors(node):
            degree[nxt] -= 1
            if degree[nxt] == 0:
                ready.append(nxt)
        ready.sort()
    return order
