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
our @EXPORT = qw(put_json_file get_json_file);

use strict;
use warnings;

sub put_json_file {
    my $filename = shift;
    chomp $filename;
    my $json_ref = shift;
    my $schema_filename = shift;
    my $coder = JSON::XS->new->canonical->pretty;
    if (defined $schema_filename and -e $schema_filename) {
        chomp $schema_filename;
        my $jv = JSON::Validator->new;
        my $schema_fh = new IO::Uncompress::UnXz $schema_filename, Transparent => 1 || die "Could not open file " . $schema_filename;
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
    debug_log(sprintf "trying to write [%s]\n", $filename);
    my $json_text = $coder->encode($json_ref);
    my $json_fh;
    if ($filename =~ /xz$/) {
        $json_fh = new IO::Compress::Xz "$filename" || die("Could not open $filename.xz for writing\n");
    } else {
        open($json_fh, ">", $filename);
    }
    printf $json_fh "%s", $json_text;
    close($json_fh);
}

sub get_json_file {
    my $filename = shift;
    chomp $filename;
    my $schema_filename = shift;
    my $coder = JSON::XS->new;
    debug_log(sprintf "trying to open [%s]\n", $filename);
    my $log_fh = new IO::Uncompress::UnXz $filename, Transparent => 1 || die "Could not open file " . $filename;
    my $json_text = "";
    while ( <$log_fh> ) {
        $json_text .= $_;
    }
    close($log_fh);
    chomp $json_text;
    my $json_ref = $coder->decode($json_text) || die "Could not read JSON";
    if (defined $schema_filename and -e $schema_filename) {
        chomp $schema_filename;
        my $jv = JSON::Validator->new;
        my $schema_fh = new IO::Uncompress::UnXz $schema_filename, Transparent => 1 || die "Could not open file " . $schema_filename;
        my $json_schema_text;
        while ( <$schema_fh> ) {
            $json_schema_text .= $_;
        }
        close($schema_fh);
        chomp $json_schema_text;
        $jv->schema($json_schema_text);
        my @errors = $jv->validate($json_ref);
        if (scalar @errors >  0) {
            printf "Validaton errors for file %s with schema %s:\n", $filename, $schema_filename;
            print Dumper \@errors;
            exit 1;
        }
    }
    return $json_ref;
}

1;
