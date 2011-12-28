# -*- coding: utf-8 -*-
# Copyright (c) 2011, Per Rovegård <per@rovegard.se>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. Neither the name of the authors nor the names of its contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import subprocess
import re

__all__ = [
    "SysInfo",
    "Root",
    "Partition",
    "LvmPhysicalVolume",
    "LvmVolumeGroup",
    "LvmLogicalVolume",
    "RaidArray",
    "ProcPartitions",
    "Mdstat",
    "LvmPvs",
    "LvmVgs",
    "LvmLvs",
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
        lines = [line for line in open_file("/proc/mdstat")]
        info = [[i[0]] + [j[:j.find("[")] for j in i[4:] if re.match(".+\\[\\d+\\](\\([A-Z]\\))*", j)] for i in lines if i[0].startswith("md")]
        sizes = [int(line[0]) for line in lines if "blocks" in line]
        self._items = [RaidArray(arr) for arr in zip(info, sizes)]

class LvmPvs(SequenceBase):
    def __init__(self):
        lines = list(exec_cmd("pvs --noheadings -o pv_name,pv_size --units b --nosuffix".split(" ")))
        self._items = [LvmPhysicalVolume(parts) for parts in lines]

class LvmVgs(SequenceBase):
    def __init__(self):
        lines = list(exec_cmd("vgs --noheadings -o vg_name,vg_size,pv_name --units b --nosuffix".split(" ")))
        vgs = []
        for vg in lines:
            if vgs and vgs[-1][0] == vg[0]:
                vgs[-1][2].append(vg[2])
                continue
            vgs.append([vg[0], vg[1], [vg[2]]])
        self._items = [LvmVolumeGroup(vg) for vg in vgs]

class LvmLvs(SequenceBase):
    def __init__(self):
        lines = list(exec_cmd("lvs --noheadings -o lv_name,vg_name,lv_size --units b --nosuffix".split(" ")))
        self._items = [LvmLogicalVolume(parts) for parts in lines]

class SysInfo(object):
    def __init__(self):
        self.partitions = ProcPartitions()
        self.raid_arrays = Mdstat()
        self.lvm_pvs = LvmPvs()
        self.lvm_vgs = LvmVgs()
        self.lvm_lvs = LvmLvs()

