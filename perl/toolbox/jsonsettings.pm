# -*- mode: perl; indent-tabs-mode: nil; perl-indent-level: 4 -*-
# vim: autoindent tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=perl

package toolbox::jsonsettings;

use toolbox::json;

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

    # break the query into fields to attempt to use to traverse the
    # json
    my @query_fields = split(/\./, $query);

    my $query_rc = 0;
    my $query_return = undef;

    # iterate through all supplied query fields
    for (my $i=0; $i<scalar(@query_fields); $i++) {
        # check if the query field exists in the hash
        if (exists($$json_ref{$query_fields[$i]})) {
            # the query field exists, but what is it
            my $var_type = ref($$json_ref{$query_fields[$i]});
                
            if ($var_type eq "HASH") {
                if ($i == (scalar(@query_fields) - 1)) {
                    # the query field is a hash and there are no more
                    # fields to search for; no value was found, fail
                    $query_rc = 1;
                    last;
                } else {
                    # keep searching by narrowing the scope for the
                    # next query field
                    $json_ref = \%{$$json_ref{$query_fields[$i]}};
                }
            } elsif ($var_type eq "") {
                # found something other than a hash
                if ($i == (scalar(@query_fields) - 1)) {
                    # this was the last query field, assume the
                    # desired value was found, success
                    $query_return = $$json_ref{$query_fields[$i]};
                } else {
                    # this is not the last query field and there no
                    # further to search, fail
                    $query_rc = 1;
                    last;
                }
            }
	} else {
            # the query field does not exist, fail
	    $query_rc = 1;
	    last;
	}
    }
  
    return ($query_rc, $query_return);
}

1;
