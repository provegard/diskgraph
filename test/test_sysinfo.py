import re
import unittest
from diskgraph.sysinfo import *
from mock import patch, MagicMock, Mock
from cStringIO import StringIO
from diskgraph.check import Checker
from subprocess import CalledProcessError

def checker_mock(b):
    c = Mock(spec=Checker)
    c.has_mdstat.return_value = b
    c.has_df_command.return_value = b
    c.has_partitions.return_value = b
    c.has_lvm_commands.return_value = b
    c.has_swaps.return_value = b
    return c

def splitkeepsep(s, sep):
    return reduce(lambda acc, i: acc[:-1] + [acc[-1] + i] if i == sep else acc + [i], re.split("(%s)" % re.escape(sep), s), [])

def confopenmock(mock, text):
    mock.return_value = MagicMock(spec=file)
    handle = mock.return_value.__enter__.return_value
    handle.__iter__.return_value = iter(splitkeepsep(text, "\n"))

class TestSysInfoProcPartitions(unittest.TestCase):
    @patch("diskgraph.sysinfo.checker", checker_mock(True))
    @patch("diskgraph.sysinfo.open", create=True)
    def setUp(self, open_mock):
        text = "major minor  #blocks  name\n\n   8        0  244198584 sda\n"
        confopenmock(open_mock, text)
        self.pp = ProcPartitions()

    def test_that_one_partition_is_found(self):
        self.assertEqual(1, len(self.pp))

    def test_that_partition_is_of_right_type(self):
        part = self.pp[0]
        self.assertIsInstance(part, Partition)

    def test_that_partition_contains_kernel_major_minor(self):
        part = self.pp[0]
        self.assertEqual((8, 0), part.kernel_major_minor)

    def test_that_partition_contains_name(self):
        part = self.pp[0]
        self.assertEqual("sda", part.name)

    def test_that_partition_contains_size(self):
        part = self.pp[0]
        self.assertEqual(250059350016, part.byte_size)

class TestSysInfoMdstat(unittest.TestCase):
    @patch("diskgraph.sysinfo.checker", checker_mock(True))
    @patch("diskgraph.sysinfo.open", create=True)
    def setUp(self, open_mock):
        text = ("Personalities : [raid1] [raid6] [raid5] [raid4] [linear] [multipath] [raid0] [raid10]\n"
                "md1 : active raid1 sdf1[1] sdi1[0]\n"
                "      244195904 blocks [2/2] [UU]\n")
        confopenmock(open_mock, text)
        self.md = Mdstat()

    def test_that_one_array_is_found(self):
        self.assertEqual(1, len(self.md))

    def test_that_array_is_of_right_type(self):
        arr = self.md[0]
        self.assertIsInstance(arr, RaidArray)

    def test_that_array_contains_name(self):
        arr = self.md[0]
        self.assertEqual("md1", arr.name)

    def test_that_array_contains_partition_names(self):
        arr = self.md[0]
        self.assertListEqual(["sdf1", "sdi1"], arr.partition_names)

    def test_that_array_contains_size(self):
        arr = self.md[0]
        self.assertEqual(250056605696, arr.byte_size)

class TestSysInfoSwaps(unittest.TestCase):
    @patch("diskgraph.sysinfo.checker", checker_mock(True))
    @patch("diskgraph.sysinfo.open", create=True)
    def setUp(self, open_mock):
        text = ("Filename                                Type            Size    Used    Priority\n"
                "/dev/sda2                               partition       497660  0       -1\n")
        confopenmock(open_mock, text)
        self.swaps = Swaps()

    def test_that_one_swap_area_is_found(self):
        self.assertEqual(1, len(self.swaps))

    def test_that_swap_is_of_right_type(self):
        swap = self.swaps[0]
        self.assertIsInstance(swap, SwapArea)

    def test_that_swap_area_contains_name(self):
        swap = self.swaps[0]
        self.assertEqual("sda2", swap.name)

    def test_that_swap_area_contains_size(self):
        swap = self.swaps[0]
        self.assertEqual(509603840, swap.byte_size)

