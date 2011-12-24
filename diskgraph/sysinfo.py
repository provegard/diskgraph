
import subprocess
import re

__all__ = [
    "SysInfo",
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
    #    return (re.split(" +", line.strip()) for line in fd if line != "")
    #return (re.split(" +", line.strip()) for line in open(f) if line != "")

def exec_cmd(args):
    return (re.split(" +", line.strip()) for line in subprocess.check_output(args).split("\n") if line != "")

class Partition(object):
    def __init__(self, line_parts):
        self.kernel_major_minor = (int(line_parts[0]), int(line_parts[1]))
        self.byte_size = int(line_parts[2]) * BLOCK_SIZE
        self.name = line_parts[3]

class LvmPhysicalVolume(object):
    def __init__(self, parts):
        self.name = parts[0].replace("/dev/", "")
        self.byte_size = int(parts[1])

class LvmVolumeGroup(object):
    def __init__(self, parts):
        self.name = parts[0]
        self.byte_size = int(parts[1])
        self.pv_names = [name.replace("/dev/", "") for name in parts[2]]

class LvmLogicalVolume(object):
    def __init__(self, parts):
        self.name = parts[0]
        self.vg_name = parts[1]
        self.byte_size = int(parts[2])

class RaidArray(object):
    def __init__(self, data):
        """([name, partition_names...], #blocks)"""
        arr, blocks = data
        self.name = arr[0]
        self.partition_names = arr[1:]
        self.byte_size = blocks * BLOCK_SIZE

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

