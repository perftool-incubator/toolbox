# -*- mode: perl; indent-tabs-mode: nil; perl-indent-level: 4 -*-
# vim: autoindent tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=perl

package toolbox::cpu;

use toolbox::logging;

use Exporter qw(import);
our @EXPORT = qw(build_cpu_topology get_cpu_topology);

use strict;
use warnings;

sub build_cpu_topology {
    my $cpu_topo_path = shift;
    my @cpu_topo;
    if (-d $cpu_topo_path) {
        opendir(my $dh, $cpu_topo_path);
        for my $cpu_dir (grep(/^cpu\d+/, sort readdir($dh))) {
            my $cpu_id = $cpu_dir;
            $cpu_id =~ s/^cpu//;
            chomp $cpu_id;
            my $this_cpu_online_path = $cpu_topo_path . "/" . $cpu_dir . "/online";
            if (-e $this_cpu_online_path) {
                open(FH, $this_cpu_online_path);
                my $online_state = <FH>;
                close(FH);
                chomp($online_state);
                if ($online_state ne 1) {
                    # skip cpus that are offline --they don't have topology information
                    next;
                }
            }
            my $this_cpu_topo_path = $cpu_topo_path . "/" . $cpu_dir . "/topology";
            if (-d $this_cpu_topo_path) {
                my %topo;
                my $file;
                for my $this_cpu_type ('physical_package_id', 'die_id', 'core_id') {
                    my $id;
                    $file = $this_cpu_topo_path . "/" . $this_cpu_type;
                    if (-e $file) {
                        open(FH, $file) or die "Could not open $file";
                        $id = <FH>;
                        close FH;
                        chomp $id;
                    } else {
                        # If the topo info is not available, assume id = 0
                        $id = 0;
                    }
                    if ($id =~ /^\d+$/) {
                        if ($this_cpu_type eq "physical_package_id") {
                            # Keep the naming consistent, $single_word_heirarchy_level . "_id"
                            $topo{'package_id'} = $id;
                        } else {
                            $topo{$this_cpu_type} = $id;
                        }
                    } else {
                        die "CPU ID for %s is not a valid number\n". $file;
                    }
                }
                # Getting a cpu-thread ID is not as straight forward as it is for package, die,
                # and core.  Sysfs does not provide an actual thread id.  We must what position
                # in the list of thread_siblings our [logical] cpu id is and use that position
                # as the thread id.
                $file = $cpu_topo_path . "/" . $cpu_dir . "/topology/thread_siblings_list";
                if (-e $file) {
                    open(FH, $file);
                    my $list = <FH>;
                    chomp $list;
                    close FH;
                    my $thread_id = 0;
                    # We need an ordered list with no x-y ranges in it
                    for my $range (split(/,/, $list)) {
                        if ($range =~ /(\d+)-(\d+)/) {
                            my $i;
                            for ($i = $1; $i <= $2; $i++) {
                                if ($i == $cpu_id) {
                                    $topo{'thread_id'} = $thread_id;
                                    last;
                                }
                                $thread_id++;
                            }
                        } else {
                            if ($range == $cpu_id) {
                                $topo{'thread_id'} = $thread_id;
                                last;
                            }
                            $thread_id++;
                        }
                    }
                } else {
                    log_print sprintf "WARNING: could not find %s\n", $file;
                }
                $cpu_topo[$cpu_id] = \%topo;
            } else {
                log_print sprintf "WARNING: could not find %s\n", $this_cpu_topo_path;
            }
        }
    } else {
        log_print sprintf "WARNING: could not find %s\n", $cpu_topo_path;
    }
    return \@cpu_topo;
}

sub get_cpu_topology {
    my $cpu_num = shift;
    my $cpus_ref = shift;
    if (exists $$cpus_ref[$cpu_num]) {
        return ($$cpus_ref[$cpu_num]{'package_id'}, $$cpus_ref[$cpu_num]{'die_id'}, $$cpus_ref[$cpu_num]{'core_id'}, $$cpus_ref[$cpu_num]{'thread_id'});
    } else {
        return (0, 0, $cpu_num, 0);
    }
}
