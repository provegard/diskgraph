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

from diskgraph import DiskGraph
from sysinfo import SysInfo
import pydot

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

def main(fn):
    dg = DiskGraph(SysInfo())
    edges = [(nn(h), nn(t)) for (h, t) in dg.visitEdges(dg.root)]
    graph = pydot.graph_from_edges(edges, directed=True)
    graph.write_png(fn)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "Usage: %s <output file>" % sys.argv[0]
        sys.exit(1)
    main(sys.argv[1])

