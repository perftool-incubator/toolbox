# -*- mode: python; indent-tabs-mode: nil; python-indent-level: 4 -*-
# vim: autoindent tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=python

import invoke


def run_cmd(cmd, check=False):
    """Execute a shell command and return (command, output, rc).

    Matches the Perl toolbox::run run_cmd() interface.

    Args:
        cmd: shell command string
        check: if True, raise on non-zero exit

    Returns:
        tuple of (command_str, combined_output, return_code)
    """
    result = invoke.run(cmd, hide=True, warn=not check)
    output = result.stdout
    if result.stderr:
        output += result.stderr
    return cmd, output, result.return_code
