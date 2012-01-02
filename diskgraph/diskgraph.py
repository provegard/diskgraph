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
from sysinfo import *
from sgraph import SimpleGraph

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

if __name__ == "__main__":
    import sys
    print "Run dgmain.py instead!\n"
    sys.exit(1)

