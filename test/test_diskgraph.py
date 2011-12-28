from diskgraph.diskgraph import DiskGraph
from diskgraph.sysinfo import *
import unittest

class dummy(object):
    pass

class Setup(object):
    def setUp(self):
        sysinfo = dummy()
        sysinfo.partitions = sysinfo.raid_arrays = sysinfo.lvm_pvs = sysinfo.lvm_vgs = sysinfo.lvm_lvs = sysinfo.mounts = []
        self.sysinfo = sysinfo

    def assertListEquivalent(self, l1, l2):
        self.assertEqual(sorted(l1), sorted(l2))

class TestMountedFileSystems(Setup, unittest.TestCase):
    def test_graph_with_disk_and_fs(self):
        self.sysinfo.partitions = [Partition("8 0 1000 sda".split(" "))]
        self.sysinfo.mounts = [MountedFileSystem("/dev/sda 3897212928 2526269440 1212547072 68% /boot".split(" "))]
        dg = DiskGraph(self.sysinfo)
        self.assertEqual(self.sysinfo.mounts, dg.headsFor(self.sysinfo.partitions[0]))

class TestDiskGraphDiskAndPartitions(Setup, unittest.TestCase):
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

class TestDiskGraphRaidArray(Setup, unittest.TestCase):
    def test_that_raid_array_is_child_of_all_its_devices(self):
        self.sysinfo.partitions = [Partition("8 0 1000 sda".split(" ")),
                                   Partition("8 16 1000 sdb".split(" ")),
                                   Partition("9 0 1000 md0".split(" "))]
        self.sysinfo.raid_arrays = [RaidArray(("md0 sda sdb".split(" "), 1000))]
        dg = DiskGraph(self.sysinfo)
        tails = dg.tailsFor(self.sysinfo.raid_arrays[0])
        self.assertListEquivalent([self.sysinfo.partitions[0], self.sysinfo.partitions[1]], tails)

    def test_that_raid_array_can_be_child_of_partition(self):
        self.sysinfo.partitions = [Partition("8 0 1000 sda".split(" ")),
                                   Partition("8 1 1000 sda1".split(" ")),
                                   Partition("9 0 1000 md0".split(" "))]
        self.sysinfo.raid_arrays = [RaidArray(("md0 sda1".split(" "), 1000))]
        dg = DiskGraph(self.sysinfo)
        tails = dg.tailsFor(self.sysinfo.raid_arrays[0])
        self.assertListEquivalent([self.sysinfo.partitions[1]], tails)

class TestDiskGraphLvmPhysicalVolume(Setup, unittest.TestCase):
    def test_that_volume_is_child_of_device(self):
        self.sysinfo.partitions = [Partition("8 0 1000 sda".split(" "))]
        self.sysinfo.lvm_pvs = [LvmPhysicalVolume("/dev/sda 1000".split(" "))]
        dg = DiskGraph(self.sysinfo)
        tails = dg.tailsFor(self.sysinfo.lvm_pvs[0])
        self.assertListEquivalent([self.sysinfo.partitions[0]], tails)

    def test_that_volume_can_be_child_of_partition(self):
        self.sysinfo.partitions = [Partition("8 0 1000 sda".split(" ")),
                                   Partition("8 1 1000 sda1".split(" "))]
        self.sysinfo.lvm_pvs = [LvmPhysicalVolume("/dev/sda1 1000".split(" "))]
        dg = DiskGraph(self.sysinfo)
        tails = dg.tailsFor(self.sysinfo.lvm_pvs[0])
        self.assertListEquivalent([self.sysinfo.partitions[1]], tails)

    def test_that_volume_can_be_child_of_raid_array(self):
        self.sysinfo.partitions = [Partition("8 0 1000 sda".split(" ")),
                                   Partition("8 1 1000 sda1".split(" "))]
        self.sysinfo.raid_arrays = [RaidArray(("md0 sda1".split(" "), 1000))]
        self.sysinfo.lvm_pvs = [LvmPhysicalVolume("/dev/md0 1000".split(" "))]
        dg = DiskGraph(self.sysinfo)
        tails = dg.tailsFor(self.sysinfo.lvm_pvs[0])
        self.assertListEquivalent(self.sysinfo.raid_arrays, tails)

