# -*- mode: python; indent-tabs-mode: nil; python-indent-level: 4 -*-
# vim: autoindent tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=python

import logging
import os
import sys
import tempfile
from pathlib import Path

ROADBLOCK_HOME = os.environ.get("ROADBLOCK_HOME")
if ROADBLOCK_HOME is not None:
    sys.path.append(str(Path(ROADBLOCK_HOME)))

try:
    from roadblock import roadblock as RoadblockEngine
except ImportError:
    RoadblockEngine = None

logger = logging.getLogger(__name__)

ROADBLOCK_EXITS = {
    "success": 0,
    "input": 2,
    "timeout": 3,
    "abort": 4,
    "abort_waiting": 6,
}


def do_roadblock(roadblock_id, label, role="follower", follower_id=None,
                 leader_id="controller", timeout=300, redis_server=None,
                 redis_password=None, messages=None, followers_file=None,
                 abort=False, connection_watchdog=True, log_level="normal",
                 msgs_dir=None):
    """Run a roadblock synchronization point.

    Supports both leader and follower roles. Uses the roadblock module
    natively rather than shelling out to roadblocker.py.

    Args:
        roadblock_id: base ID for the roadblock UUID
        label: name of this roadblock point
        role: "leader" or "follower"
        follower_id: ID when running as follower
        leader_id: ID of the leader (default: "controller")
        timeout: seconds to wait before timing out
        redis_server: redis/valkey server address
        redis_password: redis/valkey password
        messages: path to a JSON messages file to send
        followers_file: path to a file listing follower IDs (leader only)
        abort: whether to send an abort signal
        connection_watchdog: enable/disable the connection watchdog
        log_level: roadblock log level
        msgs_dir: directory for message log output

    Returns:
        tuple of (return_code, messages_data)
    """
    if RoadblockEngine is None:
        raise RuntimeError(
            "roadblock module not available. Set ROADBLOCK_HOME to the "
            "roadblock project directory."
        )

    uuid = f"{roadblock_id}:{label}"
    logger.info("Roadblock: role=%s uuid=%s timeout=%d", role, uuid, timeout)

    msgs_log_file = None
    if msgs_dir:
        msgs_log_file = os.path.join(msgs_dir, f"{label}.json")

    rb = RoadblockEngine(None, None)
    rb.set_uuid(uuid)
    rb.set_role(role)
    rb.set_timeout(timeout)

    if role == "leader":
        rb.set_leader_id(leader_id)
        if followers_file:
            rb.set_followers_file(followers_file)
    else:
        rb.set_follower_id(follower_id)
        rb.set_leader_id(leader_id)

    if redis_server:
        rb.set_redis_server(redis_server)
    if redis_password:
        rb.set_redis_password(redis_password)
    if abort:
        rb.set_abort(True)
    if msgs_log_file:
        rb.set_message_log(msgs_log_file)
    if messages:
        rb.set_user_messages(messages)

    watchdog = "enabled" if connection_watchdog else "disabled"
    rb.set_connection_watchdog(watchdog)

    rc = rb.run_it()

    if rc != ROADBLOCK_EXITS["success"]:
        logger.error("Roadblock '%s' failed with rc=%d", label, rc)
    else:
        logger.info("Roadblock '%s' completed successfully", label)

    messages_data = None
    if msgs_log_file and os.path.exists(msgs_log_file):
        import json
        try:
            with open(msgs_log_file) as f:
                messages_data = json.load(f)
        except (json.JSONDecodeError, OSError):
            logger.warning("Could not read roadblock messages from %s", msgs_log_file)

    return rc, messages_data