class TestSysInfoMount(unittest.TestCase):
    @patch("diskgraph.sysinfo.checker", checker_mock(True))
    @patch("subprocess.check_output")
    def setUp(self, exec_mock):
        exec_mock.return_value = ("Filesystem           1B-blocks      Used Available Use% Mounted on\n"
                                  "/dev/sdk2            3897212928 2526269440 1212547072  68% /boot\n")
        self.mounts = Mount()

    def test_that_one_mounted_fs_is_found(self):
        self.assertEqual(1, len(self.mounts))

    def test_that_mounted_fs_is_of_right_type(self):
        mfs = self.mounts[0]
        self.assertIsInstance(mfs, MountedFileSystem)

    def test_that_mounted_fs_contains_name(self):
        mfs = self.mounts[0]
        self.assertEqual("/boot", mfs.name)

    def test_that_mounted_fs_contains_size(self):
        mfs = self.mounts[0]
        self.assertEqual(3897212928, mfs.byte_size)

class TestSwapArea(unittest.TestCase):
    def test_that_swap_area_is_child_of_partition(self):
        p = Partition("8 2 497660 sda2".split(" "))
        sa = SwapArea("/dev/sda2 partition 497660 0 -1".split(" "))
        self.assertTrue(sa.is_child_of(p))

class TestMountedFileSystem(unittest.TestCase):
    def test_that_mounted_fs_is_not_child_of_wrong_partition(self):
        p = Partition("8 1 1000 sda1".split(" "))
        mfs = MountedFileSystem("/dev/sda2 3897212928 2526269440 1212547072 68% /boot".split(" "))
        self.assertFalse(mfs.is_child_of(p))

    def test_that_mounted_fs_is_child_of_partition(self):
        p = Partition("8 1 1000 sda1".split(" "))
        mfs = MountedFileSystem("/dev/sda1 3897212928 2526269440 1212547072 68% /boot".split(" "))
        self.assertTrue(mfs.is_child_of(p))

    def test_that_mounted_fs_is_child_of_raid_array(self):
        r = RaidArray(("md1 /dev/sda1".split(" "), 1000))
        mfs = MountedFileSystem("/dev/md1 3897212928 2526269440 1212547072 68% /boot".split(" "))
        self.assertTrue(mfs.is_child_of(r))

    def test_that_mounted_fs_is_child_of_lvm_lv_given_vg_matches(self):
        lv = LvmLogicalVolume("small test 1000".split(" "))
        mfs = MountedFileSystem("/dev/mapper/test-small 3897212928 2526269440 1212547072 68% /boot".split(" "))
        self.assertTrue(mfs.is_child_of(lv))

    def test_that_mounted_fs_is_not_child_of_lvm_lv_if_lv_mismatch(self):
        lv = LvmLogicalVolume("big test 1000".split(" "))
        mfs = MountedFileSystem("/dev/mapper/test-small 3897212928 2526269440 1212547072 68% /boot".split(" "))
        self.assertFalse(mfs.is_child_of(lv))

    def test_that_mounted_fs_is_not_child_of_lvm_lv_if_vg_mismatch(self):
        lv = LvmLogicalVolume("small blob 1000".split(" "))
        mfs = MountedFileSystem("/dev/mapper/test-small 3897212928 2526269440 1212547072 68% /boot".split(" "))
        self.assertFalse(mfs.is_child_of(lv))

    def test_that_mounted_fs_is_not_child_of_root(self):
        r = Root()
        mfs = MountedFileSystem("/dev/mapper/test-small 3897212928 2526269440 1212547072 68% /boot".split(" "))
        self.assertFalse(mfs.is_child_of(r))

class TestSysInfoLvmPvs(unittest.TestCase):
    @patch("diskgraph.sysinfo.checker", checker_mock(True))
    @patch("subprocess.check_output")
    def setUp(self, exec_mock):
        exec_mock.return_value = "  /dev/md0   1500310929408\n"
        self.pvs = LvmPvs()

    def test_that_one_lvm_physical_volume_is_found(self):
        self.assertEqual(1, len(self.pvs))

    def test_that_lvm_physical_volume_is_of_right_type(self):
        pv = self.pvs[0]
        self.assertIsInstance(pv, LvmPhysicalVolume)

    def test_that_lvm_physical_volume_contains_name(self):
        pv = self.pvs[0]
        self.assertEqual("md0", pv.name)

    def test_that_lvm_physical_volume_contains_size(self):
        pv = self.pvs[0]
        self.assertEqual(1500310929408, pv.byte_size)

