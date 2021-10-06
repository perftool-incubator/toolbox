#!/usr/bin/python3

'''Python bin script template'''

import argparse
import sys
from dataclasses import dataclass


@dataclass
class global_vars:
    '''Global variables'''

    args = None
    global1 = 5
    global2 = 'bar'


def process_options():
    '''Define the CLI argument parsing options'''

    parser = argparse.ArgumentParser(description="Python bin script template")

    parser.add_argument("--arg1",
                        dest = "arg1",
                        help = "First argument",
                        type = int,
                        default = 0)

    parser.add_argument("--arg2",
                        dest = "arg2",
                        help = "Second argument",
                        type = str,
                        default = 'foo')

    myglobal.args = parser.parse_args()


def main():
    '''Primary base function'''

    process_options()

    print("global1 value is '%d'" % (myglobal.global1))
    print("global2 value is '%s'" % (myglobal.global2))
    print("arg1 value is '%d'" % (myglobal.args.arg1))
    print("arg2 value is '%s'" % (myglobal.args.arg2))

    return 0


if __name__ == "__main__":
    myglobal = global_vars()
    sys.exit(main())
