# -*- mode: python; indent-tabs-mode: nil; python-indent-level: 4 -*-
# vim: autoindent tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=python

import json
import logging
import os
from pathlib import Path

from toolbox.json import load_json_file


logger = logging.getLogger(__name__)

ROADBLOCK_EXITS = {
    "success": 0,
    "input": 2,
    "timeout": 3,
    "abort": 4,
    "abort_waiting": 6,
}


def create_roadblock_msg(recipient_type, recipient_id, payload_type, payload):
    """Build a roadblock user message.

    Args:
        recipient_type: "leader", "follower", or "all"
        recipient_id: specific name/ID of the intended recipient
        payload_type: the key name for the payload (e.g., "user-object")
        payload: the message content

    Returns:
        A list containing the message dict (roadblock expects a list).
    """
    msg = [
        {
            "recipient": {
                "type": recipient_type,
                "id": recipient_id,
            },
            payload_type: payload,
        }
    ]

    logger.info(
        "Creating roadblock message for recipient type '%s' id '%s'",
        recipient_type, recipient_id,
        stacklevel=2,
    )

    return msg


def prepare_user_msgs_file(tx_msgs_dir, output_dir, roadblock_name,
                           default_recipients=None):
    """Collect queued messages from a tx directory and bundle them for roadblock.

    Scans tx_msgs_dir for message files. Each file should contain a JSON
    list of message dicts. Messages that already have a "recipient" key are
    passed through as-is. Raw payloads (no "recipient" key) are wrapped
    with addressing to each (type, id) pair in default_recipients.

    Processed files are moved to {tx_msgs_dir}-sent/.

    Args:
        tx_msgs_dir: directory containing outgoing message files
        output_dir: directory where the bundled message file is written
        roadblock_name: used to name the output file
        default_recipients: optional list of (type, id) tuples for wrapping
            raw payloads that lack a "recipient" key

    Returns:
        Path to the bundled message file, or None if no messages were queued.
    """
    if not os.path.isdir(tx_msgs_dir):
        logger.info("tx_msgs_dir %s does not exist, no messages to send", tx_msgs_dir)
        return None

    queued_files = sorted(os.listdir(tx_msgs_dir))
    if not queued_files:
        logger.info("No queued messages found in %s", tx_msgs_dir)
        return None

    logger.info("Found queued messages in %s, preparing them to send", tx_msgs_dir)

    tx_sent_dir = tx_msgs_dir + "-sent"
    os.makedirs(tx_sent_dir, exist_ok=True)

    user_msgs = []
    for filename in queued_files:
        filepath = os.path.join(tx_msgs_dir, filename)
        if not os.path.isfile(filepath):
            continue

        logger.info("Importing %s", filepath)

        msg_data, err = load_json_file(filepath)
        if msg_data is None:
            logger.error("Failed to load messages from %s: %s", filepath, err)
            continue

        if isinstance(msg_data, list):
            for item in msg_data:
                if "recipient" in item:
                    user_msgs.append(item)
                elif default_recipients:
                    _wrap_raw_payload(user_msgs, item, default_recipients)
                else:
                    user_msgs.append(item)
        elif isinstance(msg_data, dict):
            if "recipient" in msg_data:
                user_msgs.append(msg_data)
            elif default_recipients:
                _wrap_raw_payload(user_msgs, msg_data, default_recipients)
            else:
                user_msgs.append(msg_data)

        dest = os.path.join(tx_sent_dir, filename)
        logger.info("Moving message file from %s to %s", filepath, dest)
        os.replace(filepath, dest)

    if not user_msgs:
        return None

    msgs_file = os.path.join(output_dir, "rb-msgs-%s.json" % roadblock_name)
    logger.info("Writing %d user message(s) to %s", len(user_msgs), msgs_file)

    with open(msgs_file, "w", encoding="ascii") as fp:
        json.dump(user_msgs, fp, indent=4, sort_keys=True)

    return msgs_file


def _wrap_raw_payload(msgs_list, payload, recipients):
    """Wrap a raw payload dict with addressing for each recipient."""
    for rtype, rid in recipients:
        msgs_list.append({
            "recipient": {
                "type": rtype,
                "id": rid,
            },
            "user-object": payload,
        })


