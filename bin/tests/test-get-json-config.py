#!/usr/bin/env python3

import pytest
import json
import getjsonconfig
import re

class TestGetJsonConfig:

    # helper function to read stream from file
    def _load_file(self, filename):
        with open("tests/JSON/" + filename, "r") as file:
            data = file.read().rstrip("\n")
        return data

    # fixture to load json object from file
    @pytest.fixture(scope="function")
    def load_json_file(self, request):
        return getjsonconfig.load_json_file("tests/JSON/" + request.param)

    """Test if json_to_stream converts endpoint block to a stream"""
    @pytest.mark.parametrize("load_json_file",
                             [ "input-oslat-k8s.json" ], indirect=True)
    def test_json_to_stream_endpoints(self, load_json_file):
        endpoints_stream = getjsonconfig.json_to_stream(load_json_file, "endpoint", 0)
        expected_stream = self._load_file("output-oslat-k8s-endpoints.stream")

        # endpoint config generates random stream, so we match only general args
        assert expected_stream in endpoints_stream
        assert 'securityContext:client-1:' in endpoints_stream
        assert 'resources:client-2:' in endpoints_stream
        assert 'annotations:server-1:' in endpoints_stream

    """Test if json_to_stream converts tags block to a stream"""
    @pytest.mark.parametrize("load_json_file",
                             [ "input-oslat-k8s.json" ], indirect=True)
    def test_json_to_stream_tags(self, load_json_file):
        tags_stream = getjsonconfig.json_to_stream(load_json_file, "tags", 0)
        expected_stream = self._load_file("output-oslat-tags.stream")

        assert tags_stream == expected_stream

    """Test if json_to_stream converts passthru-args block to a stream"""
    @pytest.mark.parametrize("load_json_file",
                             [ "input-oslat-k8s.json" ], indirect=True)
    def test_json_to_stream_passthru(self, load_json_file):
        passthru_stream = getjsonconfig.dump_json(load_json_file, "passthru-args")
        expected_stream = self._load_file("output-oslat-passthru-args.stream")

        assert passthru_stream == expected_stream

    """Test if load_json_file returns a dict dump_json returns a str"""
    @pytest.mark.parametrize("load_json_file",
                             [ "input-oslat-k8s.json" ], indirect=True)
    def test_dump_json_mvparams(self, load_json_file):
        assert type(load_json_file) == dict
        input_json = getjsonconfig.dump_json(load_json_file, "mv-params")
        assert type(input_json) == str

    """Test if json_to_stream returns None for invalid index"""
    @pytest.mark.parametrize("load_json_file",
                             [ "input-oslat-k8s.json" ], indirect=True)
    def test_json_to_stream_endpoints_invalid_idx(self, load_json_file, capsys):
        input_json = getjsonconfig.json_to_stream(load_json_file, "endpoint", 1)
        out, err = capsys.readouterr()
        assert 'Invalid index' in out
        assert input_json is None

    """Test validate_schema using default schema for null schema_file arg"""
    @pytest.mark.parametrize("load_json_file",
                             [ "input-oslat-k8s.json" ], indirect=True)
    def test_validate_schema_default(self, load_json_file):
        validated_json = getjsonconfig.validate_schema(load_json_file)
        assert validated_json is True

    """Test validate_schema using endpoint schema and returns True"""
    @pytest.mark.parametrize("load_json_file",
                             [ "input-oslat-k8s.json" ], indirect=True)
    def test_validate_schema_endpoint(self, load_json_file):
        validated_json = getjsonconfig.validate_schema(
                             load_json_file["endpoint"], "schema-endpoint.json")
        assert validated_json is True
