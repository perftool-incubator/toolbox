# -*- mode: perl; indent-tabs-mode: nil; perl-indent-level: 4 -*-
# vim: autoindent tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=perl

package toolbox::json;

use Data::Dumper;
use JSON::XS;
use JSON::Validator;
use IO::Compress::Xz;
use IO::Uncompress::UnXz;
use toolbox::logging;

use Exporter qw(import);
our @EXPORT = qw(put_json_file get_json_file open_write_text_file open_read_text_file);

use strict;
use warnings;

sub open_write_text_file {
    my $filename = shift;
    chomp $filename;
    if (! defined $filename) {
        # filename not defined
        return 1;
    }
    if ($filename =~ /\.xz$/) {
        debug_log(sprintf "file [%s] already named for compression\n", $filename);
    } else {
        # Always default to compression when writing
        $filename .= ".xz";
        debug_log(sprintf "Changed filename to [%s]\n", $filename);
    }
    debug_log(sprintf "trying to open [%s] for writing\n", $filename);
    my $fh = new IO::Compress::Xz $filename;
    if (! defined $fh) {
        # cannot open file;
        return 3;
    }
    return $fh;
}

sub open_read_text_file {
    my $filename = shift;
    my $rc = 0;
    chomp $filename;
    if (! defined $filename) {
        # filename not defined
        $rc = 1;
    }
    if (-e $filename . ".xz") {
        if (-e $filename) {
            debug_log(sprintf "open_read_text_file(): both [%s] and [%s] exist, reading [%s]\n", $filename, $filename . ".xz", $filename . ".xz");
        }
        $filename .= ".xz";
    } elsif (! -e $filename ) {
        # file not found
        $rc = 2;
    }
    debug_log(sprintf "open_read_text_file(): trying to open [%s]\n", $filename);
    my $fh = new IO::Uncompress::UnXz $filename, Transparent => 1;
    if (! defined $fh) {
        # cannot open file
        $rc = 3;
    }
    return ($rc, $fh);
}

sub validate_schema {
    my $schema_filename = shift;
    my $filename = shift;
    my $json_ref = shift;
    if (defined $schema_filename) {
        chomp $schema_filename;
        my $jv = JSON::Validator->new;
        (my $rc, my $schema_fh) = open_read_text_file($schema_filename);
        if ($rc == 0 and defined $schema_fh) {
            my $json_schema_text;
            while ( <$schema_fh> ) {
                $json_schema_text .= $_;
            }
            close($schema_fh);
            chomp $json_schema_text;
            if ($jv->schema($json_schema_text)) {
                debug_log(sprintf "Going to validate schema with [%s]\n", $schema_filename);
                my @errors = $jv->validate($json_ref);
                if (scalar @errors >  0) {
                    printf "Validation errors for file %s with schema %s:\n", $filename, $schema_filename;
                    print Dumper \@errors;
                    # data validation failed
                    return 5;
                }
            } else {
                # schema invalid
                return 4;
            }
        } elsif ($rc == 1) {
            # schema file name undefined
            return 1;
        } elsif ($rc == 2) {
            # schema file not found
            return 2;
        } elsif ($rc == 3) {
            # cannot open schema file
            return 3;
        }
    }
    # no schema or data json validated
    return 0;
}

sub put_json_file {
    my $filename = shift;
    chomp $filename;
    my $json_ref = shift;
    my $schema_filename = shift;
    my $coder = JSON::XS->new->canonical->pretty;
    my $result = validate_schema($schema_filename, $filename, $json_ref);
    if ($result == 0) {
        my $json_text = $coder->encode($json_ref);
        if (! defined $json_text) {
            # data json invalid
            return 6;
        }
        (my $rc, my $json_fh) = open_write_text_file($filename);
        if ($rc == 0 and defined $json_fh) {
            printf $json_fh "%s", $json_text;
            close($json_fh);
            # all good
            return 0;
        } elsif ($rc == 1) {
            # data file name undefined
            return 7;
        } elsif ($rc == 3) {
            # cannot open data file
            return 9;
        } else {
            # something else
            return $rc;
        }
    } elsif ($result == 1) {
        # schema file name undefined
        return 1
    } elsif ($result == 2) {
        # schema file not found
        return 2;
    } elsif ($result == 3) {
        # cannot open schema file
        return 3;
    } elsif ($result == 4) {
        # schema invalid
        return 4;
    } elsif ($result == 4) {
        # validation failed
        return 5;
    } else {
        # something else
        return $result;
    }
}

sub get_json_file {
    my $filename = shift;
    my $schema_filename = shift;
    chomp $filename;
    my $json_ref;
    my $coder = JSON::XS->new;
    (my $rc, my $json_fh) = open_read_text_file($filename);
    if ($rc == 0 and defined $json_fh) {
        my $json_text = "";
        while ( <$json_fh> ) {
            $json_text .= $_;
        }
        close($json_fh);
        chomp $json_text;
        my $json_ref = $coder->decode($json_text);
        if (not defined $json_ref) {
            # data json invalid
            return (6, $json_ref);
        }
        my $result = validate_schema($schema_filename, $filename, $json_ref);
        if ($result == 0) {
            # all good, return the json hash reference
            return (0, $json_ref);
        } elsif ($result == 1) {
            # schema file undefined
            return (1, $json_ref);
        } elsif ($result == 2) {
            # schema not found
            return (2, $json_ref);
        } elsif ($result == 3) {
            # cannot open schema file
            return (3, $json_ref);
        } elsif ($result == 4) {
            # schema invalid
            return (4, $json_ref);
        } elsif ($result == 4) {
            # validation failed
            return (5, $json_ref);
        } else {
            # something else
            return ($result, $json_ref);
        }
    } elsif ($rc == 1) {
        # data file name undefined
        return (7, $json_ref);
    } elsif ($rc == 2) {
        # data file not found
        return (8, $json_ref);
    } elsif ($rc == 3) {
        # cannot open data file
        return (9, $json_ref);
    } else {
        # something else
        return ($rc, $json_ref);
    }
}

1;
