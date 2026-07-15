# -*- mode: python; indent-tabs-mode: nil; python-indent-level: 4 -*-
# vim: autoindent tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=python

import json
import lzma
import os


POSTPROCESS_DIR = "postprocess"


class CDMMetrics:
    """Thread-safe metric tracker for CDM post-processing.

    Each instance maintains its own state, so multiple threads or
    processes can each have their own CDMMetrics without conflicts.
    """

    def __init__(self, output_dir=POSTPROCESS_DIR):
        self.output_dir = output_dir
        self.metric_types = []
        self.file_id = None
        self.metric_data_fh = {}
        self.metric_idx = {}
        self.stored_sample = {}
        self.num_written_samples = {}
        self.interval = {}
        self.total_logged_samples = 0
        self.total_cons_samples = 0
        self.metric_data_file_prefix = ""
        os.makedirs(self.output_dir, exist_ok=True)

    def _get_metric_label(self, desc, names):
        label = desc["source"] + ":" + desc["type"] + ":"
        for name in sorted(names.keys()):
            value = str(names[name]) if names[name] else "x"
            label += "<" + name + ":" + value + ">"
        return label

    def _write_sample(self, idx, begin, end, value):
        if self.file_id is None:
            raise RuntimeError("Cannot write sample because file_id is undefined")
        if self.file_id not in self.metric_data_fh:
            raise RuntimeError("Cannot write sample with undefined file handle: " + self.file_id)
        self.metric_data_fh[self.file_id].write(
            str(idx) + "," + str(begin) + "," + str(end) + "," + str(value) + "\n"
        )
        if idx not in self.num_written_samples:
            self.num_written_samples[idx] = 1
        else:
            self.num_written_samples[idx] += 1

    def log_sample_by_idx(self, idx, value, end, begin=None):
        """Fast path: update a known metric idx without label lookup.

        Skips _get_metric_label and metric_idx lookup. The caller must have
        obtained idx from a prior log_sample() call and must not change
        file_id between log_sample() and calls here. begin is optional;
        pass it only when the sample has an explicit start time.
        Returns nothing.
        """
        stored = self.stored_sample[idx]
        if idx not in self.interval and stored["end"]:
            self.interval[idx] = end - stored["end"]
        if "begin" not in stored:
            if idx in self.interval:
                stored["begin"] = stored["end"] - self.interval[idx] + 1
            else:
                raise RuntimeError(
                    f"interval [{idx}] should have been defined, but it is not"
                )
        if stored["value"] != value:
            self._write_sample(idx, stored["begin"], stored["end"], stored["value"])
            self.total_cons_samples += 1
            stored["begin"] = begin if begin is not None else stored["end"] + 1
            stored["end"] = end
            stored["value"] = value
        else:
            stored["end"] = end
        self.total_logged_samples += 1

    def log_sample(self, file_id, desc, names, sample):
        """Register or update a metric sample. Returns the metric idx.

        On first call for a (desc, names) combination the metric is
        registered. On subsequent calls the stored sample is updated.
        Callers that call log_sample() in a tight loop with the same
        (desc, names) can cache the returned idx and call
        log_sample_by_idx() directly to avoid repeated label computation.
        """
        self.file_id = file_id
        self.metric_data_file_prefix = "metric-data-" + file_id
        metric_data_file = os.path.join(self.output_dir, self.metric_data_file_prefix + ".csv.xz")
        label = self._get_metric_label(desc, names)

        if label in self.metric_idx:
            idx = self.metric_idx[label]
            self.log_sample_by_idx(idx, sample["value"], sample["end"], sample.get("begin"))
            return idx
        else:
            self.metric_idx[label] = len(self.metric_types)
            idx = self.metric_idx[label]
            self.metric_types.append({"desc": desc.copy(), "names": names.copy()})
            if file_id not in self.metric_data_fh:
                self.metric_data_fh[file_id] = lzma.open(metric_data_file, "wt")
            self.stored_sample[idx] = sample.copy()
            return idx

    def finish_samples(self, dont_delete=False):
        if self.file_id is None:
            return None

        num_deletes = 0
        for idx in range(len(self.stored_sample)):
            if self.file_id in self.metric_data_fh:
                if (
                    self.stored_sample[idx]["value"] == 0
                    and idx not in self.num_written_samples
                    and not dont_delete
                ):
                    self.metric_types[idx]["purge"] = 1
                    num_deletes += 1
                else:
                    begin = self.stored_sample[idx].get("begin", self.stored_sample[idx]["end"])
                    self._write_sample(
                        idx,
                        begin,
                        self.stored_sample[idx]["end"],
                        self.stored_sample[idx]["value"],
                    )
                    self.metric_types[idx]["idx"] = idx

        self.stored_sample = {}
        self.interval = {}
        self.metric_idx = {}

        if self.file_id in self.metric_data_fh:
            self.metric_data_fh[self.file_id].close()
            del self.metric_data_fh[self.file_id]

        new_metric_types = []
        for idx in range(len(self.metric_types)):
            if self.metric_types[idx].get("purge") == 1:
                continue
            new_metric_types.append({
                "idx": self.metric_types[idx]["idx"],
                "desc": self.metric_types[idx]["desc"],
                "names": self.metric_types[idx]["names"],
            })

        if new_metric_types:
            json_file = os.path.join(self.output_dir, "metric-data-" + self.file_id + ".json.xz")
            with lzma.open(json_file, "wt") as fh:
                json.dump(new_metric_types, fh)

        prefix = self.metric_data_file_prefix
        self.metric_types = []
        self.file_id = None
        self.num_written_samples = {}
        return prefix
