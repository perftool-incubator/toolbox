# -*- mode: perl; indent-tabs-mode: t; perl-indent-level: 4 -*-
# vim: autoindent tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=perl

package toolbox::metrics;

use Exporter qw(import);
our @EXPORT = qw(log_sample finish_samples);

use strict;
use warnings;
use IO::File;
use Data::Dumper;

my $file_id;
my @metric_types;
my %metric_idx;
my @stored_sample;
my @num_written_samples;
my @interval;
my $total_logged_samples;
my $total_cons_samples;
my %inter_sample_interval;
my $use_xz = 1;
my %metric_data_fh;
my $metric_data_file_prefix;
my $metric_data_file;

sub write_sample {
    my $idx = shift;
    my $begin = shift;
    my $end = shift;
    my $value = shift;
    if (defined $file_id) {
        if (defined $metric_data_fh{$file_id}) {
            if (defined $idx) {
                if (defined $begin) {
                    if (defined $end) {
                        if (defined $value) {
                            printf { $metric_data_fh{$file_id} } "%d,%d,%d,%f\n", $idx, $begin, $end, $value;
                        } else {
                            printf "metrics.pm::write_sample(): 'value' is not defined, filed_id = %s, idx = %d, begin = %d, end = %d\n", $file_id, $idx, $begin, $end;
                            print "desc: " . Dumper $metric_types[$idx];
                        }
                    } else {
                        printf "metrics.pm::write_sample(): 'end' is not defined, filed_id = %s, idx = %d, value = %f, begin = %d\n", $file_id, $idx, $value, $begin;
                        print "desc: " . Dumper $metric_types[$idx];
                    }
                } else {
                    printf "metrics.pm::write_sample(): 'begin' is not defined, filed_id = %s, idx = %d, value = %f, end = %d\n", $file_id, $idx, $value, $end;
                    print "desc: " . Dumper $metric_types[$idx];
                }
            } else {
                printf "metrics.pm::write_sample(): 'idx' is not defined, filed_id = %s, value = %f, begin = %d, end = %d\n", $file_id, $value, $begin, $end;
                print "desc: " . Dumper $metric_types[$idx];
            }
        } else {
            printf "metrics.pm::write_sample(): metric_data_fh{file_id} is not defined, idx = %d, value = %f, begin = %d, end = %d\n", $idx, $value, $begin, $end;
            print "desc: " . Dumper $metric_types[$idx];
            exit 1;
        }
    } else {
        printf "metrics.pm::write_sample(): file_id is not defined, idx = %d, value = %f, begin = %d, end = %d\n", $idx, $value, $begin, $end;
        print "desc: " . Dumper $metric_types[$idx];
        exit 1;
    }
    if (defined $num_written_samples[$idx]) {
        $num_written_samples[$idx]++;
    } else {
        $num_written_samples[$idx] = 1;
    }
}

sub get_metric_label {
    my $desc_ref = shift;
    my $names_ref = shift;
    my $label = $$desc_ref{'source'} . ":" . $$desc_ref{'type'} . ":";

    # Build a label to uniquely identify this metric type
    foreach my $name (sort keys %$names_ref) {
        my $value;
        if (exists $$names_ref{$name} and defined $$names_ref{$name})  {
            $value = $$names_ref{$name};
        } else {
            $value = "x";
        }
        $label .= "<" . $name . ":" . $value . ">";
    }
    return $label;
}

sub finish_samples {
    if (defined $file_id) {
        my @new_metric_types;
        my $num_deletes = 0;
        # All of the stored samples need to be written
        for (my $idx = 0; $idx < scalar @stored_sample; $idx++) {
            if (defined $metric_data_fh{$file_id}) {
                if (defined $stored_sample[$idx]) {
                    if ($stored_sample[$idx]{'value'} == 0 and ! defined $num_written_samples[$idx]) {
                        # This metric has only 1 sample and the value is 0, so it "did not do any work".  Therefore, we can just
                        # not create this metric at all.
                        # TODO: This optimization might be better if the metric source/type could opt in/out of this.
                        # There might be certain metrics which users want to query and get a "0" instead of a metric
                        # not existing.  FWIW, this should *not* be a problem for metric-aggregation for throughput class.
                        $metric_types[$idx]{'purge'} = 1;
                        $num_deletes++;
                    } else {
                        write_sample($idx, $stored_sample[$idx]{'begin'}, $stored_sample[$idx]{'end'}, $stored_sample[$idx]{'value'});
                        $metric_types[$idx]{'idx'} = $idx;
                    }
                    undef $stored_sample[$idx];
                }
            }
        }
        for (my $idx = 0; $idx < scalar @metric_types; $idx++) {
            next if (defined $metric_types[$idx]{'purge'} and $metric_types[$idx]{'purge'} == 1);
            my %metric = ( 'idx' => $metric_types[$idx]{'idx'},
                           'desc' => $metric_types[$idx]{'desc'},
                           'names' => $metric_types[$idx]{'names'});
            push(@new_metric_types, \%metric);
            delete $interval[$idx];
            #undef $interval[$idx];
        }
        if (scalar @new_metric_types > 0) {
            my $coder = JSON::XS->new->canonical->pretty;
            my $file = "metric-data-" . $file_id . ".json";
            my $json_fh;
            if ($use_xz == "1") {
                $file .= ".xz";
                $json_fh = new IO::Compress::Xz $file || die("Could not open " . $file . " for writing\n");
            } else {
                open( $json_fh, '>' . $file) or die("Could not open " . $file . ": $!");
            }
            printf "writing metric_types into json for %s\n", $file_id;
            print $json_fh $coder->encode(\@new_metric_types);
            close($json_fh);
            printf "closing csv file for %s\n", $file_id;
            close($metric_data_fh{$file_id});
        } else {
            printf "There are no metric_types for %s\n", $file_id;
        }
        @stored_sample = ();;
        %metric_idx = ();
        undef @metric_types;
        delete($metric_data_fh{$file_id});
        undef $file_id;
        return $metric_data_file_prefix;
    } else {
        printf "file_id is not defined, so not going to finish_samples\n";
    }
}

