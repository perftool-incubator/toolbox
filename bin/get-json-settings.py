#!/usr/bin/python3

import argparse
import logging
import re

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
from toolbox.json import *
from toolbox.jsonsettings import *

def process_options():
    parser = argparse.ArgumentParser(description="Extract a settings value from a JSON config file")

    parser.add_argument("--log-level",
                        dest = "log_level",
                        help = "Control how much logging output should be generated",
                        default = "normal",
                        choices = [ "normal", "verbose", "debug" ])

    parser.add_argument("--settings-file",
                        dest = "settings_file",
                        help = "Which file should be loaded to extract a value from",
                        required = True,
                        type = str)

    parser.add_argument("--query",
                        dest = "query",
                        help = "The query to run to find the desired settings property",
                        required = True,
                        type = str)

    the_args = parser.parse_args()

    return the_args


def main():
    log_debug_format =    '[%(asctime)s %(levelname)s %(module)s %(funcName)s:%(lineno)d] %(message)s'
    log_verbose_format =  '[%(asctime)s %(levelname)s] %(message)s'
    log_normal_format =    '%(message)s'

    if args.log_level == 'debug':
        logging.basicConfig(level = logging.DEBUG, format = log_debug_format, stream = sys.stderr)
    elif args.log_level == 'verbose':
        logging.basicConfig(level = logging.INFO, format = log_verbose_format, stream = sys.stderr)
    elif args.log_level == 'normal':
        logging.basicConfig(level = logging.INFO, format = log_normal_format, stream = sys.stderr)

    logger = logging.getLogger(__file__)

    lzma = False
    m = re.search(r"\.xz$", args.settings_file)
    if m:
        lzma = True

    settings,err_msg = load_json_file(args.settings_file, uselzma = lzma)
    if err_msg is not None:
        logger.error(f"ERROR: failed to load JSON settings from {args.settings_file}")
        logger.error(f"       Reason is: {err_msg}")
        return 1
    else:
        logger.info(f"Loaded JSON settings from {args.settings_file}")

    value,error_no = get_json_setting(settings, args.query)
    if error_no != 0:
        logger.error(f"ERROR: JSON query '{args.query}' failed")
        return 1
    else:
        logger.info(f"JSON query '{args.query}' returned '{value}'")

    print(value);

    return 0

if __name__ == "__main__":
    args = process_options()
    logger = None
    
    exit(main())
