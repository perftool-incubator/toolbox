# -*- mode: perl; indent-tabs-mode: nil; perl-indent-level: 4 -*-
# vim: autoindent tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=perl

package toolbox::jsonsettings;

use toolbox::json;
use toolbox::logging;

use Exporter qw(import);
our @EXPORT = qw(load_json_settings get_json_setting);

use strict;
use warnings;

sub load_json_settings {
    my $filename = shift;

    my $file_open_rc;
    my $json_ref;

    ($file_open_rc, $json_ref) = get_json_file($filename);

    return ($file_open_rc, $json_ref);
}

sub get_json_setting {
    my $query = shift;
    my $json_ref = shift;

    debug_log(sprintf "get_json_setting(): processing query '%s'\n", $query);
    debug_log(sprintf "get_json_setting(): searching for query in JSON:\n%s", dump_json($json_ref));

    # break the query into fields to attempt to use to traverse the
    # json
    my @query_fields = split(/\./, $query);

    my $query_rc = 0;
    my $query_return = undef;

    # iterate through all supplied query fields
    for (my $i=0; $i<scalar(@query_fields); $i++) {
        debug_log(sprintf "get_json_setting(): processing query_field='%s'\n", $query_fields[$i]);
        # check if the query field exists in the hash
        if (exists($$json_ref{$query_fields[$i]})) {
            # the query field exists, but what is it
            my $var_type = ref($$json_ref{$query_fields[$i]});
            debug_log(sprintf "get_json_setting(): var_type='%s'\n", $var_type);

            if ($var_type eq "JSON::PP::Boolean") {
                # found a JSON::PP:Boolean; a JSON true will be a 0
                # and a JSON false will be a 1; we are going to return
                # strings of 'true' or 'false'
                if ($$json_ref{$query_fields[$i]} == 1) {
                    $query_return = "true";
                } else {
                    $query_return = "false";
                }
                debug_log(sprintf "get_json_setting(): found query_return='%s'\n", $query_return);
            } elsif ($var_type eq "HASH") {
                if ($i == (scalar(@query_fields) - 1)) {
                    # the query field is a hash and there are no more
                    # fields to search for; no value was found, fail
                    $query_rc = 1;
                    debug_log(sprintf "get_json_setting(): no more hash values to search, setting query_rc=%d\n", $query_rc);
                    last;
                } else {
                    # keep searching by narrowing the scope for the
                    # next query field
                    $json_ref = \%{$$json_ref{$query_fields[$i]}};
                    debug_log(sprintf "get_json_setting(): narrowing scope and continuing search\n");
                }
            } elsif ($var_type eq "") {
                # found something other than a hash
                if ($i == (scalar(@query_fields) - 1)) {
                    # this was the last query field, assume the
                    # desired value was found, success
                    $query_return = $$json_ref{$query_fields[$i]};
                    debug_log(sprintf "get_json_setting(): found query_return='%s'\n", $query_return);
                } else {
                    # this is not the last query field and there no
                    # further to search, fail
                    $query_rc = 1;
                    debug_log(sprintf "get_json_setting(): there is no further to search but query fields remain, setting query_rc=%d\n", $query_rc);
                    last;
                }
            }
	} else {
            # the query field does not exist, fail
	    $query_rc = 1;
            debug_log(sprintf "get_json_setting(): the query field does not exist, setting query_rc=%d\n", $query_rc);
	    last;
	}
    }

    debug_log(sprintf "get_json_setting(): returning query_rc=%d and query_return='%s'\n", $query_rc, $query_return);
  
    return ($query_rc, $query_return);
}

1;
