# -*- mode: perl; indent-tabs-mode: t; perl-indent-level: 4 -*-
# vim: autoindent tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=perl

package toolbox::metrics;

use Exporter qw(import);
our @EXPORT = qw(log_sample finish_samples);

use strict;
use warnings;
use IO::File;
use Data::Dumper;

our $file_id;
our @metrics;
our %metric_idx;
our @stored_sample;
our @num_written_samples;
our @interval;
our $total_logged_samples;
our $total_cons_samples;
our %inter_sample_interval;
our $use_xz = 1;
our $metric_data_fh;
our $metric_data_file_prefix;
our $metric_data_file;

sub write_sample {
    my $idx = shift;
    my $begin = shift;
    my $end = shift;
    my $value = shift;
    if (defined $metric_data_fh) {
        printf { $metric_data_fh } "%d,%d,%d,%f\n", $idx, $begin, $end, $value;
    } else {
        print "Cannot write sample with undefined file handle\n";
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
    my @new_metrics;
    my $num_deletes = 0;
    # All of the stored samples need to be written
    for (my $idx = 0; $idx < scalar @stored_sample; $idx++) {
        if (defined $metric_data_fh) {
            if (defined $stored_sample[$idx]) {
                if ($stored_sample[$idx]{'value'} == 0 and ! defined $num_written_samples[$idx]) {
                    # This metric has only 1 sample and the value is 0, so it "did not do any work".  Therefore, we can just
                    # not create this metric at all.
                    # TODO: This optimization might be better if the metric source/type could opt in/out of this.
                    # There might be certain metrics which users want to query and get a "0" instead of a metric
                    # not existing.  FWIW, this should *not* be a problem for metric-aggregation for throughput class.
                    $metrics[$idx]{'purge'} = 1;
                    $num_deletes++;
                } else {
                    write_sample($idx, $stored_sample[$idx]{'begin'}, $stored_sample[$idx]{'end'}, $stored_sample[$idx]{'value'});
                    $metrics[$idx]{'idx'} = $idx;
                }
            } else {
                printf "ERROR: No stored sample defined at index %d\n", $idx;
                exit 1;
            }
        }
    }
    if (defined $metric_data_fh) {
        close($metric_data_fh);
    } else {
        printf "finish_samples(): cannot close file with undefined file handle\n";
        exit 1;
    }
    for (my $idx = 0; $idx < scalar @metrics; $idx++) {
        next if (defined $metrics[$idx]{'purge'} and $metrics[$idx]{'purge'} == 1);
        my %metric;
        $metric{'idx'} = $metrics[$idx]{'idx'};
        $metric{'desc'} = $metrics[$idx]{'desc'};
        $metric{'names'} = $metrics[$idx]{'names'};
        push(@new_metrics, \%metric);
    }
    if (scalar @new_metrics > 0) {
        my $coder = JSON::XS->new;
        my $file = "metric-data-" . $file_id . ".json.xz";
        my $json_fh = new IO::Compress::Xz $file || die("Could not open " . $file . " for writing\n");
        print $json_fh $coder->encode(\@new_metrics);
        close($json_fh);
    }
    return $metric_data_file_prefix;
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

    if (! exists $metric_idx{$label}) { # This is the first sample for this metric type (of this label)
        # This is how we track which element in the metrics array belongs to this metric type
        $metric_idx{$label} = scalar @metrics;
        my $idx = $metric_idx{$label};
        # store the metric_desc info
        my %this_metric;
        $this_metric{'desc'} = $desc_ref;
        $this_metric{'names'} = $names_ref;
        $metrics[$idx] = \%this_metric;
        # Sample data will not be accumulated in a hash or array, as the memory usage
        # of this script can explode.  Instead, samples are written to a file (but we
        # also merge cronologically adjacent samples with the same valule).
        # Check for and open this file now.
        if (! defined $metric_data_fh) {
            if ($use_xz == "1") {
                $metric_data_fh = new IO::Compress::Xz $metric_data_file || die("Could not open " . $metric_data_file . " for writing\n");
            } else {
                open( $metric_data_fh, '>' . $metric_data_file) or die("Could not open " . $metric_data_file . ": $!");
            }
        }
        if (defined $$sample_ref{'begin'}) {
            $stored_sample[$idx]{'begin'} = $$sample_ref{'begin'};
        }
        $stored_sample[$idx]{'end'} = $$sample_ref{'end'};
        $stored_sample[$idx]{'value'} = $$sample_ref{'value'};
        return;
    } else {  # This is mot the first sample for this metric_type (of this label)
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
            $stored_sample[$idx]{'begin'} = $stored_sample[$idx]{'end'} - $interval[$idx];
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
            printf "Logged %d samples, wrote %d consolidated samples\n", $total_logged_samples, $total_cons_samples;
        }
    }
}

1;
