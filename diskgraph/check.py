# -*- coding: utf-8 -*-
"""Module for checking the availability of certain files and commands. Part of the
diskgraph utility.

Created and tested by Per Rovegård on a server running Ubuntu 11.04 with Python 2.7.1.

Distributed under the 3-Clause BSD license (http://opensource.org/licenses/BSD-3-Clause,
and LICENSE file).
"""

__author__ = "Per Rovegård"
__version__ = "1.2"
__license__ = "BSD-3-Clause"

import os.path
from subprocess import check_output, CalledProcessError

def file_exists(path):
    return os.path.exists(path)

def cmd_exists(cmd):
    try:
        check_output(["which", cmd])
        return True
    except CalledProcessError:
        return False

class Checker(object):
    def __init__(self):
        self._has_swaps = file_exists("/proc/swaps")
        self._has_partitions = file_exists("/proc/partitions")
        self._has_mdstat = file_exists("/proc/mdstat")
        self._has_lvm_commands = cmd_exists("pvs") and cmd_exists("vgs") and cmd_exists("lvs")
        self._has_df_command = cmd_exists("df")

    def has_partitions(self):
        return self._has_partitions

    def has_mdstat(self):
        return self._has_mdstat

    def has_lvm_commands(self):
        return self._has_lvm_commands

    def has_df_command(self):
        return self._has_df_command

    def has_swaps(self):
        return self._has_swaps

try:
    checker
except NameError:
    checker = Checker()

