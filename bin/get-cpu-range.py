#!/bin/python3

import os
from pathlib import Path
import sys

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

from toolbox.system_cpu_topology import system_cpu_topology as topology

def main():
    if len(sys.argv) != 2:
        print("Usage: python get_cpu_range.py <comma-separated-list>")
        print("\tExample: python get_cpu_range.py 0,1,5,10,12,11")
        print("\t0-1,5,10-12")
        sys.exit(1)

    # argv[1]="1,2,3"
    # Convert into a list of integer numbers: cpu_list=[1,2,3]
    cpu_list=list(map(int, sys.argv[1].split(',')))
    # Get cpu range: cpu=['1-3']
    cpus=topology.formatted_cpu_list(cpu_list)
    # Convert back into a cpu range string: cpu_range="1-3"
    cpu_range=",".join(map(str, cpus))
    # Stdout: 1-3
    print(cpu_range)

if __name__ == "__main__":
    main()
