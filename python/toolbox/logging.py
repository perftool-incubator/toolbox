# -*- mode: python; indent-tabs-mode: nil; python-indent-level: 4 -*-
# vim: autoindent tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=python

import logging
import sys

VERBOSE = 15
logging.addLevelName(VERBOSE, "VERBOSE")


def _verbose(self, message, *args, **kws):
    if self.isEnabledFor(VERBOSE):
        self._log(VERBOSE, message, args, **kws)


logging.Logger.verbose = _verbose


def setup_logging(name, level="normal"):
    """Configure logging on the root logger and return a named logger.

    Configures the root logger so that all loggers in the process
    (including library loggers like roadblock) inherit the handler
    and level. Callers that want to suppress library output at normal
    level can raise the root logger level after this call while
    keeping their named logger at a lower level.

    Args:
        name: logger name (typically the script name)
        level: "normal", "verbose", "debug", or a Python logging level name

    Returns:
        configured logger instance
    """
    level_map = {
        "normal": logging.INFO,
        "verbose": VERBOSE,
        "debug": logging.DEBUG,
        "warning": logging.WARNING,
        "error": logging.ERROR,
    }

    log_level = level_map.get(level, logging.INFO)

    root = logging.getLogger()
    root.setLevel(log_level)

    format_map = {
        "normal": "%(message)s",
        "verbose": "[%(asctime)s][%(levelname)8s] %(message)s",
        "debug": "[CODE][%(module)s %(funcName)s:%(lineno)d]\n[%(asctime)s][%(levelname) 8s][%(threadName)s] %(message)s",
    }
    fmt = format_map.get(level, "%(message)s")

    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)
        handler.setFormatter(logging.Formatter(fmt))
        root.addHandler(handler)
    else:
        for handler in root.handlers:
            handler.setLevel(log_level)
            handler.setFormatter(logging.Formatter(fmt))

    return logging.getLogger(name)
