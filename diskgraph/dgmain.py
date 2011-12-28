#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Main script for diskgraph, a utility that creates a graph of disks, partitions, etc.
present on the current Linux server.

This script must be run as root, since the LVM commands require that.

Pydot (http://code.google.com/p/pydot) is used to create a PNG image of the graph.

Created and tested by Per Rovegård on a server running Ubuntu 11.04 with Python 2.7.1.

Distributed under the 3-Clause BSD license (http://opensource.org/licenses/BSD-3-Clause,
and LICENSE file).
"""

__author__ = "Per Rovegård"
__version__ = "1.0"
__license__ = "BSD-3-Clause"

import os, sys

if __name__ == "__main__":
    if os.geteuid() != 0:
        sys.exit("Only root can run this script.\n")

from diskgraph import DiskGraph, FreeSpace
from sysinfo import *
import pydot

colors = {
    Partition: lambda p: "gold" if p.is_disk() else "chartreuse1",
    RaidArray: "cadetblue",
    LvmPhysicalVolume: "chocolate",
    LvmVolumeGroup: "coral",
    LvmLogicalVolume: "mediumorchid1",
    FreeSpace: ("red", "white"),
    MountedFileSystem: ("navy", "white"),
}

suffixes = ["B", "kB", "MB", "GB", "TB", "PB"]
def tosize(bytesize):
    size = float(bytesize)
    idx = 0
    while size > 1024:
        size /= 1024
        idx += 1
    return "%.2f%s" % (size, suffixes[idx])

def nn(node):
    s = "%s\\n%s" % (node.__class__.__name__, node.name)
    if hasattr(node, "byte_size"):
        s += "\\n%s" % (tosize(node.byte_size), )
    return s

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

def main(fn):
    dg = DiskGraph(SysInfo())
    g = pydot.Dot("diskgraph", graph_type="digraph")
    nodes = {}
    for (tail, head) in dg.visitEdges(dg.root):
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
    g.write_png(fn)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "Usage: %s <output file>" % sys.argv[0]
        sys.exit(1)
    main(sys.argv[1])

