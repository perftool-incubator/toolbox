# -*- mode: perl; indent-tabs-mode: nil; perl-indent-level: 4 -*-
# vim: autoindent tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=perl

package toolbox::logging;

use Exporter qw(import);
our @EXPORT = qw(debug_log log_print log_print_error);

use strict;
use warnings;

our $debug = 0;

sub __debug_print_log_location {
    my ($fh, $fdnum, $caller0_ref, $caller1_ref) = @_;

    # note: caller(<int>) can break due to optimization for <int> > 1
    # so we let the caller of this subroutine issue caller so that
    # we don't have to issue caller(2)

    my $file = $caller0_ref->[1];
    my $line = $caller0_ref->[2];

    my $routine = $caller1_ref->[3];
    if (not defined $routine) {
        $routine = "<unknown>";
    } else {
        $routine =~ s/^main:://;
    }

    my $location_data = sprintf "File: %s | Line: %s | Routine: %s", $file, $line, $routine;
    __log_print($fh, $fdnum, sprintf "[DEBUG1] %s\n", $location_data);
}

sub log_print {
    my ($str) = @_;

    if ($toolbox::logging::debug) {
        my @caller0 = caller(0);
        my @caller1 = caller(1);
        __debug_print_log_location(\*STDOUT, 1, \@caller0, \@caller1);

        $str = "[STDOUT] " . $str;
    }

    __log_print(\*STDOUT, 1, $str);
}

sub log_print_error {
    my ($str) = @_;

    if ($toolbox::logging::debug) {
        my @caller0 = caller(0);
        my @caller1 = caller(1);
        __debug_print_log_location(\*STDERR, 2, \@caller0, \@caller1);

        $str = "[STDERR] " . $str;
    }

    __log_print(\*STDERR, 2, $str);
}

# write the message to the specified filename and die
sub __logged_die {
    my ($filename, $str) = @_;

    if (open(my $fh, ">", $filename)) {
        print $fh $str;
        close($fh);
    }

    die($str);
}

# this subroutine is meant to handle cases where prints to a file
# handle are failing.  We believe this is because of back pressure
# from the associated device (ie. the terminal).  Retries along with
# re-opening the file handle appear to be the appropriate work around
# at this time.
sub __log_print {
    my ($fh, $fdnum, $str) = @_;

    my $max_attempts = 6;
    my $total_open_attempts = 0;
    my $attempts = 1;
    my $ret = 0;
    while ((! $ret) && ($attempts <= $max_attempts)) {
        $ret = print $fh $str;

        if (! $ret) {
            if ($attempts > ($max_attempts / 2)) {
                sleep 1;
            }

            my $open_attempts = 1;
            while (!open($fh, ">&" . $fdnum)) {
                $open_attempts++;

                if ($open_attempts > $max_attempts) {
                    last;
                }

                if ($open_attempts > ($max_attempts / 2)) {
                    sleep 1;
                }
            }
            $total_open_attempts += $open_attempts;
        }

        $attempts++;
    }

    my $logged_die_filename = "/tmp/toolbox_logged_die.txt";

    if (! $ret) {
        __logged_die($logged_die_filename, "Failed to print '" . $str . "' to STDOUT after " . $attempts . " attempts and " . $total_open_attempts . " total open attempts!\n");
    } else {
        $attempts--;

        if (($attempts > 1) || ($total_open_attempts > 1))  {
            $ret = print $fh "[PRINT WARNING] Previous line took " . $attempts . " attempts and " . $total_open_attempts . "  total open attempts to print after a perl print error!\n";
            if (! $ret) {
                __logged_die($logged_die_filename, "Failed to print the print warning!\n");
            }
        }
    }
}

sub debug_log {
    if ($toolbox::logging::debug) {
        my $log_str = shift;

        my @caller0 = caller(0);
        my @caller1 = caller(1);
        __debug_print_log_location(\*STDOUT, 1, \@caller0, \@caller1);

        my @log_str_lines = split(/\n/, $log_str);
        for (my $i=0; $i<scalar(@log_str_lines); $i++) {
            __log_print(\*STDOUT, 1, sprintf "[DEBUG2] %s\n", $log_str_lines[$i]);
        }
    }
}

1;
