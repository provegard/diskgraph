#!/usr/bin/python

import os, sys

if __name__ == "__main__":
    if os.geteuid() != 0:
        sys.exit("Only root can run this script.\n")

from subprocess import PIPE, Popen
import re, inspect
from sysinfo import *
from sgraph import SimpleGraph

suffixes = ["B", "kB", "MB", "GB", "TB", "PB"]
def tosize(bytesize):
    size = float(bytesize)
    idx = 0
    while size > 1024:
        size /= 1024
        idx += 1
    return "%.2f%s" % (size, suffixes[idx])

class Root(object):
    name = "root"

def is_disk(pp):
    return isinstance(pp, Partition) and re.match("^(h|s)d[a-z]$", pp.name)

def is_partition_for(disk, part):
    return is_disk(disk) and isinstance(part, Partition) and re.match("^%s\\d+$" % re.escape(disk.name), part.name)

hfs = {
    Root: lambda tail, p: is_disk(p),
    Partition: lambda tail, p: is_partition_for(tail, p),
}

#def partition_is_head_for(tail, p):
#    return (isinstance(tail, Root) and is_disk(p)) or is_partition_for(tail, p)

class DiskGraph(SimpleGraph):
    def __init__(self, sysinfo):
        self.pool = [sysinfo.partitions] + [sysinfo.raid_arrays] + [sysinfo.lvm_pvs] + [sysinfo.lvm_vgs] + [sysinfo.lvm_lvs]
        SimpleGraph.__init__(self, self.headfinder, Root())

    def headfinder(self, v):
        f = hfs[v.__class__]
        return [h for h in self.pool if f(v, h)]

    def dump(self):
        self._print(self.root, 0)

    def _print(self, v, level):
        print "%s%s" % ("  " * level, v.name)
        for head in self.headsFor(v):
            self._print(head, level + 1)

def main():
    dg = DiskGraph(SysInfo())
    dg.dump()

if __name__ == "__main__":
    main()

