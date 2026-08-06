#!/usr/bin/python3
# -*- mode: python; indent-tabs-mode: nil; python-indent-level: 4 -*-
# vim: autoindent tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=python

"""Unit tests for metric descriptor validation.

Run directly with: python3 -m unittest toolbox.test_validate_metric_desc
(requires TOOLBOX_HOME/python on sys.path, same as the other toolbox modules)
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

TOOLBOX_HOME = os.environ.get("TOOLBOX_HOME")
if TOOLBOX_HOME:
    sys.path.append(str(Path(TOOLBOX_HOME) / "python"))

from toolbox.cdm_metrics import CDMMetrics, validate_metric_desc
from toolbox import metrics as legacy_metrics


class TestValidateMetricDesc(unittest.TestCase):
    def test_valid_class_and_aggregation(self):
        validate_metric_desc({"source": "fio", "type": "iops", "class": "throughput", "default-aggregation": "sum"})

    def test_valid_class_without_aggregation(self):
        validate_metric_desc({"source": "fio", "type": "iops", "class": "throughput"})

    def test_invalid_class_raises(self):
        with self.assertRaises(ValueError):
            validate_metric_desc({"source": "fio", "type": "iops", "class": "bananas"})

    def test_missing_class_raises(self):
        with self.assertRaises(ValueError):
            validate_metric_desc({"source": "fio", "type": "iops"})

    def test_invalid_aggregation_raises(self):
        with self.assertRaises(ValueError):
            validate_metric_desc({"source": "fio", "type": "iops", "class": "throughput", "default-aggregation": "median"})

    def test_all_current_classes_accepted(self):
        for cdm_class in ("throughput", "latency", "count", "pass/fail", "boolean", "percentage"):
            validate_metric_desc({"source": "x", "type": "y", "class": cdm_class})

    def test_all_current_aggregations_accepted(self):
        for aggregation in ("sum", "avg", "max", "min"):
            validate_metric_desc(
                {"source": "x", "type": "y", "class": "count", "default-aggregation": aggregation}
            )


class TestCDMMetricsLogSample(unittest.TestCase):
    def test_invalid_class_raises_on_first_sample(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            metrics = CDMMetrics(output_dir=tmpdir)
            desc = {"source": "fio", "type": "iops", "class": "bananas"}
            with self.assertRaises(ValueError):
                metrics.log_sample("0", desc, {}, {"end": 1000, "value": 1})

    def test_valid_class_does_not_raise(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            metrics = CDMMetrics(output_dir=tmpdir)
            desc = {"source": "fio", "type": "iops", "class": "throughput", "default-aggregation": "sum"}
            metrics.log_sample("0", desc, {}, {"end": 1000, "value": 1})
            metrics.finish_samples()


class TestLegacyMetricsLogSample(unittest.TestCase):
    def test_invalid_class_raises_on_first_sample(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            legacy_metrics.output_dir = tmpdir
            legacy_metrics.metric_idx = {}
            legacy_metrics.metric_types = []
            legacy_metrics.stored_sample = {}
            desc = {"source": "ovs", "type": "packets-sec", "class": "bananas"}
            with self.assertRaises(ValueError):
                legacy_metrics.log_sample("0", desc, {}, {"end": 1000, "value": 1})


if __name__ == "__main__":
    unittest.main()
