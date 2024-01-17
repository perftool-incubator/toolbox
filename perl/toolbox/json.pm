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
our @EXPORT = qw(put_json_file get_json_file open_write_text_file open_read_text_file validate_schema);

use strict;
use warnings;

sub open_write_text_file {
    my $filename = shift;
    chomp $filename;
    my $fh;
    if (! defined $filename) {
        debug_log("open_write_text_file(): filename not defined\n");
        return (1, $fh);
    }
    if ($filename =~ /\.xz$/) {
        debug_log(sprintf "open_write_text_file(): file [%s] already named for compression\n", $filename);
    } else {
        # Always default to compression when writing
        $filename .= ".xz";
        debug_log(sprintf "open_write_text_file(): changed filename to [%s]\n", $filename);
    }
    debug_log(sprintf "open_write_text_file(): trying to open [%s] for writing\n", $filename);
    $fh = new IO::Compress::Xz $filename;
    if (! defined $fh) {
        debug_log("open_write_text_file(): cannot open file [%s]\n", $filename);
        return (3, $fh);
    } else {
        return (0, $fh);
    }
}

sub open_read_text_file {
    my $filename = shift;
    my $fh;
    chomp $filename;
    if (! defined $filename) {
        debug_log("open_read_text_file(): filename not defined\n");
        return (1, $fh);
    }
    if (-e $filename . ".xz") {
        if (-e $filename) {
            debug_log(sprintf "open_read_text_file(): both [%s] and [%s] exist, reading [%s]\n", $filename, $filename . ".xz", $filename . ".xz");
        } else {
            debug_log(sprintf "open_read_text_file(): found [%s] but not [%s]\n", $filename . ".xz", $filename);
        }
        $filename .= ".xz";
    } elsif (! -e $filename ) {
        debug_log(sprintf "open_read_text_file(): file not found [%s]\n", $filename);
        return (2, $fh);
    }
    debug_log(sprintf "open_read_text_file(): trying to open [%s]\n", $filename);
    $fh = new IO::Uncompress::UnXz $filename, Transparent => 1;
    if (! defined $fh) {
        debug_log(sprintf "open_read_text_file(): cannot open file [%s]\n", $filename);
        return (3, $fh);
    } else {
        return (0, $fh);
    }
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
                debug_log(sprintf "validate_schema() going to validate schema for [%s] with [%s]\n", $filename, $schema_filename);
                my @errors = $jv->validate($json_ref);
                if (scalar @errors >  0) {
                    printf "validate_schema(): validation errors for file %s with schema %s:\n", $filename, $schema_filename;
                    print Dumper \@errors;
                    return 5;
                } else {
                    return 0;
                }
            } else {
                debug_log(sprintf "validate_schema(): schema invalid [%s]\n", $schema_filename);
                return 4;
            }
        } elsif ($rc == 1) {
            debug_log("validate_schema(): schema file name undefined\n");
            return 1;
        } elsif ($rc == 2) {
            debug_log(sprintf "validate_schema(): schema file not found [%s]\n", $schema_filename);
            return 2;
        } elsif ($rc == 3) {
            debug_log(sprintf "validate_schema(): cannot open schema file [%s]\n", $schema_filename);
            return 3;
        }
    } else {
        return 0;
    }
}

sub put_json_file {
    my $filename = shift;
    chomp $filename;
    my $json_ref = shift;
    my $schema_filename = shift;
    my $coder = JSON::XS->new->canonical->pretty;
    my $result = validate_schema($schema_filename, $filename, $json_ref);
    if ($result == 0) {
        debug_log("put_json_file(): validate_schema passed\n");
        my $json_text = $coder->encode($json_ref);
        if (! defined $json_text) {
            debug_log("put_json_file(): data json invalid\n");
            return 6;
        }
        (my $rc, my $json_fh) = open_write_text_file($filename);
        if ($rc == 0 and defined $json_fh) {
            printf $json_fh "%s", $json_text;
            close($json_fh);
            return 0;
        } elsif ($rc == 1) {
            debug_log("put_json_file(): data file name undefined\n");
            return 7;
        } elsif ($rc == 3) {
            debug_log(sprintf "put_json_file(): cannot open data file [%s]\n", $filename);
            return 9;
        } else {
            debug_log(sprintf "put_json_file(): error, something else [%s]\n", $filename);
            return $rc;
        }
    } elsif ($result == 1) {
        debug_log("put_json_file(): schema file name undefined\n");
        return 1
    } elsif ($result == 2) {
        debug_log(sprintf "put_json_file(): schema file not found [%s]\n", $schema_filename);
        return 2;
    } elsif ($result == 3) {
        debug_log(sprintf "put_json_file(): cannot open schema file [%s]\n". $schema_filename);
        return 3;
    } elsif ($result == 4) {
        debug_log(sprintf "put_json_file(): schema invalid [%s]\n", $schema_filename);
        return 4;
    } elsif ($result == 4) {
        debug_log(sprintf "put_json_file(): validation failed [%s]\n", $filename);
        return 5;
    } else {
        debug_log(sprintf "put_json_file(): something else [%s]\n", $filename);
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
            debug_log("get_json_file(): data json invalid\n");
            return (6, $json_ref);
        }
        my $result = validate_schema($schema_filename, $filename, $json_ref);
        if ($result == 0) {
            return (0, $json_ref);
        } elsif ($result == 1) {
            debug_log(sprintf "get_json_file(): schema file undefined\n");
            return (1, $json_ref);
        } elsif ($result == 2) {
            debug_log(sprintf "get_json_file(): schema not found [%s]\n", $schema_filename);
            return (2, $json_ref);
        } elsif ($result == 3) {
            debug_log(sprintf "get_json_file(): cannot open schema file [%s]\n", $schema_filename);
            return (3, $json_ref);
        } elsif ($result == 4) {
            debug_log(sprintf "get_json_file(): schema invalid [%s]\n", $schema_filename);
            return (4, $json_ref);
        } elsif ($result == 5) {
            debug_log(sprintf "get_json_file(): validation failed [%s]\n", $filename);
            return (5, $json_ref);
        } else {
            debug_log(sprintf "get_json_file(): error, something else [%s]\n", $filename);
            return ($result, $json_ref);
        }
    } elsif ($rc == 1) {
        debug_log("get_json_file(): data file name undefined\n");
        return (7, $json_ref);
    } elsif ($rc == 2) {
        debug_log(sprintf "get_json_file(): data file not found [%s]\n", $filename);
        return (8, $json_ref);
    } elsif ($rc == 3) {
        debug_log(sprintf "get_json_file(): cannot open data file [%s]\n", $filename);
        return (9, $json_ref);
    } else {
        debug_log(sprintf "get_json_file(): something else [%s]\n", $filename);
        return ($rc, $json_ref);
    }
}

1;
