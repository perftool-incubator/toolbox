#!/usr/bin/python3

'''Convert CPU list(s) to CPU masks'''

import argparse
from dataclasses import dataclass


@dataclass
class global_vars:
    '''Global variables'''

    args = None


def process_options():
    '''Define the CLI argument parsing options'''

    parser = argparse.ArgumentParser(description="CPU mask creator")

    parser.add_argument("--cpus",
                        dest = "cpus",
                        help = "Use one or more times to define CPU and/or CPU lists to include in the mask",
                        action = "append",
                        type = str)
    
    myglobal.args = parser.parse_args()


def linux_hexmask(hexmask):
    '''Convert a hexmask into a Linux sysfs compatible hexmask'''

    block_size = 8
    blocks = int(len(hexmask)/block_size) + (len(hexmask) % block_size > 0)
    padded_hexmask = hexmask.zfill(block_size * blocks)
    linux_hexmask = ",".join([padded_hexmask[i:i+block_size] for i in range(0, len(padded_hexmask)-1, block_size)])
    return(linux_hexmask)


def main():
    process_options()

    cpus = set()
    
    for cpu1 in myglobal.args.cpus:
        for cpu2 in cpu1.split(","):
            cpu3 = cpu2.split("-")
            if len(cpu3) == 1:
                cpus.add(int(cpu3[0]))
            else:
                for cpu4 in range(int(cpu3[0]), int(cpu3[1])+1):
                    cpus.add(cpu4)

    mask = 0
    
    for cpu in cpus:
        bitmask = 1 << cpu
        mask |= bitmask

    print('bitmask={:b}'.format(mask))
    hexmask = '{:x}'.format(mask)
    print('hexmask={:s}'.format(linux_hexmask(hexmask)))


if __name__ == "__main__":
    myglobal = global_vars()
    exit(main())
