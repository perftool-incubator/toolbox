#!/usr/bin/python3

'''Utility to dump json section from the crucible run file'''

import os
import argparse
import sys
import json
from jsonschema import validate
from jsonschema import exceptions

def process_options():
    """Handle the CLI argument parsing options"""

    parser = argparse.ArgumentParser(description = "Read a config section from crucible run file")

    parser.add_argument("--json",
                        dest = "json_file",
                        help = "Crucible config settings json file (e.g. crucible-run.json)",
                        type = str)

    parser.add_argument("--config",
                        dest = "config",
                        required = True,
                        help = "Configuration type to get from the json file",
                        choices = [ "mv-params", "tool-params", "passthru-args", "tags", "endpoint" ])

    parser.add_argument("--index",
                        dest = "index",
                        help = "Crucible config index (e.g. 2 => endpoint[2]",
                        default = 0,
                        type = int)

    args = parser.parse_args()
    return args

def dump_json(obj, key, format = 'readable'):
    """Dump json in readable or parseable format"""
    # Parseable format has no indentation
    indentation = None
    sep = ':'
    if format == 'readable':
        indentation = 4
        sep += ' '

    try:
        json_str = json.dumps(obj[key], indent = indentation, separators = (',', sep),
                              sort_keys = False)
        return json_str
    except KeyError:
        return None

def load_json_file(json_file):
    """Load JSON file and return a json object"""
    try:
         input_fp = open(json_file, 'r')
         input_json = json.load(input_fp)
         input_fp.close()
    except FileNotFoundError as err:
         print("Could not find JSON file %s: %s" % (json_file, err))
         return None
    except IOError as err:
         print("Could not open/read JSON file %s: %s" % (json_file, err))
         return None
    except Exception as err:
         print("Unexpected error opening JSON file %s: %s" % (json_file, err))
         return None
    except JSONDecodeError as err:
         print("Decoding JSON file %s has failed: %s" % (json_file, err))
         return None
    except TypeError as err:
         print("JSON object type error: %s" % (err))
         return None
    return input_json

def json_to_stream(json_obj, cfg, idx):
    """Parse key:value from a JSON object/block and transform into a stream"""
    stream = ""
    err_msg = None
    if json_obj is None:
        return None

    try:
        # arrays w/ multiple key:value objects e.g. "endpoint" block
        if isinstance(json_obj[cfg], list):
            json_blk = json_obj[cfg][idx]
        else:
            # single object w/ key:value pairs e.g. "tags" block
            json_blk = json_obj[cfg]
    except IndexError as err:
        err_msg="{} => Invalid index: {} block has {} element(s).".format(
                        err, cfg, len(json_obj[cfg]))
    except Exception as err:
        err_msg="{} => Failed to convert block {} into stream.".format(
                        err, cfg)

    if err_msg is not None:
        print("ERROR: %s" % (err_msg))
        return None

    for key in json_blk:
        val = json_blk[key]
        #if isinstance(val, str) or isinstance(val, unicode):
        if isinstance(val, list):
            for idx in range(len(val)):
                item_val = val[idx]
                stream += key + ":" + item_val + ","
        else:
            try:
                val_str = str(val)
                if len(key) > 0:
                    stream += key + ":"
                stream += val_str + ","
            except:
                raise Exception("Error: Unexpected object type %s" % (type(val)))
                return None

    # remove last ","
    if len(stream)>0:
        stream = stream[:-1]

    return stream

def validate_schema(input_json):
    """Validate json with schema file"""

    SCHEMA_FILE = "%s/../JSON/schema.json" % (os.path.dirname(os.path.abspath(__file__)))
    try:
        schema_fp = open(SCHEMA_FILE, 'r')
        schema_contents = json.load(schema_fp)
        schema_fp.close()
        validate(instance = input_json, schema = schema_contents)
    except Exception as err:
        print("JSON schema validation error: %s" % (err))
        return False
    return True

def main():
    """Main function of get-json-config.py tool"""

    global args

    input_json = load_json_file(args.json_file)
    if input_json is None:
        return 1

    if not validate_schema(input_json):
        return 1

    if args.config == "endpoint" or args.config == "tags":
        output = json_to_stream(input_json, args.config, args.index)
    else:
        output = dump_json(input_json, args.config)
    print(output)

if __name__ == "__main__":
    args = process_options()
    exit(main())

