# -*- mode: perl; indent-tabs-mode: nil; perl-indent-level: 4 -*-
# vim: autoindent tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=perl

package toolbox::run;

use toolbox::logging;

use Exporter qw(import);
our @EXPORT = qw(run_cmd);

use strict;
use warnings;

sub run_cmd {
    my $cmd = shift;

    my $tmp_file = `mktemp`;
    chomp($tmp_file);
    my $tmp_cmd = $cmd . " > $tmp_file";

    my $foo = `$tmp_cmd 2>&1`;
    my $cmd_rc = $? >> 8;

    my $cmd_output = "";
    if (open my $fh, '<', $tmp_file) {
        while (<$fh>) {
            $cmd_output .= $_;
        }
        close $fh;
    } else {
        $cmd_output = sprintf "Failed to open %s to read the output from \"%s\"!\n", $tmp_file, $cmd;
    }

    return ($cmd, $cmd_output, $cmd_rc);
}

1;
