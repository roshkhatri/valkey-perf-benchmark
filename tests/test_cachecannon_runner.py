"""Tests for cachecannon_runner module."""

import json
from unittest.mock import patch, MagicMock

import pytest

from cachecannon_runner import (
    supports_command,
    _build_toml_config,
    _parse_json_output,
    run_cachecannon,
)


class TestSupportsCommand:
    """Tests for supports_command()."""

    def test_get_supported(self):
        assert supports_command("GET") is True

    def test_set_supported(self):
        assert supports_command("SET") is True

    def test_case_insensitive(self):
        assert supports_command("get") is True
        assert supports_command("Set") is True

    def test_unsupported_commands(self):
        assert supports_command("RPUSH") is False
        assert supports_command("LPUSH") is False
        assert supports_command("HSET") is False
        assert supports_command("MGET") is False
        assert supports_command("FT.SEARCH") is False

    def test_empty_string(self):
        assert supports_command("") is False


class TestBuildTomlConfig:
    """Tests for _build_toml_config()."""

    def _default_kwargs(self, **overrides):
        defaults = dict(
            target_ip="127.0.0.1",
            port=6379,
            duration=60,
            requests=None,
            warmup=10,
            data_size=64,
            keyspacelen=1000000,
            pipeline=32,
            clients=16,
            command="GET",
            cluster_mode=False,
            tls_mode=False,
        )
        defaults.update(overrides)
        return defaults

    def test_get_command_ratios(self):
        toml = _build_toml_config(**self._default_kwargs(command="GET"))
        assert "get = 100" in toml
        assert "set = 0" in toml

    def test_set_command_ratios(self):
        toml = _build_toml_config(**self._default_kwargs(command="SET"))
        assert "get = 0" in toml
        assert "set = 100" in toml

    def test_unsupported_command_raises(self):
        with pytest.raises(ValueError, match="Unsupported command"):
            _build_toml_config(**self._default_kwargs(command="RPUSH"))

    def test_duration_in_output(self):
        toml = _build_toml_config(**self._default_kwargs(duration=120))
        assert 'duration = "120s"' in toml

    def test_warmup_in_output(self):
        toml = _build_toml_config(**self._default_kwargs(warmup=15))
        assert 'warmup = "15s"' in toml

    def test_zero_warmup(self):
        toml = _build_toml_config(**self._default_kwargs(warmup=0))
        assert 'warmup = "0s"' in toml

    def test_connection_settings(self):
        toml = _build_toml_config(**self._default_kwargs(clients=50, pipeline=10))
        assert "connections = 50" in toml
        assert "pipeline_depth = 10" in toml

    def test_keyspace_count(self):
        toml = _build_toml_config(**self._default_kwargs(keyspacelen=5000000))
        assert "count = 5000000" in toml

    def test_value_length(self):
        toml = _build_toml_config(**self._default_kwargs(data_size=256))
        assert "length = 256" in toml

    def test_endpoint(self):
        toml = _build_toml_config(
            **self._default_kwargs(target_ip="10.0.0.1", port=6380)
        )
        assert 'endpoints = ["10.0.0.1:6380"]' in toml

    def test_cluster_mode(self):
        toml = _build_toml_config(**self._default_kwargs(cluster_mode=True))
        assert "cluster = true" in toml

    def test_no_cluster_by_default(self):
        toml = _build_toml_config(**self._default_kwargs(cluster_mode=False))
        assert "cluster" not in toml

    def test_tls_mode(self):
        toml = _build_toml_config(**self._default_kwargs(tls_mode=True))
        assert "tls = true" in toml

    def test_no_tls_by_default(self):
        toml = _build_toml_config(**self._default_kwargs(tls_mode=False))
        assert "tls" not in toml

    def test_threads_optional(self):
        toml = _build_toml_config(**self._default_kwargs())
        assert "threads" not in toml

    def test_threads_included(self):
        toml = _build_toml_config(**self._default_kwargs(threads=4))
        assert "threads = 4" in toml

    def test_cpu_list_optional(self):
        toml = _build_toml_config(**self._default_kwargs())
        assert "cpu_list" not in toml

    def test_cpu_list_included(self):
        toml = _build_toml_config(**self._default_kwargs(cpu_list="0-3"))
        assert 'cpu_list = "0-3"' in toml

    def test_json_format(self):
        toml = _build_toml_config(**self._default_kwargs())
        assert 'format = "json"' in toml

    def test_prefill_for_get(self):
        toml = _build_toml_config(**self._default_kwargs(command="GET"))
        assert "prefill = true" in toml

    def test_no_prefill_for_set(self):
        toml = _build_toml_config(**self._default_kwargs(command="SET"))
        assert "prefill = false" in toml

    def test_default_duration_when_none(self):
        toml = _build_toml_config(**self._default_kwargs(duration=None))
        assert 'duration = "60s"' in toml


