import copy
import json
from pathlib import Path

global metric_types
metric_types = []
global file_id
file_id = None
global metric_data_fh
metric_data_fh = {}
global metric_idx
metric_idx = {}
global stored_sample
stored_sample = {}
global num_written_samples
num_written_samples = {}
global interval
interval = {}
global total_logged_samples
total_logged_samples = 0
global total_cons_samples
total_cons_samples = 0
global metric_data_file_prefix
metric_data_file_prefix = ''
global metric_data_file
metric_data_file = ''


def write_sample(idx: str, begin: int, end: int, value: float):
    if file_id is not None:
        try:
            metric_data_fh[file_id]
        except NameError:
            print("Cannot write sample with undefined file handle: " + file_id)
            exit(1)
        else:
            metric_data_fh[file_id].write(str(idx) + "," + str(begin) + "," + str(end) + "," + str(value) + "\n")
    else:
            print("Cannot write sample because file_id is undefined")
            exit(1);
    try:
        num_written_samples[idx]
    except:
        num_written_samples[idx] = 1
    else:
        num_written_samples[idx] += 1

def get_metric_label(desc: object, names: object):
    label = desc['source'] +  ":" + desc['type'] + ":"
    # Build a label to uniquely identify this metric type
    for name in names.keys():
        if names[name]:
            value = names[name]
        else:
            value = "x"
        label = label + "<" + name + ":" + value + ">"
    return label

def log_sample(this_file_id: str, desc: dict, names: dict, sample: dict):
    global file_id, total_logged_samples, total_cons_samples, stored_sample
    file_id = this_file_id
    metric_data_file_prefix = "metric-data-" + file_id
    metric_data_file = metric_data_file_prefix + ".csv"
    label = get_metric_label(desc, names)
    if label in metric_idx:
        # This is not the first sample for this metric_type (of this label)
        idx = metric_idx[label]
        # Figure out what the typical duration is between samples from the first two
        # (This should only be triggered on the second sample)
        if idx not in interval.keys() and stored_sample[idx]['end']:
            interval[idx] = sample['end'] - stored_sample[idx]['end']
        # If this is the very first sample (that is written), we can't get a begin
        # from a previous sample's end+1, so we derive the begin by subtracting the
        # interval from current sample's end.
        if idx in stored_sample.keys() and 'begin' not in stored_sample[idx].keys():
            if idx in interval.keys():
                stored_sample[idx]['begin'] = stored_sample[idx]['end'] - interval[idx] + 1
            else:
                print("ERROR: interval [" + idx + "] should have been defined, but it is not")
                print("file_id: [" + file_id + "]")
                print("sample:" + sample)
                print("desc:" +  desc)
                print("names:\n" + names)
                exit(1);
        # Once we have a sample with a different value, we can write the previous [possibly consolidated] sample
        if stored_sample[idx]['value'] != sample['value']:
            write_sample(idx, stored_sample[idx]['begin'], stored_sample[idx]['end'], stored_sample[idx]['value'])
            total_cons_samples += 1
            # Now the new sample becomes the stored sample
            if 'begin' in sample.keys():
                stored_sample[idx]['begin'] = sample['begin']
            else:
                # If a begin is not provided (common), use the previous sample's end + 1ms.
                stored_sample[idx]['begin'] = stored_sample[idx]['end'] + 1
            stored_sample[idx]['end'] = sample['end']
            stored_sample[idx]['value'] = sample['value']
        else:
            # The new sample did not have a different value, so we update the stored sample to have a new end time
            # The effect is reducing the total number of samples (sample "dedup" or consolidation)
            stored_sample[idx]['end'] = sample['end']
        total_logged_samples += 1
        return
    else:
        # This is the first sample for this metric type (of this label)
        # This is how we track which element in the metrics array belongs to this metric type
        metric_idx[label] = len(metric_types)
        idx = metric_idx[label]
        metric_type = { 'desc': {}, 'names': {} }
        for key in desc.keys():
            metric_type['desc'][key] = desc[key]
        for key in names.keys():
            metric_type['names'][key] = names[key]
        metric_types.append(metric_type)
        # Sample data will not be accumulated in a hash or array, as the memory usage
        # of this script can explode.  Instead, samples are written to a file (but we
        # also merge cronologically adjacent samples with the same valule).
        # Check for and open this file now.
        if file_id not in metric_data_fh:
            metric_data_fh[file_id] = open(metric_data_file, "w")
        stored_sample[idx] = sample

def finish_samples():
    global file_id, stored_sample, interval, metric_idx, metric_types
    if file_id is not None:
        new_metric_types = []
        num_deletes = 0
        # All of the stored samples need to be written
        for idx in range(0, len(stored_sample)):
            if file_id in metric_data_fh.keys():
                if stored_sample[idx]['value'] == 0 and idx not in num_written_samples.keys():
                    # This metric has only 1 sample and the value is 0, so it "did not do any work".  Therefore, we can just
                    # not create this metric at all.
                    # TODO: This optimization might be better if the metric source/type could opt in/out of this.
                    # There might be certain metrics which users want to query and get a "0" instead of a metric
                    # not existing.  FWIW, this should *not* be a problem for metric-aggregation for throughput class.
                    metric_types[idx]['purge'] = 1
                    num_deletes += 1
                else:
                    write_sample(idx, stored_sample[idx]['begin'], stored_sample[idx]['end'], stored_sample[idx]['value'])
                    metric_types[idx]['idx'] = idx
        stored_sample = {}
        interval = {}
        metric_idx = {}
        if file_id in metric_data_fh.keys():
            metric_data_fh[file_id].close()
            del metric_data_fh[file_id]
        else:
            print("Cannot finish samples because file_id is undefined")
            exit(1)
        for idx in range(0, len(metric_types)):
            if 'purge' in metric_types[idx].keys() and metric_types[idx]['purge'] == 1:
                continue
            metric = { 'idx': metric_types[idx]['idx'],
                       'desc': metric_types[idx]['desc'],
                       'names': metric_types[idx]['names'] }
            new_metric_types.append(metric)
        if len(new_metric_types) > 0:
            file = "metric-data-" + file_id + ".json"
            with open(file, 'w') as json_file:
                json.dump(new_metric_types, json_file)
            json_file.close()
        metric_types = []
        file_id = None
        return metric_data_file_prefix
