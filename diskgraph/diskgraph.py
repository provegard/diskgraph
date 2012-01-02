# -*- coding: utf-8 -*-
"""Module for creating a graph of entities discovered by the sysinfo module. Part of
the diskgraph utility.

Created and tested by Per Rovegård on a server running Ubuntu 11.04 with Python 2.7.1.

Distributed under the 3-Clause BSD license (http://opensource.org/licenses/BSD-3-Clause,
and LICENSE file).
"""

__author__ = "Per Rovegård"
__version__ = "1.1"
__license__ = "BSD-3-Clause"

import re
import pydot
from sysinfo import *
from sgraph import SimpleGraph

colors = {
    Partition: lambda p: "gold" if p.is_disk() else "chartreuse1",
    RaidArray: "cadetblue",
    LvmPhysicalVolume: "chocolate",
    LvmVolumeGroup: "coral",
    LvmLogicalVolume: "mediumorchid1",
    MountedFileSystem: ("navy", "white"),
    FreeSpace: ("red", "white"),
    SwapArea: "mediumslateblue",
}

def nn(node):
    return str(node).replace("\n", "\\n")

def get_color(node, c):
    if isinstance(c, basestring):
        return c
    else:
        return c(node)

def get_fillcolor(node):
    c = colors.get(node.__class__)
    if c:
        if isinstance(c, tuple):
            # (fillcolor, fontcolor)
            return get_color(node, c[0])
        return get_color(node, c)

def get_fontcolor(node):
    c = colors.get(node.__class__)
    if isinstance(c, tuple):
        # (fillcolor, fontcolor)
        return get_color(node, c[1])

def style_dict(node):
    d = {}
    fillc = get_fillcolor(node)
    if fillc:
        d["style"] = "filled"
        d["fillcolor"] = fillc
    fontc = get_fontcolor(node)
    if fontc:
        d["fontcolor"] = fontc
    d["label"] = nn(node)
    return d

class DiskGraph(SimpleGraph):
    def __init__(self, sysinfo):
        self.pool = sysinfo.objects
        SimpleGraph.__init__(self, self.headfinder, Root())

    def headfinder(self, v):
        return v.expand(self.pool)

    def dump(self):
        self._print(self.root, 0)

    def _print(self, v, level):
        print "%s%s" % ("  " * level, str(v))
        for head in self.headsFor(v):
            self._print(head, level + 1)

    def todot(self):
        g = pydot.Dot("diskgraph", graph_type="digraph")
        nodes = {}
        for (tail, head) in self.visitEdges(self.root):
            hnode = nodes.get(head)
            if not hnode:
                hnode = pydot.Node(str(len(nodes)), **style_dict(head))
                g.add_node(hnode)
                nodes[head] = hnode
            tnode = nodes.get(tail)
            if not tnode:
                tnode = pydot.Node(str(len(nodes)), **style_dict(tail))
                g.add_node(tnode)
                nodes[tail] = tnode
            g.add_edge(pydot.Edge(tnode, hnode))
        return g

if __name__ == "__main__":
    import sys
    print "Run dgmain.py instead!\n"
    sys.exit(1)