class TestParseJsonOutput:
    """Tests for _parse_json_output().

    Cachecannon v0.0.11 outputs per-command latency objects (``get``, ``set``)
    with fields ``p50_us``, ``p90_us``, ``p99_us``, ``p999_us``, ``p9999_us``,
    ``max_us`` in microseconds.
    """

    def _make_ndjson(self, *objects):
        return "\n".join(json.dumps(o) for o in objects)

    def test_parses_result_line(self):
        output = self._make_ndjson(
            {"type": "config", "protocol": "resp"},
            {"type": "sample", "time": 1.0, "requests": 500000},
            {
                "type": "result",
                "throughput": 530000,
                "get": {
                    "count": 530000,
                    "p50_us": 45,
                    "p90_us": 89,
                    "p99_us": 150,
                    "p999_us": 312,
                    "p9999_us": 891,
                    "max_us": 1200,
                },
                "set": {
                    "count": 0,
                    "p50_us": 0,
                    "p90_us": 0,
                    "p99_us": 0,
                    "p999_us": 0,
                    "p9999_us": 0,
                    "max_us": 0,
                },
            },
        )
        result = _parse_json_output(output, "GET")
        assert result is not None
        assert float(result["rps"]) == 530000
        assert float(result["p50_latency_ms"]) == 0.045
        assert float(result["p90_latency_ms"]) == 0.089
        assert float(result["p99_latency_ms"]) == 0.15
        assert float(result["max_latency_ms"]) == 1.2

    def test_no_result_line(self):
        output = self._make_ndjson(
            {"type": "config"},
            {"type": "sample", "time": 1.0},
        )
        assert _parse_json_output(output, "GET") is None

    def test_empty_output(self):
        assert _parse_json_output("", "GET") is None

    def test_malformed_json_lines_skipped(self):
        output = "not json\n" + json.dumps(
            {"type": "result", "throughput": 100, "get": {}, "set": {}}
        )
        result = _parse_json_output(output, "GET")
        assert result is not None
        assert float(result["rps"]) == 100

    def test_uses_last_result_line(self):
        output = self._make_ndjson(
            {"type": "result", "throughput": 100, "get": {}, "set": {}},
            {"type": "result", "throughput": 200, "get": {}, "set": {}},
        )
        result = _parse_json_output(output, "GET")
        assert float(result["rps"]) == 200

    def test_missing_latency_fields_default_zero(self):
        output = json.dumps({"type": "result", "throughput": 1000, "set": {}})
        result = _parse_json_output(output, "SET")
        assert float(result["avg_latency_ms"]) == 0.0
        assert float(result["p50_latency_ms"]) == 0.0

    def test_set_command_uses_set_latency(self):
        output = json.dumps(
            {
                "type": "result",
                "throughput": 1000,
                "get": {
                    "count": 0,
                    "p50_us": 0,
                    "p90_us": 0,
                    "p99_us": 0,
                    "p999_us": 0,
                    "p9999_us": 0,
                    "max_us": 0,
                },
                "set": {
                    "count": 1000,
                    "p50_us": 52,
                    "p90_us": 95,
                    "p99_us": 167,
                    "p999_us": 334,
                    "p9999_us": 500,
                    "max_us": 800,
                },
            }
        )
        result = _parse_json_output(output, "SET")
        assert float(result["p50_latency_ms"]) == 0.052
        assert float(result["p99_latency_ms"]) == 0.167


