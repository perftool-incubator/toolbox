#!/usr/bin/python3

import argparse
import copy
import re
import logging
from pathlib import Path

import sys
import os
TOOLBOX_HOME = os.environ.get('TOOLBOX_HOME')
if TOOLBOX_HOME is None:
    print("This script requires libraries that are provided by the toolbox project.")
    print("Toolbox can be acquired from https://github.com/perftool-incubator/toolbox and")
    print("then use 'export TOOLBOX_HOME=/path/to/toolbox' so that it can be located.")
    exit(1)
else:
    p = Path(TOOLBOX_HOME) / 'python'
    if not p.exists() or not p.is_dir():
        print("ERROR: <TOOLBOX_HOME>/python ('%s') does not exist!" % (p))
        exit(2)
    sys.path.append(str(p))
from toolbox.metrics import *

def main():
    desc = {'class': 'throughput', 'source': 'ovs', 'type': 'packets-sec'}
    names = {'bridge': 'br0', 'interface': 'p2p1', 'direction': 'tx'}
    sample = {'end': 15000, 'value': 1000}
    log_sample("0", desc, names, sample)
    names = {'bridge': 'br0', 'interface': 'p2p2', 'direction': 'tx'}
    sample = {'end': 15000, 'value': 1000}
    log_sample("0", desc, names, sample)
    names = {'bridge': 'br0', 'interface': 'eno1', 'direction': 'tx'}
    sample = {'end': 15000, 'value': 0}
    log_sample("0", desc, names, sample)
    names = {'bridge': 'br0', 'interface': 'p2p1', 'direction': 'tx'}
    sample = {'end': 16000, 'value': 1000}
    log_sample("0", desc, names, sample)
    names = {'bridge': 'br0', 'interface': 'p2p2', 'direction': 'tx'}
    sample = {'end': 16000, 'value': 1100}
    log_sample("0", desc, names, sample)
    names = {'bridge': 'br0', 'interface': 'eno1', 'direction': 'tx'}
    sample = {'end': 16000, 'value': 0}
    log_sample("0", desc, names, sample)
    finish_samples()

    desc = {'class': 'throughput', 'source': 'ovs', 'type': 'bytes-sec'}
    names = {'bridge': 'br0', 'interface': 'p2p1', 'direction': 'tx'}
    sample = {'end': 15000, 'value': 10000}
    log_sample("1", desc, names, sample)
    names = {'bridge': 'br0', 'interface': 'p2p2', 'direction': 'tx'}
    sample = {'end': 15000, 'value': 10000}
    log_sample("1", desc, names, sample)
    names = {'bridge': 'br0', 'interface': 'p2p1', 'direction': 'tx'}
    sample = {'end': 16000, 'value': 10000}
    log_sample("1", desc, names, sample)
    names = {'bridge': 'br0', 'interface': 'p2p2', 'direction': 'tx'}
    sample = {'end': 16000, 'value': 11000}
    log_sample("1", desc, names, sample)
    finish_samples()

if __name__ == "__main__":
    exit(main())
