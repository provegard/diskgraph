import re
from sysinfo import *
from sgraph import SimpleGraph
import new

class Root(object):
    name = "root"
    def __str__(self):
        return self.name

def is_disk(pp):
    return isinstance(pp, Partition) and re.match("^[hs]d[a-z]$", pp.name)

def is_partition_for(disk, part):
    return is_disk(disk) and isinstance(part, Partition) and re.match("^%s\\d+$" % re.escape(disk.name), part.name)

hfs = {
    Partition: lambda self, tail: (isinstance(tail, Root) and is_disk(self)) or is_partition_for(tail, self),
    RaidArray: lambda self, tail: isinstance(tail, Partition) and tail.name in self.partition_names,
    LvmPhysicalVolume: lambda self, tail: isinstance(tail, (Partition, RaidArray)) and tail.name == self.name,
    LvmVolumeGroup: lambda self, tail: isinstance(tail, LvmPhysicalVolume) and tail.name in self.pv_names,
    LvmLogicalVolume: lambda self, tail: isinstance(tail, LvmVolumeGroup) and self.vg_name == tail.name,
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
        print "%s%s" % ("  " * level, str(v))
        for head in self.headsFor(v):
            self._print(head, level + 1)

