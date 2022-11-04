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

    args = parser.parse_args()
    return args

def dump_json(obj, format = 'readable'):
    """Dump json in readable or parseable format"""
    # Parseable format has no indentation
    indentation = None
    sep = ':'
    if format == 'readable':
        indentation = 4
        sep += ' '

    return json.dumps(obj, indent = indentation, separators = (',', sep),
                      sort_keys = False)

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

def json_to_stream(json_str):
    """Parse key:value from a JSON object and transform into a stream"""
    stream=""
    json_obj = json.loads(json_str)
    for key in json_obj:
        val = json_obj[key]
        stream += key
        # keys without values do not add ":" e.g. --endpoint k8s,
        if len(val) > 0:
            stream += ":" + val
        stream += ","
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

    output = dump_json(input_json[args.config])
    if args.config == "tags" or args.config == "endpoint":
        output = json_to_stream(output)
    print(output)

if __name__ == "__main__":
    args = process_options()
    exit(main())

