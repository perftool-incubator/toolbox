#!/usr/bin/python3
# -*- mode: python; indent-tabs-mode: nil; python-indent-level: 4 -*-
# vim: autoindent tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=python

"""Unit tests for lightweight CPU topology and node-local L3 selection.

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
    get_node_l3_domains,
    select_node_l3_domain,
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

    def test_default_shape_and_last_cache_index_are_unchanged(self):
        self.make_cache_index(0, 0, level=3, shared_cpu_list="0")
        self.make_cache_index(0, 1, level=3, shared_cpu_list="0-1")
        # The snapshot API historically accepts caches without a type file
        # and keeps only the last index at each level.
        self.assertEqual(build_cpu_topology(self.cpu_root, self.numa_map_file), {
            0: {"package_id": 0, "die_id": 0, "core_id": 0, "thread_id": 0,
                "cache_domains": {"3": "0-1"}},
        })


class TestNodeL3Domains(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tmpdir.name) / 'sys' / 'devices' / 'system'
        write(self.root / 'node/node0/cpulist', '0-7\n')
        # CPU 3 is offline. Domain 0 has two CPUs, domain 2 has three,
        # and CPU 7 has only a non-Unified L3 cache.
        for cpu, shared in ((0, '0-1'), (1, '0-1'), (2, '2-3'),
                            (3, '2-3'), (4, '4-6,8'), (5, '4-6,8'),
                            (6, '4-6,8'), (7, '7')):
            base = self.root / f'cpu/cpu{cpu}/cache/index3'
            write(base / 'level', '3\n')
            write(base / 'type', 'Data\n' if cpu == 7 else 'Unified\n')
            write(base / 'shared_cpu_list', shared + '\n')
        write(self.root / 'cpu/cpu3/online', '0\n')

    def tearDown(self):
        self.tmpdir.cleanup()

    def select(self, domain=None, count=None, log=None):
        return select_node_l3_domain(0, domain, count, self.root, log)

    def test_discovery_intersects_node_and_online_and_ignores_data_cache(self):
        self.assertEqual(get_node_l3_domains(0, self.root),
                         ([0, 1, 2, 4, 5, 6, 7], [[0, 1], [2], [4, 5, 6]]))

    def test_auto_largest_and_count(self):
        self.assertEqual(self.select(), (2, [4, 5, 6]))
        self.assertEqual(self.select(count=2), (2, [4, 5]))
        self.assertEqual(self.select(count=3), (2, [4, 5, 6]))

    def test_explicit_zero_based_domain_and_count(self):
        self.assertEqual(self.select(domain=0), (0, [0, 1]))
        self.assertEqual(self.select(domain=1, count=1), (1, [2]))
        self.assertEqual(self.select(domain=2, count=2), (2, [4, 5]))

    def test_tie_goes_to_lowest_cpu(self):
        write(self.root / 'cpu/cpu3/online', '1\n')
        write(self.root / 'node/node0/cpulist', '0-3\n')
        self.assertEqual(self.select(), (0, [0, 1]))

    def test_insufficient_and_out_of_range_with_mapping(self):
        messages = []
        with self.assertRaisesRegex(ValueError, 'domain 1 has 1 CPUs.*requested 2'):
            self.select(domain=1, count=2, log=messages.append)
        self.assertIn('L3 domain 0: 0,1 (2 CPUs)', messages)
        self.assertIn('L3 domain 2: 4,5,6 (3 CPUs)', messages)
        with self.assertRaisesRegex(ValueError, 'no L3 domain has 4 CPUs.*0: 2, 1: 1, 2: 3'):
            self.select(count=4)
        with self.assertRaisesRegex(ValueError, 'valid domains are 0..2'):
            self.select(domain=3)
        for domain, count in ((-1, None), (None, 0), (None, -1)):
            with self.assertRaises(ValueError):
                self.select(domain, count)

    def test_single_domain_and_no_l3(self):
        write(self.root / 'node/node0/cpulist', '0-1\n')
        self.assertEqual(self.select(), (0, [0, 1]))
        write(self.root / 'node/node0/cpulist', '7\n')
        with self.assertRaisesRegex(ValueError, 'no online CPUs with L3 Unified'):
            self.select()

    def test_multiple_indices_at_the_same_level_are_preserved(self):
        base = self.root / 'cpu/cpu0/cache/index4'
        write(base / 'level', '3\n')
        write(base / 'type', 'Unified\n')
        write(base / 'shared_cpu_list', '0,2\n')
        _, domains = get_node_l3_domains(0, self.root)
        self.assertEqual(domains, [[0, 1], [0, 2], [2], [4, 5, 6]])

    def test_equivalent_shared_lists_and_duplicate_indices_are_deduplicated(self):
        write(self.root / 'cpu/cpu1/cache/index3/shared_cpu_list', '1,0,0\n')
        base = self.root / 'cpu/cpu0/cache/index10'
        write(base / 'level', '3\n')
        write(base / 'type', 'Unified\n')
        write(base / 'shared_cpu_list', '0,1\n')
        self.assertEqual(get_node_l3_domains(0, self.root),
                         ([0, 1, 2, 4, 5, 6, 7], [[0, 1], [2], [4, 5, 6]]))

    def test_ignores_core_topology_non_l3_and_other_nodes(self):
        write(self.root / 'cpu/cpu0/topology/core_id', '\n')
        write(self.root / 'cpu/cpu0/topology/thread_siblings_list', '\n')
        base = self.root / 'cpu/cpu0/cache/index2'
        write(base / 'level', '2\n')
        write(base / 'type', 'Unified\n')
        write(base / 'shared_cpu_list', 'invalid\n')
        write(self.root / 'cpu/cpu3/cache/index3/shared_cpu_list', 'invalid\n')
        write(self.root / 'cpu/cpu8/topology/core_id', 'invalid\n')
        write(self.root / 'cpu/cpu8/cache/index3/level', '3\n')
        write(self.root / 'cpu/cpu8/cache/index3/type', 'Unified\n')
        write(self.root / 'cpu/cpu8/cache/index3/shared_cpu_list', 'invalid\n')
        self.assertEqual(self.select(), (2, [4, 5, 6]))

    def test_global_online_list_handles_missing_per_cpu_flags(self):
        write(self.root / 'cpu/online', '1-2,4,6\n')
        self.assertEqual(get_node_l3_domains(0, self.root),
                         ([1, 2, 4, 6], [[1], [2], [4, 6]]))
        self.assertEqual(self.select(), (2, [4, 6]))
        write(self.root / 'cpu/online', '\n')
        with self.assertRaisesRegex(ValueError, 'no online CPUs'):
            self.select()

    def test_invalid_global_online_list_is_rejected(self):
        for value in ('invalid', '2-1,4'):
            with self.subTest(value=value):
                write(self.root / 'cpu/online', value + '\n')
                with self.assertRaisesRegex(ValueError, 'system online CPUs.*invalid CPU'):
                    self.select()

    def test_missing_cpu_directories_are_not_online(self):
        write(self.root / 'node/node0/cpulist', '0-2,9\n')
        # A file with a CPU-like name is not a CPU directory either.
        write(self.root / 'cpu/cpu9', '')
        self.assertEqual(get_node_l3_domains(0, self.root),
                         ([0, 1, 2], [[0, 1], [2]]))

    def test_missing_or_empty_l3_fields_are_unavailable(self):
        write(self.root / 'node/node0/cpulist', '0\n')
        base = self.root / 'cpu/cpu0/cache/index3'
        for field, value in (('level', '3\n'), ('type', 'Unified\n'),
                             ('shared_cpu_list', '0-1\n')):
            for missing in (True, False):
                with self.subTest(field=field, missing=missing):
                    if missing:
                        (base / field).unlink()
                    else:
                        write(base / field, '\n')
                    with self.assertRaisesRegex(ValueError, 'no online CPUs with L3 Unified'):
                        self.select()
                    write(base / field, value)

    def test_malformed_l3_cpu_lists_are_rejected_with_context(self):
        path = self.root / 'cpu/cpu0/cache/index3/shared_cpu_list'
        for value in ('0-1,', '0-2-3', '0,-1', '2-1,0'):
            with self.subTest(value=value):
                write(path, value + '\n')
                with self.assertRaisesRegex(ValueError, 'CPU 0 L3 cache.*invalid CPU'):
                    self.select()

    def test_l3_mask_must_include_the_reporting_cpu(self):
        write(self.root / 'cpu/cpu0/cache/index3/shared_cpu_list', '4-6\n')
        with self.assertRaisesRegex(ValueError, 'does not include CPU 0'):
            self.select()

    def test_vm_without_cache_topology_reports_unavailable(self):
        write(self.root / 'node/node1/cpulist', '20\n')
        (self.root / 'cpu/cpu20').mkdir()
        with self.assertRaisesRegex(ValueError, 'NUMA node 1 has no online CPUs with L3 Unified'):
            get_node_l3_domains(1, self.root)

    def test_null_padding_is_stripped_from_sysfs_values(self):
        for relative in ('node/node0/cpulist', 'cpu/cpu3/online',
                         'cpu/cpu0/cache/index3/level', 'cpu/cpu0/cache/index3/type',
                         'cpu/cpu0/cache/index3/shared_cpu_list'):
            path = self.root / relative
            write(path, path.read_text() + '\x00' * 20)
        self.assertEqual(get_node_l3_domains(0, self.root),
                         ([0, 1, 2, 4, 5, 6, 7], [[0, 1], [2], [4, 5, 6]]))

    def test_sparse_smt_domains_count_logical_cpus(self):
        write(self.root / 'node/node0/cpulist', '0-3,8-11\n')
        write(self.root / 'cpu/cpu3/online', '1\n')
        for cpu in (0, 1, 2, 3, 8, 9, 10, 11):
            base = self.root / f'cpu/cpu{cpu}/cache/index7'
            shared = '0-1,8-9' if cpu in (0, 1, 8, 9) else '2-3,10-11'
            old_index = self.root / f'cpu/cpu{cpu}/cache/index3/type'
            if old_index.exists():
                write(old_index, 'Data\n')
            write(base / 'level', '3\n')
            write(base / 'type', 'Unified\n')
            write(base / 'shared_cpu_list', shared + '\n')
        self.assertEqual(get_node_l3_domains(0, self.root),
                         ([0, 1, 2, 3, 8, 9, 10, 11], [[0, 1, 8, 9], [2, 3, 10, 11]]))
        self.assertEqual(self.select(count=3), (0, [0, 1, 8]))

    def test_domain_numbering_sorts_numeric_cpu_ids(self):
        write(self.root / 'node/node0/cpulist', '16,8-9,0\n')
        for cpu, shared in ((16, '16'), (9, '8-9'), (8, '8-9')):
            base = self.root / f'cpu/cpu{cpu}/cache/index0'
            write(base / 'level', '3\n')
            write(base / 'type', 'Unified\n')
            write(base / 'shared_cpu_list', shared + '\n')
        self.assertEqual(get_node_l3_domains(0, self.root),
                         ([0, 8, 9, 16], [[0], [8, 9], [16]]))
        self.assertEqual(self.select(domain=2), (2, [16]))
        self.assertEqual(self.select(), (1, [8, 9]))

    def test_logging_includes_mapping_and_final_count_limited_selection(self):
        messages = []
        self.assertEqual(self.select(count=2, log=messages.append), (2, [4, 5]))
        self.assertEqual(messages, [
            'NUMA node 0 online CPUs: 0,1,2,4,5,6,7',
            'L3 domain 0: 0,1 (2 CPUs)',
            'L3 domain 1: 2 (1 CPUs)',
            'L3 domain 2: 4,5,6 (3 CPUs)',
            'selected L3 domain 2 CPUs: 4,5',
        ])

    def test_invalid_argument_types(self):
        for value in (-1, True, False, '0', 0.0):
            with self.subTest(node=value):
                with self.assertRaisesRegex(ValueError, 'NUMA node must be'):
                    get_node_l3_domains(value, self.root)
            with self.subTest(domain=value):
                with self.assertRaisesRegex(ValueError, 'L3 domain number must be'):
                    self.select(domain=value)
        for value in (-1, 0, True, False, '1', 1.0):
            with self.subTest(count=value):
                with self.assertRaisesRegex(ValueError, 'L3 CPU count must be'):
                    self.select(count=value)

    def test_nonzero_node(self):
        write(self.root / 'node/node2/cpulist', '4-6\n')
        self.assertEqual(get_node_l3_domains(2, self.root), ([4, 5, 6], [[4, 5, 6]]))
        self.assertEqual(select_node_l3_domain(2, domain=0, count=2, sysfs_root=self.root),
                         (0, [4, 5]))

    def test_missing_empty_and_offline_node(self):
        with self.assertRaisesRegex(ValueError, 'cannot read NUMA node 1'):
            get_node_l3_domains(1, self.root)
        write(self.root / 'node/node0/cpulist', '\n')
        with self.assertRaisesRegex(ValueError, 'empty or invalid CPU list'):
            self.select()
        write(self.root / 'node/node0/cpulist', '2-1,4\n')
        with self.assertRaisesRegex(ValueError, 'invalid CPU range'):
            self.select()
        write(self.root / 'node/node0/cpulist', '3\n')
        with self.assertRaisesRegex(ValueError, 'no online CPUs'):
            self.select()
        write(self.root / 'node/node0/cpulist', '99\n')
        with self.assertRaisesRegex(ValueError, 'no online CPUs'):
            self.select()


if __name__ == "__main__":
    unittest.main()
