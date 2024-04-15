import json
import lzma

from jsonschema import validate
from jsonschema import exceptions


def load_json_file(json_file, uselzma = False):
    """Load JSON file and return a json object/error msg tuple"""
    err_msg = None
    try:
        if uselzma:
            input_fp = lzma.open(json_file, 'rt')
        else:
            input_fp = open(json_file, 'r')
        input_json = json.load(input_fp)
        input_fp.close()
        return input_json, None
    except FileNotFoundError as err:
        err_msg = f"Could not find JSON file { json_file }:{ err }"
    except IOError as err:
        err_msg = "Could not open/read JSON file { json_file }:{ err }"
    except Exception as err:
        err_msg = f"Unexpected error opening JSON file { json_file }:{ err }"
    except JSONDecodeError as err:
        err_msg = f"Decoding JSON file %s has failed: { json_file }:{ err }"
    except TypeError as err:
        err_msg = f"JSON object type error: { err }"
    return None, err_msg

def validate_schema(input_json, schema_file):
    """Validate json with schema file"""
    err_msg = None

    try:
        schema_obj, err_msg = load_json_file(schema_file)
        if schema_obj is None:
            return False, err_msg
        validate(instance = input_json, schema = schema_obj)
    except Exception as err:
        err_msg = f"JSON schema validation error: { err }"
        return False, err_msg
    return True, err_msg