sub log_sample {
    $file_id = shift;
    my $desc_ref = shift;
    my $names_ref = shift;
    my $sample_ref = shift;
    $metric_data_file_prefix = "metric-data-" . $file_id;
    $metric_data_file = $metric_data_file_prefix . ".csv";
    if ($use_xz == 1) {
        $metric_data_file .= ".xz";
    }

    my $label = get_metric_label($desc_ref, $names_ref);

    if (! defined $metric_idx{$label} and ! exists $metric_idx{$label}) { # This is the first sample for this metric type (of this label)
        # This is how we track which element in the metrics array belongs to this metric type
        $metric_idx{$label} = scalar @metric_types;
        my $idx = $metric_idx{$label};
        # store the metric_desc info
        my %desc = %$desc_ref;
        my %names = %$names_ref;
        my %sample = %$sample_ref;
        my %metric_type = ( 'desc' => \%desc, 'names' => \%names);
        $metric_types[$idx] = \%metric_type;
        # Sample data will not be accumulated in a hash or array, as the memory usage
        # of this script can explode.  Instead, samples are written to a file (but we
        # also merge cronologically adjacent samples with the same valule).
        # Check for and open this file now.
        if (! defined $metric_data_fh{$file_id}) {
            if ($use_xz == "1") {
                $metric_data_fh{$file_id} = new IO::Compress::Xz $metric_data_file || die("Could not open " . $metric_data_file . " for writing\n");
            } else {
                open( $metric_data_fh{$file_id}, '>' . $metric_data_file) or die("Could not open " . $metric_data_file . ": $!");
            }
        }
        if (defined $sample{'begin'}) {
            $stored_sample[$idx]{'begin'} = $sample{'begin'};
        }
        $stored_sample[$idx]{'end'} = $sample{'end'};
        $stored_sample[$idx]{'value'} = $sample{'value'};
        return;
    } else {  # This is not the first sample for this metric_type (of this label)
        my $idx = $metric_idx{$label};
        # Figure out what the typical duration is between samples from the first two
        # (This should only be triggered on the second sample)
        if (! defined $interval[$idx] and defined $stored_sample[$idx]{'end'}) {
            $interval[$idx] = $$sample_ref{'end'} - $stored_sample[$idx]{'end'};
        }
        # If this is the very first sample (that is written), we can't get a begin
        # from a previous sample's end+1, so we derive the begin by subtracting the
        # interval from current sample's end.
        if (defined $stored_sample[$idx] and ! defined $stored_sample[$idx]{'begin'}) {
            if (defined $interval[$idx]) {
                $stored_sample[$idx]{'begin'} = $stored_sample[$idx]{'end'} - $interval[$idx];
            } else {
                printf "ERROR: interval[%d] should have been defined, but it is not\n", $idx;
                printf "file_id: [%s]\n", $file_id;
                print "sample:\n" . Dumper $sample_ref;
                print "desc:\n" . Dumper $desc_ref;
                print "names:\n" . Dumper $names_ref;
                exit 1;
            }
        }
        # Once we have a sample with a different value, we can write the previous [possibly consolidated] sample
        if ($stored_sample[$idx]{'value'} != $$sample_ref{'value'}) {
            write_sample($idx, $stored_sample[$idx]{'begin'}, $stored_sample[$idx]{'end'}, $stored_sample[$idx]{'value'});
            $total_cons_samples++;
            # Now the new sample becomes the stored sample
            if (defined($$sample_ref{'begin'})) {
                $stored_sample[$idx]{'begin'} = $$sample_ref{'begin'};
            } else {
                # If a begin is not provided (common), use the previous sample's end + 1ms.
                $stored_sample[$idx]{'begin'} = $stored_sample[$idx]{'end'} + 1;
            }
            $stored_sample[$idx]{'end'} = $$sample_ref{'end'};
            $stored_sample[$idx]{'value'} = $$sample_ref{'value'};
        } else {
            # The new sample did not have a different value, so we update the stored sample to have a new end time
            # The effect is reducing the total number of samples (sample "dedup" or consolidation)
            $stored_sample[$idx]{'end'} = $$sample_ref{'end'};
        }
        $total_logged_samples++;
        if ($total_logged_samples % 1000000 == 0) {
        }
    }
}

1;
