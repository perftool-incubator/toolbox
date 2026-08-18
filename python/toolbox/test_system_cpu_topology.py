#!/usr/bin/python3
# -*- mode: python; indent-tabs-mode: nil; python-indent-level: 4 -*-
# vim: autoindent tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=python

"""Unit tests for build_cpu_topology()/get_cpu_topology()/get_cpu_node()/
get_cpu_cache_domains() -- the lightweight (non-class-based) CPU
topology helpers used by post-processing scripts like sysstat's.

Run directly with: python3 -m unittest toolbox.test_system_cpu_topology
(requires TOOLBOX_HOME/python on sys.path, same as the other toolbox modules)
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

TOOLBOX_HOME = os.environ.get("TOOLBOX_HOME")
if TOOLBOX_HOME:
    sys.path.append(str(Path(TOOLBOX_HOME) / "python"))

from toolbox.system_cpu_topology import (
    build_cpu_topology,
    get_cpu_topology,
    get_cpu_node,
    get_cpu_cache_domains,
)


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)


class TestBuildCpuTopology(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.cpu_root = os.path.join(self.tmpdir.name, "sys/devices/system/cpu")
        self.numa_map_file = os.path.join(self.tmpdir.name, "cpu-numa-nodes.txt")
        self.orig_cwd = os.getcwd()
        os.chdir(self.tmpdir.name)

    def tearDown(self):
        os.chdir(self.orig_cwd)
        self.tmpdir.cleanup()

    def make_cpu(self, cpu_id, package_id=0, die_id=0, core_id=0, thread_siblings=None, online=None):
        cpu_dir = os.path.join(self.cpu_root, f"cpu{cpu_id}")
        topo_dir = os.path.join(cpu_dir, "topology")
        write(os.path.join(topo_dir, "physical_package_id"), f"{package_id}\n")
        write(os.path.join(topo_dir, "die_id"), f"{die_id}\n")
        write(os.path.join(topo_dir, "core_id"), f"{core_id}\n")
        if thread_siblings is not None:
            write(os.path.join(topo_dir, "thread_siblings_list"), f"{thread_siblings}\n")
        if online is not None:
            write(os.path.join(cpu_dir, "online"), f"{online}\n")
        return cpu_dir

    def test_package_die_core_thread_from_topology(self):
        self.make_cpu(0, package_id=1, die_id=2, core_id=3, thread_siblings="0,4")
        cpu_topo = build_cpu_topology(self.cpu_root, numa_map_file=self.numa_map_file)
        self.assertEqual(get_cpu_topology(0, cpu_topo), (1, 2, 3, 0))

    def test_thread_id_second_sibling(self):
        self.make_cpu(4, thread_siblings="0,4")
        cpu_topo = build_cpu_topology(self.cpu_root, numa_map_file=self.numa_map_file)
        self.assertEqual(get_cpu_topology(4, cpu_topo)[3], 1)

    def test_unknown_cpu_falls_back_to_defaults(self):
        cpu_topo = build_cpu_topology(self.cpu_root, numa_map_file=self.numa_map_file)
        self.assertEqual(get_cpu_topology(7, cpu_topo), (0, 0, 7, 0))

    def test_cpu_topo_path_missing_returns_empty(self):
        cpu_topo = build_cpu_topology(os.path.join(self.tmpdir.name, "does-not-exist"))
        self.assertEqual(cpu_topo, {})
        self.assertEqual(get_cpu_topology(0, cpu_topo), (0, 0, 0, 0))

    def test_offline_cpu_excluded(self):
        self.make_cpu(0, online="0")
        cpu_topo = build_cpu_topology(self.cpu_root, numa_map_file=self.numa_map_file)
        self.assertNotIn(0, cpu_topo)
        self.assertEqual(get_cpu_topology(0, cpu_topo), (0, 0, 0, 0))
        self.assertIsNone(get_cpu_node(0, cpu_topo))

    def test_missing_topology_dir_matches_unknown_cpu_fallback(self):
        # A cpu directory that exists (e.g. because it has cache info)
        # but has no topology/ subdirectory at all must still produce
        # the exact same (package, die, core, thread) tuple as a CPU
        # absent from cpu_topo entirely -- this is the "no regression"
        # guarantee for adding node_id/cache_domains independently of
        # topology/'s presence.
        write(os.path.join(self.cpu_root, "cpu2", "cache", "index0", "level"), "1\n")
        write(os.path.join(self.cpu_root, "cpu2", "cache", "index0", "shared_cpu_list"), "2\n")
        cpu_topo = build_cpu_topology(self.cpu_root, numa_map_file=self.numa_map_file)
        self.assertEqual(get_cpu_topology(2, cpu_topo), (0, 0, 2, 0))

    def test_null_byte_padding_stripped(self):
        # cpio pads sysfs pseudo-files (which report a bogus non-zero
        # size) with trailing null bytes when copying them -- verify the
        # existing null-stripping convention still works for topology
        # fields.
        self.make_cpu(0, package_id=1, die_id=2, core_id=3)
        topo_dir = os.path.join(self.cpu_root, "cpu0", "topology")
        write(os.path.join(topo_dir, "core_id"), "3\n" + "\x00" * 20)
        cpu_topo = build_cpu_topology(self.cpu_root, numa_map_file=self.numa_map_file)
        self.assertEqual(get_cpu_topology(0, cpu_topo), (1, 2, 3, 0))


class TestNumaNode(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.cpu_root = os.path.join(self.tmpdir.name, "sys/devices/system/cpu")
        self.numa_map_file = os.path.join(self.tmpdir.name, "cpu-numa-nodes.txt")
        os.makedirs(os.path.join(self.cpu_root, "cpu0", "topology"))

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_node_from_manifest(self):
        write(self.numa_map_file, "cpu0 node1\n")
        cpu_topo = build_cpu_topology(self.cpu_root, numa_map_file=self.numa_map_file)
        self.assertEqual(get_cpu_node(0, cpu_topo), 1)

    def test_node_unset_without_manifest(self):
        cpu_topo = build_cpu_topology(self.cpu_root, numa_map_file=self.numa_map_file)
        self.assertIsNone(get_cpu_node(0, cpu_topo))

    def test_malformed_manifest_lines_ignored(self):
        write(self.numa_map_file, "garbage line\ncpu0 node1\ncpu1\n")
        cpu_topo = build_cpu_topology(self.cpu_root, numa_map_file=self.numa_map_file)
        self.assertEqual(get_cpu_node(0, cpu_topo), 1)

    def test_unknown_cpu_node_is_none(self):
        write(self.numa_map_file, "cpu0 node1\n")
        cpu_topo = build_cpu_topology(self.cpu_root, numa_map_file=self.numa_map_file)
        self.assertIsNone(get_cpu_node(9, cpu_topo))


class TestCacheDomains(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.cpu_root = os.path.join(self.tmpdir.name, "sys/devices/system/cpu")
        self.numa_map_file = os.path.join(self.tmpdir.name, "cpu-numa-nodes.txt")

    def tearDown(self):
        self.tmpdir.cleanup()

    def make_cache_index(self, cpu_id, index, level, shared_cpu_list, pad_nulls=False):
        base = os.path.join(self.cpu_root, f"cpu{cpu_id}", "cache", f"index{index}")
        suffix = ("\n" + "\x00" * 20) if pad_nulls else "\n"
        write(os.path.join(base, "level"), f"{level}{suffix}")
        write(os.path.join(base, "shared_cpu_list"), f"{shared_cpu_list}{suffix}")

    def test_single_level_single_cpu(self):
        self.make_cache_index(0, 0, level=1, shared_cpu_list="0")
        cpu_topo = build_cpu_topology(self.cpu_root, numa_map_file=self.numa_map_file)
        self.assertEqual(get_cpu_cache_domains(0, cpu_topo), {"1": "0"})

    def test_multiple_levels_and_shared_range(self):
        self.make_cache_index(0, 0, level=1, shared_cpu_list="0")
        self.make_cache_index(0, 1, level=2, shared_cpu_list="0")
        self.make_cache_index(0, 2, level=3, shared_cpu_list="0-15")
        cpu_topo = build_cpu_topology(self.cpu_root, numa_map_file=self.numa_map_file)
        self.assertEqual(
            get_cpu_cache_domains(0, cpu_topo),
            {"1": "0", "2": "0", "3": "0-15"},
        )

    def test_null_byte_padding_stripped(self):
        self.make_cache_index(0, 0, level=3, shared_cpu_list="0-15", pad_nulls=True)
        cpu_topo = build_cpu_topology(self.cpu_root, numa_map_file=self.numa_map_file)
        self.assertEqual(get_cpu_cache_domains(0, cpu_topo), {"3": "0-15"})

    def test_no_cache_dir_is_empty(self):
        os.makedirs(os.path.join(self.cpu_root, "cpu0", "topology"))
        cpu_topo = build_cpu_topology(self.cpu_root, numa_map_file=self.numa_map_file)
        self.assertEqual(get_cpu_cache_domains(0, cpu_topo), {})

    def test_unknown_cpu_is_empty(self):
        cpu_topo = build_cpu_topology(self.cpu_root, numa_map_file=self.numa_map_file)
        self.assertEqual(get_cpu_cache_domains(9, cpu_topo), {})


if __name__ == "__main__":
    unittest.main()
