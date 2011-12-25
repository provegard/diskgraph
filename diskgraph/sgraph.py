
__all__ = [
    "SimpleGraph"
]

class SimpleGraph(object):
    """
    Represents a cyclic, directed graph. Keeps track of some rudimentary graph
    properties and allow the graph vertices to be visited using a depth-first
    search algorithm.
    """
    def __init__(self, headfinder, root):
        self._headfinder = headfinder
        self._graph = {}
        self._build(root)
        self._root = root

    @property
    def root(self):
        return self._root

    @property
    def order(self):
        return len(self._graph.keys())

    def _build(self, root):
        self._graph[root] = []
        for v in self.visit(root):
            heads = self._headfinder(v)
            for h in heads:
                self._graph[v].append(h)
                if not h in self._graph.keys():
                    # not seen this one before
                    self._graph[h] = []

    def visit(self, start):
        """Visit the graph starting at the given vertex. This is a generator
        function that will return each visited vertex in turn. The graph is 
        visited using the DFS algorithm and heads are visited left-to-right
        (i.e. first-to-last).
        """
        visited = []
        vertices = [start]
        while vertices:
            v = vertices.pop(0)
            visited.append(v)
            yield v
            heads = [h for h in self.headsFor(v) if not h in visited]
            vertices = heads + vertices

    def visitEdges(self, start):
        """Visit the edges in the graph starting at the given vertex. This is
        a generated function that will return each visited edge in turn.
        """
        visited = []
        queue = [(None, start)]
        while queue:
            e = queue.pop(0)
            if e[0]:
                yield e
            if e[1] in visited:
                continue
            visited.append(e[1])
            edges = [(e[1], h) for h in self.headsFor(e[1])]
            queue = edges + queue

    def headsFor(self, vertex):
        """Return a list of the heads of the given vertex, i.e. the vertices (if
        any) that are on the opposite end of any edges originating in the given
        vertex."""
        return self._graph.get(vertex, [])

    def tailsFor(self, vertex):
        """Return a list of the tails of the given vertex, i.e. the vertices (if
        any) that are on the opposite end of any edges terminating in the given
        vertex."""
        return [v for v in self._graph.keys() if vertex in self._graph[v]]