def evaluate_roadblock_result(roadblock_rc, roadblock_name, msgs_dir,
                              engine_label=None, buddy_label=None):
    """Evaluate a completed roadblock and extract received messages.

    Checks the roadblock return code for timeout/abort conditions and
    parses the message log for user-object messages addressed to this
    engine (or broadcast from buddy for legacy compatibility).

    Args:
        roadblock_rc: return code from the roadblock
        roadblock_name: name of the completed roadblock
        msgs_dir: directory containing roadblock message logs
        engine_label: if set, extract messages addressed to this label
        buddy_label: if set, also accept broadcast messages from this sender

    Returns:
        A dict with keys:
            "is_timeout" (bool): roadblock timed out
            "is_abort" (bool): roadblock received an abort
            "messages" (list): extracted user-object message dicts
    """
    result = {
        "is_timeout": False,
        "is_abort": False,
        "messages": [],
    }

    if roadblock_rc != ROADBLOCK_EXITS["success"]:
        if roadblock_rc == ROADBLOCK_EXITS["timeout"]:
            logger.error(
                "Roadblock '%s' timed out, attempting to exit cleanly",
                roadblock_name,
            )
            result["is_timeout"] = True
        elif roadblock_rc == ROADBLOCK_EXITS["abort"]:
            logger.warning(
                "Roadblock '%s' received an abort", roadblock_name,
            )
            result["is_abort"] = True

    msgs_log_file = os.path.join(msgs_dir, "%s.json" % roadblock_name)
    if not os.path.isfile(msgs_log_file):
        return result

    logger.info("Found received messages file: %s", msgs_log_file)

    msgs_json, err = load_json_file(msgs_log_file)
    if msgs_json is None:
        logger.error("Failed to load %s: %s", msgs_log_file, err)
        return result

    received = msgs_json.get("received", [])
    if not received:
        return result

    for msg in received:
        payload = msg.get("payload", {})
        message = payload.get("message", {})

        if message.get("command") != "user-object":
            continue

        user_object = message.get("user-object")
        if user_object is None:
            continue

        recipient = payload.get("recipient", {})
        sender = payload.get("sender", {})

        if engine_label is not None:
            if recipient.get("id") == engine_label:
                result["messages"].append(user_object)
            elif (buddy_label is not None
                  and sender.get("id") == buddy_label
                  and recipient.get("type") == "all"):
                result["messages"].append(user_object)
        else:
            result["messages"].append(user_object)

    logger.info("Found %d message(s) for processing", len(result["messages"]))

    return result


def save_received_messages(messages, rx_msgs_dir, roadblock_label):
    """Save extracted messages to individual files in the rx directory.

    Args:
        messages: list of user-object message dicts
        rx_msgs_dir: directory to write message files
        roadblock_label: base name for the message files

    Returns:
        Number of messages saved.
    """
    for i, msg in enumerate(messages, start=1):
        filename = "%s:%d" % (roadblock_label, i)
        outfile = os.path.join(rx_msgs_dir, filename)
        logger.info("Saving message to %s", outfile)
        with open(outfile, "w", encoding="ascii") as fp:
            json.dump(msg, fp, indent=4, sort_keys=True)

    return len(messages)


def resolve_svc_messages(rx_msgs_dir):
    """Resolve service discovery information from received messages.

    Looks for endpoint-start-end or server-start-end message files and
    creates a "svc" symlink pointing to the resolved file. This is how
    client engines discover server IP/port information.

    Args:
        rx_msgs_dir: directory containing received message files

    Returns:
        Path to the resolved svc symlink, or None if no service info found.
    """
    svc_file = os.path.join(rx_msgs_dir, "svc")

    found = None
    source = None

    for entry in sorted(Path(rx_msgs_dir).iterdir()):
        if entry.name.startswith("endpoint-start-end:") and entry.is_file():
            found = entry
            source = "endpoint"
            break

    if found is None:
        for entry in sorted(Path(rx_msgs_dir).iterdir()):
            if entry.name.startswith("server-start-end:") and entry.is_file():
                found = entry
                source = "server (direct)"
                break

    if found is not None:
        os.symlink(found.name, svc_file)
        logger.info(
            "Resolved service info from %s (%s -> %s)",
            source, svc_file, found.name,
        )
        return svc_file

    logger.info("No service info found to resolve")
    return None