class TestDiskGraphLvmVolumeGroup(Setup, unittest.TestCase):
    def test_that_volume_group_is_child_of_physical_volume(self):
        self.sysinfo.partitions = [Partition("8 0 1000 sda".split(" "))]
        self.sysinfo.lvm_pvs = [LvmPhysicalVolume("/dev/sda 1000".split(" "))]
        self.sysinfo.lvm_vgs = [LvmVolumeGroup(["group", "1000", ["/dev/sda"]])]
        dg = DiskGraph(self.sysinfo)
        tails = dg.tailsFor(self.sysinfo.lvm_vgs[0])
        self.assertListEquivalent([self.sysinfo.lvm_pvs[0]], tails)

    def test_that_volume_group_can_be_child_of_multiple_physical_volumes(self):
        self.sysinfo.partitions = [Partition("8 0 1000 sda".split(" ")),
                                   Partition("8 16 1000 sdb".split(" "))]
        self.sysinfo.lvm_pvs = [LvmPhysicalVolume("/dev/sda 1000".split(" ")),
                                LvmPhysicalVolume("/dev/sdb 1000".split(" "))]
        self.sysinfo.lvm_vgs = [LvmVolumeGroup(["group", "1000", ["/dev/sda", "/dev/sdb"]])]
        dg = DiskGraph(self.sysinfo)
        tails = dg.tailsFor(self.sysinfo.lvm_vgs[0])
        self.assertListEquivalent(self.sysinfo.lvm_pvs, tails)

class TestDiskGraphLvmLogicalVolume(Setup, unittest.TestCase):
    def test_that_logical_volume_is_child_of_volume_group(self):
        self.sysinfo.partitions = [Partition("8 0 1000 sda".split(" "))]
        self.sysinfo.lvm_pvs = [LvmPhysicalVolume("/dev/sda 1000".split(" "))]
        self.sysinfo.lvm_vgs = [LvmVolumeGroup(["group", "1000", ["/dev/sda"]])]
        self.sysinfo.lvm_lvs= [LvmLogicalVolume(["test", "group", "1000"])]
        dg = DiskGraph(self.sysinfo)
        tails = dg.tailsFor(self.sysinfo.lvm_lvs[0])
        self.assertListEquivalent(self.sysinfo.lvm_vgs, tails)

class TestFreeSpace(Setup, unittest.TestCase):
    def test_that_free_space_node_is_not_added_for_less_than_5MB_free_space(self):
        self.sysinfo.partitions = [Partition("8 0 6119 sda".split(" ")),
                                   Partition("8 1 1000 sda1".split(" "))]
        dg = DiskGraph(self.sysinfo)
        visited = [x.name for x in list(dg.visit(dg.root))]
        self.assertFalse("free" in visited)

    def test_that_free_space_node_is_added(self):
        self.sysinfo.partitions = [Partition("8 0 6120 sda".split(" ")),
                                   Partition("8 1 1000 sda1".split(" "))]
        dg = DiskGraph(self.sysinfo)
        visited = [x.name for x in list(dg.visit(dg.root))]
        self.assertTrue("free" in visited)

    def test_that_free_space_is_calculated_correctly(self):
        self.sysinfo.partitions = [Partition("8 0 5620 sda".split(" ")),
                                   Partition("8 1 500 sda1".split(" "))]
        dg = DiskGraph(self.sysinfo)
        freenode = [x for x in list(dg.visit(dg.root)) if x.name == "free"][0]
        self.assertEqual(5242880, freenode.byte_size)

