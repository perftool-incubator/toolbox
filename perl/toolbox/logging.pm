# -*- mode: perl; indent-tabs-mode: t; perl-indent-level: 4 -*-
# vim: autoindent tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=perl

package toolbox::logging;

use Exporter qw(import);
our @EXPORT = qw(debug_log);

use strict;
use warnings;

our $debug = 0;

sub debug_log {
    if ($toolbox::logging::debug) {
        print "[DEBUG]" . shift;
    }
}

1;
