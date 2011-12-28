# -*- coding: utf-8 -*-
# Copyright (c) 2011, Per Rovegård <per@rovegard.se>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. Neither the name of the authors nor the names of its contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

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

