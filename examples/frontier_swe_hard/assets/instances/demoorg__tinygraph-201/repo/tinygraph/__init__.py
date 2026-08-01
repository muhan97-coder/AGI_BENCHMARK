"""tinygraph -- a miniature DAG toolkit (demo instance repo)."""

from .graph import Graph
from .traversal import topo_sort

__all__ = ["Graph", "topo_sort"]
__version__ = "3.1.0"
