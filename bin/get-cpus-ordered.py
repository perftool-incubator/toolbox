#!/usr/bin/python3

import argparse
import copy
import logging

import sys
import os
from pathlib import Path
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
from toolbox.system_cpu_topology import *

# define some global variables
class t_global(object):
    args = None
    system_cpus = None
    log_debug_format =    '[%(asctime)s %(levelname)s %(module)s %(funcName)s:%(lineno)d] %(message)s'
    log_verbose_format =  '[%(asctime)s %(levelname)s] %(message)s'
    log_normal_format =    '%(message)s'
    log = None

def process_options():
    parser = argparse.ArgumentParser(description="Order a list of CPUs based on requested topology")

    parser.add_argument("--log-level",
                        dest = "log_level",
                        help = "Control how much logging output should be generated",
                        default = "normal",
                        choices = [ "normal", "verbose", "debug" ])

    parser.add_argument("--smt",
                        dest = "smt_mode",
                        help = "Should siblings be used",
                        default = "off",
                        choices = [ "off", "on" ])

    parser.add_argument("--smt-enumeration",
                        dest = "smt_enumeration",
                        help = "SMT sibling ordering control",
                        default = "grouped",
                        choices = [ "grouped", "separate" ])

    parser.add_argument("--smt-siblings-per-core",
                        dest = "smt_siblings_per_core",
                        help = "How many SMT siblings per core to use",
                        default = 2,
                        type = int,
                        choices = range(1, 8))

    parser.add_argument("--cpu",
                        dest = "cpu_list",
                        help = "One or more CPUs to order",
                        required = True,
                        default = [],
                        action = 'append',
                        type = int)

    t_global.args = parser.parse_args()

    if t_global.args.log_level == 'debug':
        logging.basicConfig(level = logging.DEBUG, format = t_global.log_debug_format, stream = sys.stdout)
    elif t_global.args.log_level == 'verbose':
        logging.basicConfig(level = logging.INFO, format = t_global.log_verbose_format, stream = sys.stdout)
    elif t_global.args.log_level == 'normal':
        logging.basicConfig(level = logging.INFO, format = t_global.log_normal_format, stream = sys.stdout)

    t_global.log = logging.getLogger(__file__)

    if t_global.args.smt_mode == "on" and t_global.args.smt_siblings_per_core == 1:
        t_global.log.info("Disabling SMT since siblings per core is 1")
        t_global.args.smt_mode = "off"

    return(0)

def disable_smt(cpu_list):
    smt_off_list = []

    cpu_set = set(cpu_list)

    for cpu in cpu_list:
        if not cpu in cpu_set:
            t_global.log.debug("disable_smt: skipping cpu '%d' because it has be processed already" % (cpu))
            continue

        cpu_set.remove(cpu)
        smt_off_list.append(cpu)
        
        siblings = t_global.system_cpus.get_thread_siblings(cpu)
        for sibling in siblings:
            if sibling in cpu_set:
                cpu_set.remove(sibling)

    return(smt_off_list)

def configure_smt_enumeration(cpu_list):
    smt_enumeration_list = []
    sibling_lists = []

    cpu_set = set(cpu_list)

    # create sibling_lists -- an array of arrays where each sub-array
    # is a set of siblings that are present
    for cpu in cpu_list:
        if not cpu in cpu_set:
            continue

        cpu_set.remove(cpu)
        
        siblings = t_global.system_cpus.get_thread_siblings(cpu)

        sibling_list = [cpu]

        for sibling in siblings:
            if sibling in cpu_set:
                sibling_list.append(sibling)
                cpu_set.remove(sibling)

        sibling_lists.append(sibling_list)

    # limit the sibling_lists sub-arrays to the number of siblings per
    # core requested
    for sibling_list in sibling_lists:
        if len(sibling_list) <= t_global.args.smt_siblings_per_core:
            pass
        else:
            for idx in range(t_global.args.smt_siblings_per_core, len(sibling_list)):
                sibling_list.pop()

    # order the siblings
    if t_global.args.smt_enumeration == "grouped":
        # in grouped mode, each set of siblings is listed together
        # ie. [x1,x2,y1,y2,z1,z2]
        for sibling_list in sibling_lists:
            smt_enumeration_list.extend(sibling_list)
    elif t_global.args.smt_enumeration == "separate":
        # in separate mode, 1 sibling per core is listed before the
        # sequence starts over
        # ie. [x1,y1,z2,x2,y2,x2]
        process_siblings = True
        while process_siblings:
            process_siblings = False
            for sibling_list in sibling_lists:
                if len(sibling_list) > 0:
                    smt_enumeration_list.append(sibling_list.pop(0))
                    process_siblings = True

    return(smt_enumeration_list)

def main():
    process_options()

    output_list = []
    
    # remove any duplicates from the cpu list
    t_global.args.cpu_list = list(set(t_global.args.cpu_list))

    t_global.system_cpus = system_cpu_topology(log = t_global.log)

    t_global.log.info("all: %s" % (t_global.system_cpus.get_all_cpus()))

    t_global.log.info("online: %s" % (t_global.system_cpus.get_online_cpus()))

    if t_global.args.smt_mode == "on":
        t_global.log.info("SMT is on -> all CPUs from a sibling list are included")
        
        output_list = copy.deepcopy(t_global.args.cpu_list)
    elif t_global.args.smt_mode == "off":
        t_global.log.info("SMT is off -> only including one CPU from each sibling list")

        output_list = disable_smt(t_global.args.cpu_list)

    t_global.log.info("output list: %s" % (output_list))

    if t_global.args.smt_mode == "on":
        t_global.log.info("SMT is on -> using '%s' mode to order SMT siblings" % (t_global.args.smt_enumeration))

        output_list = configure_smt_enumeration(output_list)

    t_global.log.info("output list: %s" % (output_list))

    return(0)

if __name__ == "__main__":
    exit(main())
