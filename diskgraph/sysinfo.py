# -*- coding: utf-8 -*-
"""Module for collecting information about disks, partitions, RAID arrays and LVM
entities on a Linux server. Part of the diskgraph utility.

Created and tested by Per Rovegård on a server running Ubuntu 11.04 with Python 2.7.1.

Distributed under the 3-Clause BSD license (http://opensource.org/licenses/BSD-3-Clause,
and LICENSE file).
"""

__author__ = "Per Rovegård"
__version__ = "1.1"
__license__ = "BSD-3-Clause"

import subprocess
import re
from check import checker

__all__ = [
    "SysInfo",
    "Root",
    "Partition",
    "LvmPhysicalVolume",
    "LvmVolumeGroup",
    "LvmLogicalVolume",
    "RaidArray",
    "MountedFileSystem",
    "SwapArea",
    "FreeSpace",
]

BLOCK_SIZE = 1024
FREE_SPACE_LIMIT = 100 * 1024 * 1024

def open_file(f):
    with open(f) as fd:
        return [re.split("\\s+", line.strip()) for line in fd if line != ""]

def exec_cmd(args):
    return (re.split("\\s+", line.strip()) for line in subprocess.check_output(args).split("\n") if line != "")

suffixes = ["B", "kB", "MB", "GB", "TB", "PB"]
def tosize(bytesize):
    size = float(bytesize)
    idx = 0
    while size > 1024:
        size /= 1024
        idx += 1
    return "%.2f%s" % (size, suffixes[idx])

class SysObject(object):
    def __str__(self):
        s = "%s\n%s" % (self.gettypename(), self.name)
        if hasattr(self, "byte_size"):
            s += "\n%s" % tosize(self.byte_size)
        return s

    def gettypename(self):
        return self.__class__.__name__

    def expand(self, candidates):
        return [c for c in candidates if c.is_child_of(self)]

    @classmethod
    def generate(cls):
        return []

    def is_child_of(self, tail):
        return False

class Root(SysObject):
    name = "root"

    def __str__(self):
        return "Root"

class FreeSpace(SysObject):
    name = "free"
    def __init__(self, size):
        self.byte_size = size

    @staticmethod
    def is_relevant(size):
        return size >= FREE_SPACE_LIMIT

    def __str__(self):
        return "Free space\n%s" % tosize(self.byte_size)

class Partition(SysObject):
    def __init__(self, line_parts):
        self.kernel_major_minor = (int(line_parts[0]), int(line_parts[1]))
        self.byte_size = int(line_parts[2]) * BLOCK_SIZE
        self.name = line_parts[3]

    def gettypename(self):
        return "Disk" if self.is_disk() else "Partition"

    def is_disk(self):
        return re.match("^[hs]d[a-z]$", self.name)

    def is_partition_for(self, disk):
        return isinstance(disk, Partition) and disk.is_disk() and re.match("^%s\\d+$" % re.escape(disk.name), self.name)

    def is_child_of(self, tail):
        return (isinstance(tail, Root) and self.is_disk()) or self.is_partition_for(tail)

    @classmethod
    def generate(cls):
        return [Partition(p) for p in list(open_file("/proc/partitions"))[2:]]

    def expand(self, candidates):
        result = super(Partition, self).expand(candidates)
        if self.is_disk():
            tot_child_size = sum([c.byte_size for c in result])
            free = self.byte_size - tot_child_size
            if FreeSpace.is_relevant(free):
                result.append(FreeSpace(free))
        return result

class LvmPhysicalVolume(SysObject):
    def __init__(self, parts):
        self.name = parts[0].replace("/dev/", "")
        self.byte_size = int(parts[1])

    def is_child_of(self, tail):
        return isinstance(tail, (Partition, RaidArray)) and tail.name == self.name

    @classmethod
    def generate(cls):
        lines = []
        if checker.has_lvm_commands():
            lines = list(exec_cmd("pvs --noheadings -o pv_name,pv_size --units b --nosuffix".split(" ")))
        return [LvmPhysicalVolume(parts) for parts in lines]