class TestSysInfoLvmVgs(unittest.TestCase):
    @patch("diskgraph.sysinfo.checker", checker_mock(True))
    @patch("subprocess.check_output")
    def setUp(self, exec_mock):
        exec_mock.return_value = ("  backup  700146778112 /dev/md1\n"
                                  "  backup  700146778112 /dev/md2\n"
                                  "  small    50008686592 /dev/sdd2\n")
        self.vgs = LvmVgs()

    def test_that_two_lvm_volume_groups_are_found(self):
        self.assertEqual(2, len(self.vgs))

    def test_that_lvm_volume_group_is_of_right_type(self):
        vg = self.vgs[0]
        self.assertIsInstance(vg, LvmVolumeGroup)

    def test_that_lvm_volume_group_contains_name(self):
        vg = self.vgs[0]
        self.assertEqual("backup", vg.name)

    def test_that_lvm_volume_group_contains_size(self):
        vg = self.vgs[0]
        self.assertEqual(700146778112, vg.byte_size)

    def test_that_lvm_volume_group_contains_physical_volume_names(self):
        vg = self.vgs[0]
        self.assertListEqual(["md1", "md2"], vg.pv_names)

class TestSysInfoLvmLvs(unittest.TestCase):
    @patch("diskgraph.sysinfo.checker", checker_mock(True))
    @patch("subprocess.check_output")
    def setUp(self, exec_mock):
        exec_mock.return_value = "  homes   backup   21474836480\n"
        self.lvs = LvmLvs()

    def test_that_one_lvm_logical_volume_is_found(self):
        self.assertEqual(1, len(self.lvs))

    def test_that_lvm_logical_volume_is_of_right_type(self):
        lv = self.lvs[0]
        self.assertIsInstance(lv, LvmLogicalVolume)

    def test_that_lvm_logical_volume_contains_name(self):
        lv = self.lvs[0]
        self.assertEqual("homes", lv.name)

    def test_that_lvm_logical_volume_contains_size(self):
        lv = self.lvs[0]
        self.assertEqual(21474836480, lv.byte_size)

    def test_that_lvm_logical_volume_contains_volume_group_name(self):
        lv = self.lvs[0]
        self.assertEqual("backup", lv.vg_name)

class TestPartition(unittest.TestCase):
    def test_that_hd_without_number_is_disk(self):
        p = Partition("3 0 1000 hda".split(" "))
        self.assertTrue(p.is_disk())

    def test_that_sd_without_number_is_disk(self):
        p = Partition("8 0 1000 sda".split(" "))
        self.assertTrue(p.is_disk())

    def test_that_hd_with_number_is_not_disk(self):
        p = Partition("3 1 1000 hda1".split(" "))
        self.assertFalse(p.is_disk())

    def test_that_partition_is_part_for_disk(self):
        d = Partition("8 0 1000 sda".split(" "))
        p = Partition("8 1 1000 sda1".split(" "))
        self.assertTrue(p.is_partition_for(d))

    def test_that_partition_is_not_part_for_disk(self):
        d = Partition("8 0 1000 sda".split(" "))
        p = Partition("8 17 1000 sdb1".split(" "))
        self.assertFalse(p.is_partition_for(d))

    def test_that_partition_is_child_of_root_if_disk(self):
        r = Root()
        d = Partition("8 0 1000 sda".split(" "))
        self.assertTrue(d.is_child_of(r))

    def test_that_partition_is_not_child_of_root_if_partition(self):
        r = Root()
        p = Partition("8 1 1000 sda1".split(" "))
        self.assertFalse(p.is_child_of(r))

    def test_that_partition_is_child_of_disk(self):
        d = Partition("8 0 1000 sda".split(" "))
        p = Partition("8 1 1000 sda1".split(" "))
        self.assertTrue(p.is_child_of(d))

class TestLvmPhysicalVolume(unittest.TestCase):
    def test_that_pv_is_child_of_disk_if_name_matches(self):
        d = Partition("8 0 1000 sda".split(" "))
        pv = LvmPhysicalVolume("/dev/sda 1000".split(" "))
        self.assertTrue(pv.is_child_of(d))

    def test_that_pv_is_not_child_of_disk_if_name_doesnt_match(self):
        d = Partition("8 0 1000 sda".split(" "))
        pv = LvmPhysicalVolume("/dev/sdb 1000".split(" "))
        self.assertFalse(pv.is_child_of(d))

    def test_that_pv_is_child_of_partition(self):
        p = Partition("8 1 1000 sda1".split(" "))
        pv = LvmPhysicalVolume("/dev/sda1 1000".split(" "))
        self.assertTrue(pv.is_child_of(p))

    def test_that_pv_is_child_of_raid_array(self):
        r = RaidArray(("md1 /dev/sda1".split(" "), 1000))
        pv = LvmPhysicalVolume("/dev/md1 1000".split(" "))
        self.assertTrue(pv.is_child_of(r))

    def test_that_pv_is_not_child_of_root(self):
        r = Root()
        pv = LvmPhysicalVolume("/dev/sda 1000".split(" "))
        self.assertFalse(pv.is_child_of(r))

