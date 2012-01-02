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
__version__ = "1.1"
__license__ = "BSD-3-Clause"

import os, sys
from check import checker
from diskgraph import DiskGraph

if not checker.has_partitions():
    sys.exit("The file /proc/partitions must exist.\n")

if not checker.has_df_command():
    print "No df command found - mounted file systems won't be included."

if not checker.has_mdstat():
    print "No /proc/mdstat file - software RAID arrays won't be included."

if not checker.has_swaps():
    print "No /proc/swaps file - swap areas won't be included."

if not checker.has_lvm_commands():
    print "No LVM commands founds - LVM entities won't be included."

# Currently, only the LVM commands require root privileges.
if checker.has_lvm_commands() and __name__ == "__main__":
    if os.geteuid() != 0:
        sys.exit("Only root can run this script, because the LVM commands need that.\n")

from sysinfo import *
import pydot

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
    print "Graph contains %d entities." % (dg.order - 1, )
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

    print "Writing PNG image to %s..." % fn
    g.write_png(fn)
    print "All done!"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "Usage: %s <output file>" % sys.argv[0]
        sys.exit(1)
    main(sys.argv[1])

