import re
import unittest
from diskgraph.sysinfo import *
from mock import patch, MagicMock
from cStringIO import StringIO

def splitkeepsep(s, sep):
    return reduce(lambda acc, i: acc[:-1] + [acc[-1] + i] if i == sep else acc + [i], re.split("(%s)" % re.escape(sep), s), [])

def confopenmock(mock, text):
    mock.return_value = MagicMock(spec=file)
    handle = mock.return_value.__enter__.return_value
    handle.__iter__.return_value = iter(splitkeepsep(text, "\n"))

class TestSysInfoProcPartitions(unittest.TestCase):
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

class TestSysInfoLvmPvs(unittest.TestCase):
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
    
