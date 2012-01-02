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
from sysinfo import SysInfo

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

def main(fn):
    dg = DiskGraph(SysInfo())
    print "Graph contains %d entities." % (dg.order - 1, )
    g = dg.todot()
    print "Writing PNG image to %s..." % fn
    g.write_png(fn)
    print "All done!"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "Usage: %s <output file>" % sys.argv[0]
        sys.exit(1)
    main(sys.argv[1])

