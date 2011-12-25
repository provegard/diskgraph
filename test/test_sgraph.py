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
        headfinder = lambda x: [2] if x == root else []
        graph = SimpleGraph(headfinder, root)
        self.assertEqual(2, graph.order)

    def test_that_graph_with_loop_can_be_built(self):
        root = 1
        headfinder = lambda x: [2] if x == root else [root]
        graph = SimpleGraph(headfinder, root)
        self.assertEqual(2, graph.order)

    def test_that_headsFor_handles_loop_case(self):
        root = 1
        headfinder = lambda x: [2] if x == root else [root]
        graph = SimpleGraph(headfinder, root)
        self.assertEqual([root], graph.headsFor(2))

    def test_that_heads_for_vertex_can_be_queried(self):
        root = 1
        headfinder = lambda x: [2] if x == root else []
        graph = SimpleGraph(headfinder, root)
        heads = graph.headsFor(1)
        self.assertEqual([2], heads)

    def test_that_tails_for_vertex_can_be_queried(self):
        root = 1
        headfinder = lambda x: [2] if x == root else []
        graph = SimpleGraph(headfinder, root)
        heads = graph.tailsFor(2)
        self.assertEqual([1], heads)

    def test_that_vertices_can_be_visited(self):
        root = 1
        headfinder = lambda x: [2] if x == root else []
        graph = SimpleGraph(headfinder, root)
        visited = list(graph.visit(root))
        self.assertEqual([1, 2], visited)

    def test_that_loops_are_handled_when_visiting(self):
        root = 1
        headfinder = lambda x: [2] if x == root else [root]
        graph = SimpleGraph(headfinder, root)
        visited = list(graph.visit(root))
        self.assertEqual([1, 2], visited)

    def test_that_heads_are_visited_ltr(self):
        root = 1
        headfinder = lambda x: [2, 3] if x == root else []
        graph = SimpleGraph(headfinder, root)
        visited = list(graph.visit(root))
        self.assertEqual([root, 2, 3], visited)

    def test_that_edges_can_be_visited_for_simple_graph(self):
        root = 1
        headfinder = lambda x: [2] if x == root else []
        graph = SimpleGraph(headfinder, root)
        visited = list(graph.visitEdges(root))
        self.assertEqual([(root, 2)], visited)

    def test_that_edges_can_be_visited_for_graph_with_loop(self):
        root = 1
        headfinder = lambda x: [2] if x == root else [root]
        graph = SimpleGraph(headfinder, root)
        visited = list(graph.visitEdges(root))
        self.assertEqual([(root, 2), (2, root)], visited)

