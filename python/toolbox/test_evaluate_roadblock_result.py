#!/usr/bin/python3
# -*- mode: python; indent-tabs-mode: nil; python-indent-level: 4 -*-
# vim: autoindent tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=python

"""Unit tests for evaluate_roadblock_result()'s rc-to-flag mapping.

Run directly with: python3 -m unittest toolbox.test_evaluate_roadblock_result
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

from toolbox.messages import ROADBLOCK_EXITS, evaluate_roadblock_result


class TestEvaluateRoadblockResult(unittest.TestCase):
    def test_success_sets_no_flags(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = evaluate_roadblock_result(ROADBLOCK_EXITS["success"], "label", tmpdir)
        self.assertFalse(result["is_timeout"])
        self.assertFalse(result["is_abort"])

    def test_plain_timeout_sets_is_timeout(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = evaluate_roadblock_result(ROADBLOCK_EXITS["timeout"], "label", tmpdir)
        self.assertTrue(result["is_timeout"])
        self.assertFalse(result["is_abort"])

    def test_heartbeat_timeout_sets_is_timeout(self):
        # Regression test: do_roadblock() on a wait_for roadblock can return
        # RC_HEARTBEAT_TIMEOUT (5) instead of RC_TIMEOUT (3). Before this fix
        # ROADBLOCK_EXITS had no entry for it, so neither is_timeout nor
        # is_abort was set and the engine silently continued instead of
        # quitting.
        with tempfile.TemporaryDirectory() as tmpdir:
            result = evaluate_roadblock_result(ROADBLOCK_EXITS["heartbeat_timeout"], "label", tmpdir)
        self.assertTrue(result["is_timeout"])
        self.assertFalse(result["is_abort"])

    def test_abort_sets_is_abort(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = evaluate_roadblock_result(ROADBLOCK_EXITS["abort"], "label", tmpdir)
        self.assertTrue(result["is_abort"])
        self.assertFalse(result["is_timeout"])


if __name__ == "__main__":
    unittest.main()
