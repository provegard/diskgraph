from diskgraph.diskgraph import DiskGraph
from diskgraph.sysinfo import *
import unittest

class dummy(object):
    pass

class TestDiskGraph(unittest.TestCase):
    def setUp(self):
        sysinfo = dummy()
        sysinfo.partitions = sysinfo.raid_arrays = sysinfo.lvm_pvs = sysinfo.lvm_vgs = sysinfo.lvm_lvs = []
        self.sysinfo = sysinfo

    def test_graph_with_single_disk(self):
        self.sysinfo.partitions = [Partition("8 0 1000 sda".split(" "))]
        dg = DiskGraph(self.sysinfo)
        visited = [x.name for x in list(dg.visit(dg.root))]
        self.assertEqual(["root", "sda"], visited)

    def test_graph_with_single_ide_disk(self):
        self.sysinfo.partitions = [Partition("3 0 1000 hda".split(" "))]
        dg = DiskGraph(self.sysinfo)
        visited = [x.name for x in list(dg.visit(dg.root))]
        self.assertEqual(["root", "hda"], visited)

    def test_that_mds_and_dms_are_ignored_as_root_level_disks(self):
        self.sysinfo.partitions = [Partition("252 1 1000 dm-1".split(" ")),
                                   Partition("9 1 1000 md1".split(" "))]
        dg = DiskGraph(self.sysinfo)
        visited = [x.name for x in list(dg.visit(dg.root))]
        self.assertEqual(["root"], visited)

    def test_graph_with_single_disk_and_partition(self):
        self.sysinfo.partitions = [Partition("8 0 1000 sda".split(" ")),
                                   Partition("8 1 1000 sda1".split(" "))]
        dg = DiskGraph(self.sysinfo)
        visited = [x.name for x in list(dg.visit(dg.root))]
        self.assertEqual(["root", "sda", "sda1"], visited)

    def test_that_partition_is_associated_with_right_disk(self):
        self.sysinfo.partitions = [Partition("8 0 1000 sda".split(" ")),
                                   Partition("8 16 1000 sdb".split(" ")),
                                   Partition("8 1 1000 sda1".split(" "))]
        dg = DiskGraph(self.sysinfo)
        visited = [x.name for x in list(dg.visit(dg.root))]
        self.assertEqual(["root", "sda", "sda1", "sdb"], visited)

    def test_that_raid_array_is_child_of_all_its_devices(self):
        self.sysinfo.partitions = [Partition("8 0 1000 sda".split(" ")),
                                   Partition("8 16 1000 sdb".split(" ")),
                                   Partition("9 0 1000 md0".split(" "))]
        self.sysinfo.raid_arrays = [RaidArray(("md0 sda sdb".split(" "), 1000))]
        dg = DiskGraph(self.sysinfo)
        tails = dg.tailsFor(self.sysinfo.raid_arrays[0])
        self.assertEqual([self.sysinfo.partitions[0], self.sysinfo.partitions[1]], tails)

    def test_that_raid_array_can_be_child_of_partition(self):
        self.sysinfo.partitions = [Partition("8 0 1000 sda".split(" ")),
                                   Partition("8 1 1000 sda1".split(" ")),
                                   Partition("9 0 1000 md0".split(" "))]
        self.sysinfo.raid_arrays = [RaidArray(("md0 sda1".split(" "), 1000))]
        dg = DiskGraph(self.sysinfo)
        tails = dg.tailsFor(self.sysinfo.raid_arrays[0])
        self.assertEqual([self.sysinfo.partitions[1]], tails)