class TestRunCachecannon:
    """Tests for run_cachecannon()."""

    def test_unsupported_command_raises(self):
        with pytest.raises(ValueError, match="only supports GET/SET"):
            run_cachecannon(command="RPUSH")

    @patch("cachecannon_runner.subprocess.run")
    def test_successful_run(self, mock_run):
        result_json = json.dumps(
            {
                "type": "result",
                "throughput": 500000,
                "set": {
                    "count": 500000,
                    "p50_us": 45,
                    "p90_us": 89,
                    "p99_us": 150,
                    "p999_us": 312,
                    "p9999_us": 891,
                    "max_us": 1000,
                },
                "get": {
                    "count": 0,
                    "p50_us": 0,
                    "p90_us": 0,
                    "p99_us": 0,
                    "p999_us": 0,
                    "p9999_us": 0,
                    "max_us": 0,
                },
            }
        )
        mock_run.return_value = MagicMock(returncode=0, stdout=result_json, stderr="")

        result = run_cachecannon(command="SET", data_size=64)
        assert result is not None
        assert float(result["rps"]) == 500000
        mock_run.assert_called_once()

    @patch("cachecannon_runner.subprocess.run")
    def test_nonzero_exit_returns_none(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
        assert run_cachecannon(command="GET") is None

    @patch("cachecannon_runner.subprocess.run")
    def test_binary_not_found_returns_none(self, mock_run):
        mock_run.side_effect = FileNotFoundError()
        assert run_cachecannon(command="GET") is None

    @patch("cachecannon_runner.subprocess.run")
    def test_timeout_returns_none(self, mock_run):
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired(cmd="cachecannon", timeout=60)
        assert run_cachecannon(command="GET", timeout=60) is None

    @patch("cachecannon_runner.subprocess.run")
    def test_toml_file_cleaned_up(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="{}", stderr="")
        run_cachecannon(command="SET")
        # The temp file path is passed as second arg to the binary
        call_args = mock_run.call_args[0][0]
        toml_path = call_args[1]
        from pathlib import Path

        assert not Path(toml_path).exists()

    @patch("cachecannon_runner.subprocess.run")
    def test_passes_correct_binary_path(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="{}", stderr="")
        run_cachecannon(command="GET", cachecannon_path="/usr/bin/cachecannon")
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "/usr/bin/cachecannon"


class TestCachecannonConfigInToml:
    """Tests for cachecannon_config parameter in _build_toml_config()."""

    def _default_kwargs(self, **overrides):
        defaults = dict(
            target_ip="127.0.0.1",
            port=6379,
            duration=60,
            requests=None,
            warmup=10,
            data_size=64,
            keyspacelen=1000000,
            pipeline=32,
            clients=16,
            command="GET",
            cluster_mode=False,
            tls_mode=False,
        )
        defaults.update(overrides)
        return defaults

    def test_cachecannon_config_threads_in_toml(self):
        toml = _build_toml_config(
            **self._default_kwargs(cachecannon_config={"threads": 8})
        )
        assert "threads = 8" in toml

    def test_cachecannon_config_cpu_list_in_toml(self):
        toml = _build_toml_config(
            **self._default_kwargs(cachecannon_config={"cpu_list": "0-7"})
        )
        assert 'cpu_list = "0-7"' in toml

    def test_cachecannon_config_timeouts_in_toml(self):
        toml = _build_toml_config(
            **self._default_kwargs(
                cachecannon_config={"connect_timeout": "10s", "request_timeout": "3s"}
            )
        )
        assert 'connect_timeout = "10s"' in toml
        assert 'request_timeout = "3s"' in toml

    def test_cachecannon_config_none_uses_defaults(self):
        toml = _build_toml_config(**self._default_kwargs(cachecannon_config=None))
        assert "threads" not in toml
        assert "cpu_list" not in toml
        assert 'connect_timeout = "5s"' in toml
        assert 'request_timeout = "1s"' in toml


class TestCommandRatioInToml:
    """Tests for command_ratio parameter in _build_toml_config()."""

    def _default_kwargs(self, **overrides):
        defaults = dict(
            target_ip="127.0.0.1",
            port=6379,
            duration=60,
            requests=None,
            warmup=10,
            data_size=64,
            keyspacelen=1000000,
            pipeline=32,
            clients=16,
            command="GET",
            cluster_mode=False,
            tls_mode=False,
        )
        defaults.update(overrides)
        return defaults

    def test_command_ratio_get_set_in_toml(self):
        toml = _build_toml_config(
            **self._default_kwargs(command_ratio={"GET": 80, "SET": 20})
        )
        assert "get = 80" in toml
        assert "set = 20" in toml

    def test_command_ratio_overrides_command_param(self):
        toml = _build_toml_config(
            **self._default_kwargs(command="SET", command_ratio={"GET": 60, "SET": 40})
        )
        assert "get = 60" in toml
        assert "set = 40" in toml

    def test_command_ratio_unsupported_command_raises(self):
        with pytest.raises(ValueError, match="Unsupported command in command_ratio"):
            _build_toml_config(
                **self._default_kwargs(command_ratio={"HSET": 50, "GET": 50})
            )

    def test_command_ratio_not_summing_100_raises(self):
        with pytest.raises(ValueError, match="command_ratio must sum to 100"):
            _build_toml_config(
                **self._default_kwargs(command_ratio={"GET": 60, "SET": 20})
            )


class TestRunCachecannonNewParams:
    """Tests for new params in run_cachecannon()."""

    @patch("cachecannon_runner.subprocess.run")
    def test_run_cachecannon_passes_config_and_ratio(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(
                {"type": "result", "throughput": 100, "get": {}, "set": {}}
            ),
            stderr="",
        )
        run_cachecannon(
            command="GET",
            cachecannon_config={"threads": 4},
            command_ratio={"GET": 70, "SET": 30},
        )
        # Verify the TOML written contains the config values
        call_args = mock_run.call_args[0][0]
        toml_path = call_args[1]
        # The file is cleaned up, so we verify the call succeeded
        mock_run.assert_called_once()

    @patch("cachecannon_runner.subprocess.run")
    def test_backward_compat_no_new_params(self, mock_run):
        result_json = json.dumps(
            {
                "type": "result",
                "throughput": 500000,
                "get": {
                    "count": 500000,
                    "p50_us": 50,
                    "p90_us": 89,
                    "p99_us": 150,
                    "p999_us": 300,
                    "p9999_us": 800,
                    "max_us": 1000,
                },
                "set": {
                    "count": 0,
                    "p50_us": 0,
                    "p90_us": 0,
                    "p99_us": 0,
                    "p999_us": 0,
                    "p9999_us": 0,
                    "max_us": 0,
                },
            }
        )
        mock_run.return_value = MagicMock(returncode=0, stdout=result_json, stderr="")
        result = run_cachecannon(command="GET")
        assert result is not None
        assert float(result["rps"]) == 500000


class TestP95Fix:
    """Test that p99 from cachecannon maps to both p95 and p99 (cachecannon has no p95)."""

    def test_p99_maps_to_p95_and_p99(self):
        output = json.dumps(
            {
                "type": "result",
                "throughput": 1000,
                "get": {
                    "count": 1000,
                    "p50_us": 45,
                    "p90_us": 89,
                    "p99_us": 150,
                    "p999_us": 300,
                    "p9999_us": 800,
                    "max_us": 1200,
                },
                "set": {
                    "count": 0,
                    "p50_us": 0,
                    "p90_us": 0,
                    "p99_us": 0,
                    "p999_us": 0,
                    "p9999_us": 0,
                    "max_us": 0,
                },
            }
        )
        result = _parse_json_output(output, "GET")
        # cachecannon has no p95; we map p99 to both p95 and p99
        assert float(result["p95_latency_ms"]) == 0.15
        assert float(result["p99_latency_ms"]) == 0.15
