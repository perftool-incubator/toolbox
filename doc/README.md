# get-json-config.py
get-json-config.py is a python utility to get settings from a json
config file.

## mv-params
```
python3 get-json-config.py --json ~/crucible-run.json.example --config mv-params
{
    "global-options": [
        {
            "name": "common-params",
            "params": [
                {
                    "arg": "rw",
                    "vals": [
                        "read",
                        "write"
                    ]
                }
            ]
        }
    ],
    "sets": [
        {
            "enabled": "yes",
            "include": "common-params",
            "params": [
                {
                    "arg": "ioengine",
                    "vals": [
                        "sync"
                    ]
                }
            ]
        },
        {
            "include": "common-params",
            "params": [
                {
                    "arg": "bs",
                    "vals": [
                        "4K",
                        "16K"
                    ]
                }
            ]
        }
    ]
}

## tool-params
```
python3 get-json-config.py --json ~/crucible-run.json.example --config tool-params
{}
```

## Invalid config
```
python3 get-json-config.py --json crucible-run.json.example --config another-config
usage: get-json-config.py [-h] [--json JSON_FILE] --config
                          {mv-params,tool-params,passthru-args}
get-json-config.py: error: argument --config: invalid choice: 'another-config' (choose from 'mv-params', 'tool-params', 'passthru-args')
```


