#!/usr/bin/python3
# -*- mode: python; indent-tabs-mode: nil; python-indent-level: 4 -*-
# vim: autoindent tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=python

"""Unit tests for do_roadblock()'s dropped_followers_out out-param.

Run directly with: python3 -m unittest toolbox.test_do_roadblock
(requires TOOLBOX_HOME/python on sys.path, same as the other toolbox modules)
"""

import os
import sys
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

TOOLBOX_HOME = os.environ.get("TOOLBOX_HOME")
if TOOLBOX_HOME:
    sys.path.append(str(Path(TOOLBOX_HOME) / "python"))

from toolbox import roadblock as rb_module


class FakeRoadblockEngine:
    """Stands in for the roadblock package's engine class without requiring Redis."""

    def __init__(self, *args, **kwargs):
        self.followers = {
            "online": [], "ready": [], "busy_waiting": [], "waiting": [], "gone": [],
        }
        self.roadblock_waiting = threading.Event()
        self.user_messages = None
        self._rc = rb_module.ROADBLOCK_EXITS["success"]

    def set_uuid(self, *a, **k): pass
    def set_role(self, *a, **k): pass
    def set_timeout(self, *a, **k): pass
    def set_leader_id(self, *a, **k): pass
    def set_followers(self, *a, **k): pass
    def set_follower_id(self, *a, **k): pass
    def set_redis_server(self, *a, **k): pass
    def set_redis_password(self, *a, **k): pass
    def set_abort(self, *a, **k): pass
    def set_message_log(self, *a, **k): pass
    def set_user_messages(self, *a, **k): pass
    def set_connection_watchdog(self, *a, **k): pass

    def run_it(self):
        return self._rc


def make_engine(rc, followers=None, waiting=False):
    """Build a factory usable as a drop-in replacement for RoadblockEngine."""
    def factory(*args, **kwargs):
        engine = FakeRoadblockEngine()
        engine._rc = rc
        if followers is not None:
            engine.followers.update(followers)
        if waiting:
            engine.roadblock_waiting.set()
        return engine
    return factory


class TestDoRoadblockDroppedFollowers(unittest.TestCase):
    def test_return_is_two_values(self):
        with patch.object(rb_module, "RoadblockEngine", make_engine(rb_module.ROADBLOCK_EXITS["success"])):
            result = rb_module.do_roadblock("run1", "label", role="leader", redis_server="localhost")
        self.assertEqual(len(result), 2)

    def test_old_style_caller_unaffected_by_new_param(self):
        followers = {"online": ["client-1"]}
        with patch.object(rb_module, "RoadblockEngine", make_engine(rb_module.ROADBLOCK_EXITS["timeout"], followers=followers)):
            rc, messages_data = rb_module.do_roadblock("run1", "label", role="leader", redis_server="localhost")
        self.assertEqual(rc, rb_module.ROADBLOCK_EXITS["timeout"])

    def test_dropped_followers_populated_on_plain_timeout(self):
        followers = {"online": ["client-1"]}
        with patch.object(rb_module, "RoadblockEngine", make_engine(rb_module.ROADBLOCK_EXITS["timeout"], followers=followers)):
            dropped = []
            rb_module.do_roadblock("run1", "label", role="leader", redis_server="localhost", dropped_followers_out=dropped)
        self.assertEqual(dropped, ["client-1"])

    def test_dropped_followers_populated_on_heartbeat_timeout(self):
        # Regression test: do_heartbeat_timeout() in the roadblock library
        # returns RC_HEARTBEAT_TIMEOUT (5), a distinct code path from the
        # plain RC_TIMEOUT (3), that must also surface dropped followers —
        # this is the case a wait_for command dying mid-roadblock hits.
        followers = {"busy_waiting": ["client-2"], "waiting": ["client-3"]}
        with patch.object(
            rb_module, "RoadblockEngine",
            make_engine(rb_module.ROADBLOCK_EXITS["heartbeat_timeout"], followers=followers, waiting=True),
        ):
            dropped = []
            rc, _ = rb_module.do_roadblock("run1", "label", role="leader", redis_server="localhost", dropped_followers_out=dropped)
        self.assertEqual(rc, rb_module.ROADBLOCK_EXITS["heartbeat_timeout"])
        self.assertEqual(dropped, ["client-2", "client-3"])

    def test_dropped_followers_precedence_ready_over_gone(self):
        followers = {"ready": ["client-4"], "gone": ["client-5"]}
        with patch.object(rb_module, "RoadblockEngine", make_engine(rb_module.ROADBLOCK_EXITS["timeout"], followers=followers)):
            dropped = []
            rb_module.do_roadblock("run1", "label", role="leader", redis_server="localhost", dropped_followers_out=dropped)
        self.assertEqual(dropped, ["client-4"])

    def test_dropped_followers_falls_back_to_gone(self):
        followers = {"gone": ["client-6"]}
        with patch.object(rb_module, "RoadblockEngine", make_engine(rb_module.ROADBLOCK_EXITS["timeout"], followers=followers)):
            dropped = []
            rb_module.do_roadblock("run1", "label", role="leader", redis_server="localhost", dropped_followers_out=dropped)
        self.assertEqual(dropped, ["client-6"])

    def test_dropped_followers_not_populated_on_success(self):
        followers = {"online": ["client-7"]}
        with patch.object(rb_module, "RoadblockEngine", make_engine(rb_module.ROADBLOCK_EXITS["success"], followers=followers)):
            dropped = []
            rb_module.do_roadblock("run1", "label", role="leader", redis_server="localhost", dropped_followers_out=dropped)
        self.assertEqual(dropped, [])

    def test_dropped_followers_not_populated_for_follower_role(self):
        followers = {"online": ["client-8"]}
        with patch.object(rb_module, "RoadblockEngine", make_engine(rb_module.ROADBLOCK_EXITS["timeout"], followers=followers)):
            dropped = []
            rb_module.do_roadblock(
                "run1", "label", role="follower", follower_id="client-8",
                redis_server="localhost", dropped_followers_out=dropped,
            )
        self.assertEqual(dropped, [])

    def test_dropped_followers_out_optional(self):
        followers = {"online": ["client-9"]}
        with patch.object(rb_module, "RoadblockEngine", make_engine(rb_module.ROADBLOCK_EXITS["timeout"], followers=followers)):
            # Must not raise even though dropped_followers_out isn't passed.
            rb_module.do_roadblock("run1", "label", role="leader", redis_server="localhost")


if __name__ == "__main__":
    unittest.main()
