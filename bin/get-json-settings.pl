#!/usr/bin/perl
# -*- mode: perl; indent-tabs-mode: nil; perl-indent-level: 4 -*-
# vim: autoindent tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=perl

use strict;
use warnings;

BEGIN {
    if (!(exists $ENV{'TOOLBOX_HOME'} && -d "$ENV{'TOOLBOX_HOME'}/perl")) {
        print "This script requires libraries that are provided by the toolbox project.\n";
        print "Toolbox can be acquired from https://github.com/perftool-incubator/toolbox and\n";
        print "then use 'export TOOLBOX_HOME=/path/to/toolbox' so that it can be located.\n";
        exit 1;
    }
}
use lib "$ENV{'TOOLBOX_HOME'}/perl";
use toolbox::jsonsettings;

my $json_settings_file = "";
my $json_settings_query = "";

while (scalar(@ARGV) > 0) {
    my $param = shift(@ARGV);

    my $arg;
    my $val;

    if ($param =~ /^--(\S+)/) {
        $arg = $1;
        if ($arg =~ /^(\S+)=(.*)/) { # '--arg=val'
            $arg = $1;
            $val = $2;
        } else { # '--arg val'
            $val = shift(@ARGV);
        }
    } else {
        printf STDERR "ERROR: malformed parameter: %s\n", $param;
        exit 1;
    }

    if ($arg eq "settings") {
        $json_settings_file = $val;
    } elsif ($arg eq "query") {
        $json_settings_query = $val;
    }
}

if ($json_settings_file eq "") {
    print STDERR "ERROR: you must supply a JSON settings file using --settings\n";
    exit 1;
}

if ($json_settings_query eq "") {
    print STDERR "ERROR: you must supply a JSON settings query using --query\n";
    exit 1;
}

my $rc;
my $json_settings;
my $json_settings_value;

($rc, $json_settings) = load_json_settings($json_settings_file);

if ($rc != 0) {
    printf STDERR "ERROR: failed to load JSON settings from '%s'\n", $json_settings_file;
    exit 1;
}

($rc, $json_settings_value) = get_json_setting($json_settings_query, $json_settings);

if ($rc != 0) {
    printf STDERR "ERROR: JSON query '%s' failed\n", $json_settings_query;
    exit 1;
}

printf "%s\n", $json_settings_value;

exit 0;
