"""Graph container."""


class Graph:
    """A directed graph stored as an adjacency map."""

    def __init__(self):
        self._edges = {}

    def add_node(self, node):
        self._edges.setdefault(node, set())

    def add_edge(self, src, dst):
        self.add_node(src)
        self.add_node(dst)
        self._edges[src].add(dst)

    @property
    def nodes(self):
        return list(self._edges)

    def successors(self, node):
        return sorted(self._edges.get(node, ()))

    def in_degree(self):
        degree = {node: 0 for node in self._edges}
        for _src, dsts in self._edges.items():
            for dst in dsts:
                degree[dst] += 1
        return degree
