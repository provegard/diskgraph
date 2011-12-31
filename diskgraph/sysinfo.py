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
    "ProcPartitions",
    "Mdstat",
    "LvmPvs",
    "LvmVgs",
    "LvmLvs",
    "Mount",
]

BLOCK_SIZE = 1024

def open_file(f):
    with open(f) as fd:
        return [re.split(" +", line.strip()) for line in fd if line != ""]

def exec_cmd(args):
    return (re.split(" +", line.strip()) for line in subprocess.check_output(args).split("\n") if line != "")

class NamedObject(object):
    def __str__(self):
        return "%s: %s" % (self.__class__.__name__, self.name)

class Root(NamedObject):
    name = "root"

class Partition(NamedObject):
    def __init__(self, line_parts):
        self.kernel_major_minor = (int(line_parts[0]), int(line_parts[1]))
        self.byte_size = int(line_parts[2]) * BLOCK_SIZE
        self.name = line_parts[3]

    def is_disk(self):
        return re.match("^[hs]d[a-z]$", self.name)

    def is_partition_for(self, disk):
        return isinstance(disk, Partition) and disk.is_disk() and re.match("^%s\\d+$" % re.escape(disk.name), self.name)

    def is_child_of(self, tail):
        return (isinstance(tail, Root) and self.is_disk()) or self.is_partition_for(tail)

class LvmPhysicalVolume(NamedObject):
    def __init__(self, parts):
        self.name = parts[0].replace("/dev/", "")
        self.byte_size = int(parts[1])

    def is_child_of(self, tail):
        return isinstance(tail, (Partition, RaidArray)) and tail.name == self.name

class LvmVolumeGroup(NamedObject):
    def __init__(self, parts):
        self.name = parts[0]
        self.byte_size = int(parts[1])
        self.pv_names = [name.replace("/dev/", "") for name in parts[2]]

    def is_child_of(self, tail):
        return isinstance(tail, LvmPhysicalVolume) and tail.name in self.pv_names

class LvmLogicalVolume(NamedObject):
    def __init__(self, parts):
        self.name = parts[0]
        self.vg_name = parts[1]
        self.byte_size = int(parts[2])

    def is_child_of(self, tail):
        return isinstance(tail, LvmVolumeGroup) and self.vg_name == tail.name

class RaidArray(NamedObject):
    def __init__(self, data):
        """([name, partition_names...], #blocks)"""
        arr, blocks = data
        self.name = arr[0]
        self.partition_names = arr[1:]
        self.byte_size = blocks * BLOCK_SIZE

    def is_child_of(self, tail):
        return isinstance(tail, Partition) and tail.name in self.partition_names

class MountedFileSystem(NamedObject):
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

class SequenceBase(object):
    def __getitem__(self, index):
        return self._items[index]

    def __len__(self):
        return len(self._items)

    def __iter__(self):
        return (i for i in self._items)

class ProcPartitions(SequenceBase):
    def __init__(self):
        self._items = [Partition(p) for p in list(open_file("/proc/partitions"))[2:]]

class Mdstat(SequenceBase):
    def __init__(self):
        if checker.has_mdstat():
            lines = [line for line in open_file("/proc/mdstat")]
            info = [[i[0]] + [j[:j.find("[")] for j in i[4:] if re.match(".+\\[\\d+\\](\\([A-Z]\\))*", j)] for i in lines if i[0].startswith("md")]
            sizes = [int(line[0]) for line in lines if "blocks" in line]
            self._items = [RaidArray(arr) for arr in zip(info, sizes)]
        else:
            self._items = []

class LvmPvs(SequenceBase):
    def __init__(self):
        lines = []
        if checker.has_lvm_commands():
            lines = list(exec_cmd("pvs --noheadings -o pv_name,pv_size --units b --nosuffix".split(" ")))
        self._items = [LvmPhysicalVolume(parts) for parts in lines]

class LvmVgs(SequenceBase):
    def __init__(self):
        vgs = []
        if checker.has_lvm_commands():
            lines = list(exec_cmd("vgs --noheadings -o vg_name,vg_size,pv_name --units b --nosuffix".split(" ")))
            for vg in lines:
                if vgs and vgs[-1][0] == vg[0]:
                    vgs[-1][2].append(vg[2])
                    continue
                vgs.append([vg[0], vg[1], [vg[2]]])
        self._items = [LvmVolumeGroup(vg) for vg in vgs]

class LvmLvs(SequenceBase):
    def __init__(self):
        lines = []
        if checker.has_lvm_commands():
            lines = list(exec_cmd("lvs --noheadings -o lv_name,vg_name,lv_size --units b --nosuffix".split(" ")))
        self._items = [LvmLogicalVolume(parts) for parts in lines]

class Mount(SequenceBase):
    def __init__(self):
        lines = []
        if checker.has_df_command():
            lines = list(exec_cmd("df -P -B 1".split(" ")))[1:]
        self._items = [MountedFileSystem(parts) for parts in lines]

class SysInfo(object):
    def __init__(self):
        self.partitions = ProcPartitions()
        self.raid_arrays = Mdstat()
        self.lvm_pvs = LvmPvs()
        self.lvm_vgs = LvmVgs()
        self.lvm_lvs = LvmLvs()
        self.mounts = Mount()