class LvmVolumeGroup(SysObject):
    def __init__(self, parts):
        self.name = parts[0]
        self.byte_size = int(parts[1])
        self.pv_names = [name.replace("/dev/", "") for name in parts[2]]
        self.free_space = int(parts[3])

    def is_child_of(self, tail):
        return isinstance(tail, LvmPhysicalVolume) and tail.name in self.pv_names

    def expand(self, candidates):
        result = super(LvmVolumeGroup, self).expand(candidates)
        if FreeSpace.is_relevant(self.free_space):
            result.append(FreeSpace(self.free_space))
        return result

    @classmethod
    def generate(cls):
        vgs = []
        if checker.has_lvm_commands():
            lines = list(exec_cmd("vgs --noheadings -o vg_name,vg_size,pv_name,vg_free --units b --nosuffix".split(" ")))
            for vg in lines:
                if vgs and vgs[-1][0] == vg[0]:
                    vgs[-1][2].append(vg[2])
                    continue
                vgs.append([vg[0], vg[1], [vg[2]], vg[3]])
        return [LvmVolumeGroup(vg) for vg in vgs]

class LvmLogicalVolume(SysObject):
    def __init__(self, parts):
        self.name = parts[0]
        self.vg_name = parts[1]
        self.byte_size = int(parts[2])

    def is_child_of(self, tail):
        return isinstance(tail, LvmVolumeGroup) and self.vg_name == tail.name

    @classmethod
    def generate(cls):
        lines = []
        if checker.has_lvm_commands():
            lines = list(exec_cmd("lvs --noheadings -o lv_name,vg_name,lv_size --units b --nosuffix".split(" ")))
        return [LvmLogicalVolume(parts) for parts in lines]

class RaidArray(SysObject):
    def __init__(self, data):
        """([name, partition_names...], #blocks)"""
        arr, blocks = data
        self.name = arr[0]
        self.partition_names = arr[1:]
        self.byte_size = blocks * BLOCK_SIZE

    def is_child_of(self, tail):
        return isinstance(tail, Partition) and tail.name in self.partition_names

    @classmethod
    def generate(cls):
        if checker.has_mdstat():
            lines = [line for line in open_file("/proc/mdstat")]
            info = [[i[0]] + [j[:j.find("[")] for j in i[4:] if re.match(".+\\[\\d+\\](\\([A-Z]\\))*", j)] for i in lines if i[0].startswith("md")]
            sizes = [int(line[0]) for line in lines if "blocks" in line]
            return [RaidArray(arr) for arr in zip(info, sizes)]
        return []

class MountedFileSystem(SysObject):
    def __init__(self, parts):
        self.name = parts[5]
        self.path = parts[0]
        self.byte_size = int(parts[1])

    def is_child_of(self, tail):
        if isinstance(tail, (Partition, RaidArray)):
            return "/dev/%s" % tail.name == self.path
        if isinstance(tail, LvmLogicalVolume):
            return "/dev/mapper/%s-%s" % (tail.vg_name, tail.name) == self.path
        return False

    @classmethod
    def generate(cls):
        lines = []
        if checker.has_df_command():
            lines = list(exec_cmd("df -P -B 1".split(" ")))[1:]
        return [MountedFileSystem(parts) for parts in lines]

class SwapArea(SysObject):
    def __init__(self, parts):
        self.name = parts[0].replace("/dev/", "")
        self.byte_size = int(parts[2]) * BLOCK_SIZE

    def is_child_of(self, tail):
        if isinstance(tail, Partition):
            return tail.name == self.name
        return False

    @classmethod
    def generate(cls):
        lines = []
        if checker.has_swaps():
            lines = [line for line in open_file("/proc/swaps")][1:]
        return [SwapArea(parts) for parts in lines]

class SysInfo(object):
    def __init__(self):
        sos = [v for v in globals().values() if isinstance(v, type) and SysObject in v.__bases__]
        self.objects = reduce(lambda x, y: x + y, [so.generate() for so in sos], [])

