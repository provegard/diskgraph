#!/usr/bin/python

import os, sys

if __name__ == "__main__":
    if os.geteuid() != 0:
        sys.exit("Only root can run this script.\n")

from subprocess import PIPE, Popen
import re, inspect
from sysinfo import *
from sgraph import SimpleGraph
import new

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
    return isinstance(pp, Partition) and re.match("^[hs]d[a-z]$", pp.name)

def is_partition_for(disk, part):
    return is_disk(disk) and isinstance(part, Partition) and re.match("^%s\\d+$" % re.escape(disk.name), part.name)

hfs = {
    Partition: lambda self, tail: (isinstance(tail, Root) and is_disk(self)) or is_partition_for(tail, self),
    RaidArray: lambda self, tail: isinstance(tail, Partition) and tail.name in self.partition_names,
}

for klass in hfs.keys():
    klass.isHeadFor = new.instancemethod(hfs[klass], None, klass)

class DiskGraph(SimpleGraph):
    def __init__(self, sysinfo):
        self.pool = []
        self.pool.extend(sysinfo.partitions)
        self.pool.extend(sysinfo.raid_arrays)
        self.pool.extend(sysinfo.lvm_pvs)
        self.pool.extend(sysinfo.lvm_vgs)
        self.pool.extend(sysinfo.lvm_lvs)
        SimpleGraph.__init__(self, self.headfinder, Root())

    def headfinder(self, v):
        return [h for h in self.pool if h.isHeadFor(v)]

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