class LvmVolumeGroupTest(unittest.TestCase):
    def test_that_vg_is_child_of_pv_if_pv_among_names(self):
        pv = LvmPhysicalVolume("/dev/sda 1000".split(" "))
        vg = LvmVolumeGroup(["test", "1000", ["/dev/sda"]])
        self.assertTrue(vg.is_child_of(pv))

    def test_that_vg_is_not_child_of_pv_if_pv_not_among_names(self):
        pv = LvmPhysicalVolume("/dev/sda 1000".split(" "))
        vg = LvmVolumeGroup(["test", "1000", ["/dev/sdb"]])
        self.assertFalse(vg.is_child_of(pv))

    def test_that_vg_is_not_child_of_root(self):
        r = Root()
        vg = LvmVolumeGroup(["test", "1000", ["/dev/sdb"]])
        self.assertFalse(vg.is_child_of(r))

class LvmLogicalVolumeTest(unittest.TestCase):
    def test_that_lv_is_child_of_vg_with_correct_name(self):
        vg = LvmVolumeGroup(["test", "1000", ["/dev/sdb"]])
        lv = LvmLogicalVolume("small test 1000".split(" "))
        self.assertTrue(lv.is_child_of(vg))

    def test_that_lv_is_not_child_of_vg_with_wrong_name(self):
        vg = LvmVolumeGroup(["blob", "1000", ["/dev/sdb"]])
        lv = LvmLogicalVolume("small test 1000".split(" "))
        self.assertFalse(lv.is_child_of(vg))

    def test_that_lv_is_not_child_of_root(self):
        r = Root()
        lv = LvmLogicalVolume("small test 1000".split(" "))
        self.assertFalse(lv.is_child_of(r))

class RaidArrayTest(unittest.TestCase):
    def test_that_array_is_child_of_disk_among_names(self):
        d = Partition("8 0 1000 /dev/sda".split(" "))
        r = RaidArray(("md1 /dev/sda".split(" "), 1000))
        self.assertTrue(r.is_child_of(d))

    def test_that_array_is_not_child_of_disk_not_among_names(self):
        d = Partition("8 16 1000 /dev/sdb".split(" "))
        r = RaidArray(("md1 /dev/sda".split(" "), 1000))
        self.assertFalse(r.is_child_of(d))

    def test_that_array_is_child_of_partition_among_names(self):
        p = Partition("8 1 1000 /dev/sda1".split(" "))
        r = RaidArray(("md1 /dev/sda1".split(" "), 1000))
        self.assertTrue(r.is_child_of(p))

@patch("diskgraph.sysinfo.checker", checker_mock(False))
class MissingFileOrCommandTest(unittest.TestCase):
    @patch("subprocess.check_output")
    def test_that_no_lvm_physical_volumes_are_found_if_lvm_commands_dont_exist(self, co_mock):
        co_mock.side_effect = CalledProcessError(1, "pvs")
        self.assertEqual(0, len(LvmPvs()))

    @patch("subprocess.check_output")
    def test_that_no_lvm_logical_volums_are_found_if_lvm_commands_dont_exist(self, co_mock):
        co_mock.side_effect = CalledProcessError(1, "lvs")
        self.assertEqual(0, len(LvmLvs()))

    @patch("subprocess.check_output")
    def test_that_no_lvm_volume_groups_are_found_if_lvm_commands_dont_exist(self, co_mock):
        co_mock.side_effect = CalledProcessError(1, "vgs")
        self.assertEqual(0, len(LvmVgs()))

    @patch("diskgraph.sysinfo.open", create=True)
    def test_that_no_arrays_are_found_if_mdstat_file_doesnt_exist(self, open_mock):
        open_mock.side_effect = IOError
        self.assertEqual(0, len(Mdstat()))

    @patch("subprocess.check_output")
    def test_that_no_mounted_fs_are_found_if_df_command_doesnt_exist(self, co_mock):
        co_mock.side_effect = CalledProcessError(1, "df")
        self.assertEqual(0, len(Mount()))
    
    @patch("diskgraph.sysinfo.open", create=True)
    def test_that_no_swap_areas_are_found_if_swaps_file_doesnt_exist(self, open_mock):
        open_mock.side_effect = IOError
        self.assertEqual(0, len(Swaps()))


