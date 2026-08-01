# topo_sort() silently returns a truncated order for cyclic graphs

Reported against `tinygraph` (demo instance repo).

```python
>>> from tinygraph import Graph, topo_sort
>>> g = Graph()
>>> g.add_edge("a", "b")
>>> g.add_edge("b", "a")
>>> topo_sort(g)
[]
```

A graph with a cycle has no topological order, but `topo_sort()` returns
whatever prefix it managed to peel off and the caller has no way to tell that
from a legitimately short order. Two callers in our pipeline have shipped
partial build plans because of this.

`topo_sort()` should raise instead. The exception needs to be:

* a dedicated `CycleError`, importable as `from tinygraph import CycleError`;
* a subclass of `ValueError`, so existing `except ValueError` handlers around
  graph loading keep working;
* carrying the nodes that could not be ordered on a `.nodes` attribute, so the
  caller can report *which* cycle it hit -- a count is useless in a build log.

Acyclic behaviour must not change.
