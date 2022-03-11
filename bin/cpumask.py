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

    parser = argparse.ArgumentParser(description = "CPU mask creator",
                                     formatter_class = argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("--type",
                        dest = "type",
                        help = "What type of input to process",
                        choices = [ "bitmask", "list", "hexmask" ],
                        default = "list")

    parser.add_argument("--cpus",
                        dest = "cpus",
                        help = "The CPUs to process as input.  The format of this parameter depends on the input type",
                        required = True,
                        default = None,
                        type = str)

    myglobal.args = parser.parse_args()

    return 0


def linux_hexmask(hexmask):
    '''Convert a hexmask into a Linux sysfs compatible hexmask'''

    block_size = 8

    if len(hexmask) <= block_size:
        return hexmask
    else:
        blocks = int(len(hexmask)/block_size) + (len(hexmask) % block_size > 0)
        padded_hexmask = hexmask.zfill(block_size * blocks)
        linux_hexmask = ",".join([padded_hexmask[i:i+block_size] for i in range(0, len(padded_hexmask)-1, block_size)])
        return linux_hexmask


def cpulist(cpus):
    '''Format the cpus for printing'''

    cpulist = ""
    counter = 0
    for cpu in cpus:
        counter += 1

        cpulist += str(cpu)

        if counter != len(cpus):
            cpulist += ","

    return(cpulist)


def parse_hexmask():
    '''Parse the --hexmask input information'''

    cpus = set()

    if myglobal.args.cpus is not None:
        hexmask = ""
        for linux_hexmask_piece in myglobal.args.cpus.split(","):
            hexmask += linux_hexmask_piece

        integer = int("0x" + hexmask, 16)

        cpus = integer_to_set(integer)

    return cpus


def parse_bitmask():
    '''Parse the --bitmask input information'''

    cpus = set()

    if myglobal.args.cpus is not None:
        integer = int(myglobal.args.cpus, 2)
        cpus = integer_to_set(integer)

    return cpus


def integer_to_set(integer):
    '''Convert a binary bitmask to a set of cpus'''

    cpus = set()

    bitmask = '{:b}'.format(integer)
    for cpu in range(0, len(bitmask)):
        mask = 1 << cpu
        if mask & integer:
            cpus.add(cpu)

    return cpus


def parse_cpus():
    '''Parse the --cpus input information'''

    cpus = set()

    if myglobal.args.cpus is not None:
        for cpu2 in myglobal.args.cpus.split(","):
            cpu3 = cpu2.split("-")
            if len(cpu3) == 1:
                cpus.add(int(cpu3[0]))
            else:
                for cpu4 in range(int(cpu3[0]), int(cpu3[1])+1):
                    cpus.add(cpu4)

    return cpus


def set_to_masks(cpus):
    '''Convert the given set of cpus into the various masks and output them'''

    mask = 0
    
    for cpu in cpus:
        bitmask = 1 << cpu
        mask |= bitmask

    hexmask = '{:x}'.format(mask)

    print('cpulist={:s}'.format(cpulist(cpus)))
    print('bitmask={:b}'.format(mask))
    print('hexmask={:s}'.format(linux_hexmask(hexmask)))

    return 0


def main():
    process_options()

    cpus = None

    if myglobal.args.type == "list":
        cpus = parse_cpus()
    elif myglobal.args.type == "hexmask":
        cpus = parse_hexmask()
    elif myglobal.args.type == "bitmask":
        cpus = parse_bitmask()

    if len(cpus) < 1:
        print('ERROR: No valid CPUs to process')
        return 1
    else:
        set_to_masks(cpus)

    return 0


if __name__ == "__main__":
    myglobal = global_vars()
    exit(main())
