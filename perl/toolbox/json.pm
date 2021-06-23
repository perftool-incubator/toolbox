# -*- mode: perl; indent-tabs-mode: t; perl-indent-level: 4 -*-
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
        printf "open_write_text_file(): filename was not defined\n";
        exit 1;
    }
    if (! $filename =~ /\.xz/) { # Always default to compression when writing
        $filename .= ".xz";
    }
    debug_log(sprintf "trying to open [%s] for writing\n", $filename);
    my $fh = new IO::Compress::Xz $filename || die "Could not open file " . $filename;
    return $fh;
}

sub open_read_text_file {
    my $filename = shift;
    chomp $filename;
    if (! defined $filename) {
        printf "open_read_text_file(): filename was not defined\n";
        exit 1;
    }
    if (-e $filename . ".xz") {
        if (-e $filename) {
            printf "open_read_text_file(): both [%s] and [%s] exist, reading [%s]\n", $filename, $filename . ".xz", $filename . ".xz";
        }
        $filename .= ".xz";
    } elsif (! -e $filename ) {
        printf "open_read_text_file(): file [%s] was not found\n", $filename;
        exit 1;
    }
    debug_log(sprintf "trying to open [%s]\n", $filename);
    my $fh = new IO::Uncompress::UnXz $filename, Transparent => 1 || die "Could not open file " . $filename;
    if (! defined $fh) { # Added as IO::Uncompress::UnXz does not always error out when it should
        printf "open_read_text_file() cannot read file: [%s]\n", $filename;
        exit 1;
    }
    return $fh;
}

sub validate_schema {
    my $schema_filename = shift;
    my $filename = shift;
    my $json_ref = shift;
    if (defined $schema_filename) {
        chomp $schema_filename;
        my $jv = JSON::Validator->new;
        my $schema_fh = open_read_text_file($schema_filename);
        my $json_schema_text;
        while ( <$schema_fh> ) {
            $json_schema_text .= $_;
        }
        close($schema_fh);
        chomp $json_schema_text;
        $jv->schema($json_schema_text);
        debug_log(sprintf "Going to validate schema with [%s]\n", $schema_filename);
        my @errors = $jv->validate($json_ref);
        if (scalar @errors >  0) {
            printf "Validation errors for file %s with schema %s:\n", $filename, $schema_filename;
            print Dumper \@errors;
            exit 1;
        }
    }
}

sub put_json_file {
    my $filename = shift;
    chomp $filename;
    my $json_ref = shift;
    my $schema_filename = shift;
    my $coder = JSON::XS->new->canonical->pretty;
    validate_schema($schema_filename, $filename, $json_ref);
    my $json_text = $coder->encode($json_ref);
    my $json_fh = open_write_text_file($filename);
    printf $json_fh "%s", $json_text;
    close($json_fh);
}

sub get_json_file {
    my $filename = shift;
    chomp $filename;
    my $schema_filename = shift;
    my $coder = JSON::XS->new;
    my $json_fh = open_read_text_file($filename);
    my $json_text = "";
    while ( <$json_fh> ) {
        $json_text .= $_;
    }
    close($json_fh);
    chomp $json_text;
    my $json_ref = $coder->decode($json_text) || die "Could not read JSON";
    validate_schema($schema_filename, $filename, $json_ref);
    return $json_ref;
}

1;
