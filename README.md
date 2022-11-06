# toolbox
The toolbox project contains code libraries and scripts to be shared across the [crucible](https://github.com/perftool-incubator/crucible) family of [subprojects](https://github.com/perftool-incubator).

Language(s) supported include:

- [bash](bash/)
- [perl](perl/)
- [python](python/)

Scripts are located in [bin](bin/).


## get-json-config.py

The "get-json-config.py" utility extracts a configuration section from the
"all-in-one" JSON file. With the inner blocks of settings Crucible is capable
of running tests using a single configuration file through the --from-file
argument. The script can be called as follows:

```
# python3 get-json-config.py --json <all-in-one-json> --config <config>
```
Example:
```
# python3 get-json-config.py --json all-in-one.json --config mv-params
```

For more options and usage run:
```
# python3 get-json-config.py --help
```

### All-in-one JSON

The "all-in-one" JSON enables test configuration by using a single JSON file.
Users can specify multi-value parameters, tools, tags, endpoint, and passthru
arguments in JSON format, everything in the same file. An example is shown
below:

```
{
    "mv-params": {
        "global-options": [
            {
                "name": "common-params",
                "params": [
                    { "arg": "duration", "vals": [ "10" ], "role": "client" },
                    { "arg": "rtprio", "vals": [ "1" ], "role": "client" }
                ]
            }
        ],
        "sets": [
            {
                "include": "common-params"
            }
        ]
    },
    "tool-params": [
        {
            "tool": "sysstat",
            "params": [
                { "arg": "subtools", "val": "mpstat", "enabled": "yes" }
            ]
        }
    ],
    "tags": {
        "run": "single-jsonTAGS"
    },
    "endpoint": {
        "k8s": "",
        "COMMON_ENDPOINT_ARGS": "",
        "COMMON_K8S_ENDPOINT_ARGS": "",
        "client": "1-2",
        "server": "1",
        "cpu-partitioning": "default:1",
        "securityContext": "client-1:SCRIPT_DIR/k8s-endpoint/securityContext-oslat.json",
        "securityContext": "client-2:SCRIPT_DIR/k8s-endpoint/securityContext-oslat.json"
    },
    "passthru-args": ""
}
```

For more details on the supported format, refer to the JSON [schema](JSON/schema.json).
