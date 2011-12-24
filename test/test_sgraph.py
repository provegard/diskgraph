import unittest
from diskgraph.sgraph import *

class TestSimpleGraph(unittest.TestCase):

    def test_that_graph_is_created_with_head_finder_and_root(self):
        root = 1
        headfinder = lambda x: []
        self.assertIsInstance(SimpleGraph(headfinder, root), SimpleGraph)

    def test_that_graph_exposes_root(self):
        root = 1
        g = SimpleGraph(lambda x: [], root)
        self.assertEquals(root, g.root)

    def test_that_graph_with_single_vertex_can_be_built(self):
        root = 1
        headfinder = lambda x: []
        graph = SimpleGraph(headfinder, root)
        self.assertEqual(1, graph.order)

    def test_that_graph_with_two_vertices_can_be_built(self):
        root = 1
        headfinder = lambda x: [2] if x == 1 else []
        graph = SimpleGraph(headfinder, root)
        self.assertEqual(2, graph.order)

    def test_that_graph_with_loop_can_be_built(self):
        root = 1
        headfinder = lambda x: [2] if x == 1 else [1]
        graph = SimpleGraph(headfinder, root)
        self.assertEqual(2, graph.order)

    def test_that_heads_for_vertex_can_be_queried(self):
        root = 1
        headfinder = lambda x: [2] if x == 1 else []
        graph = SimpleGraph(headfinder, root)
        heads = graph.headsFor(1)
        self.assertListEqual([2], heads)

    def test_that_tails_for_vertex_can_be_queried(self):
        root = 1
        headfinder = lambda x: [2] if x == 1 else []
        graph = SimpleGraph(headfinder, root)
        heads = graph.tailsFor(2)
        self.assertListEqual([1], heads)

    def test_that_vertices_can_be_visited(self):
        root = 1
        headfinder = lambda x: [2] if x == 1 else []
        graph = SimpleGraph(headfinder, root)
        #visited = []
        #graph.visit(root, lambda x: visited.append(x))
        visited = list(graph.visit(root))
        self.assertListEqual([1, 2], visited)

    def test_that_loops_are_handled_when_visiting(self):
        root = 1
        headfinder = lambda x: [2] if x == 1 else [1]
        graph = SimpleGraph(headfinder, root)
        #visited = []
        visited = list(graph.visit(root))
        self.assertListEqual([1, 2], visited)

