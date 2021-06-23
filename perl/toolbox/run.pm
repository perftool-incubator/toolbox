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

    if ($cmd !~ /2>&1/) {
        $cmd .= " 2>&1";
    }

    my $cmd_output = `$cmd`;
    my $cmd_rc = $? >> 8;

    return ($cmd, $cmd_output, $cmd_rc);
}

1;
