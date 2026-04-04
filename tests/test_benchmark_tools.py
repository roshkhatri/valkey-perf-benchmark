"""Tests for the runners benchmark tool abstraction layer."""

import dataclasses
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest

from runners.base import (
    BenchmarkResult,
    BenchmarkTool,
    RunContext,
    _TOOL_REGISTRY,
    available_tools,
    create_tool,
    register_tool,
)
from runners.valkey_benchmark_tool import ValkeyBenchmarkTool
from runners.cachecannon_tool import CachecannonTool


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_result():
    """A BenchmarkResult with only core fields set."""
    return BenchmarkResult(
        rps=100000.0,
        avg_latency_ms=0.5,
        min_latency_ms=0.1,
        p50_latency_ms=0.4,
        p95_latency_ms=0.8,
        p99_latency_ms=1.2,
        max_latency_ms=5.0,
    )


@pytest.fixture
def result_with_tails():
    """A BenchmarkResult with tail latencies populated."""
    return BenchmarkResult(
        rps=80000.0,
        avg_latency_ms=0.6,
        min_latency_ms=0.1,
        p50_latency_ms=0.5,
        p95_latency_ms=1.0,
        p99_latency_ms=2.0,
        max_latency_ms=10.0,
        p90_latency_ms=0.9,
        p999_latency_ms=5.0,
        p9999_latency_ms=8.0,
    )


@pytest.fixture
def run_context():
    """Minimal RunContext for testing."""
    return RunContext(
        target_ip="127.0.0.1",
        port=6379,
        cluster_mode=False,
        tls_mode=False,
        valkey_path=Path("/tmp/valkey"),
    )


@pytest.fixture
def tls_context():
    """RunContext with TLS and CPU pinning."""
    return RunContext(
        target_ip="10.0.0.1",
        port=6380,
        cluster_mode=True,
        tls_mode=True,
        valkey_path=Path("/tmp/valkey"),
        cores="0-3",
    )


SAMPLE_CSV = (
    '"test","rps","avg_latency_ms","min_latency_ms",'
    '"p50_latency_ms","p95_latency_ms","p99_latency_ms","max_latency_ms"\n'
    '"SET","150000.00","0.500","0.100","0.400","0.800","1.200","5.000"\n'
)


# ===========================================================================
# BenchmarkResult
# ===========================================================================


class TestBenchmarkResult:
    """Tests for BenchmarkResult dataclass."""

    def test_to_row_dict_has_7_keys(self, sample_result):
        row = sample_result.to_row_dict()
        assert len(row) == 7

    def test_to_row_dict_values_are_strings(self, sample_result):
        row = sample_result.to_row_dict()
        assert all(isinstance(v, str) for v in row.values())

    def test_to_row_dict_keys(self, sample_result):
        expected = {
            "rps",
            "avg_latency_ms",
            "min_latency_ms",
            "p50_latency_ms",
            "p95_latency_ms",
            "p99_latency_ms",
            "max_latency_ms",
        }
        assert set(sample_result.to_row_dict().keys()) == expected

    def test_extra_latencies_empty_when_defaults(self, sample_result):
        assert sample_result.extra_latencies() == {}

    def test_extra_latencies_returns_nonzero_only(self, result_with_tails):
        extras = result_with_tails.extra_latencies()
        assert "p90_latency_ms" in extras
        assert "p999_latency_ms" in extras
        assert "p9999_latency_ms" in extras
        # These were left at default 0.0
        assert "p1_latency_ms" not in extras
        assert "p5_latency_ms" not in extras

    def test_extra_latencies_values(self, result_with_tails):
        extras = result_with_tails.extra_latencies()
        assert extras["p90_latency_ms"] == 0.9
        assert extras["p999_latency_ms"] == 5.0
        assert extras["p9999_latency_ms"] == 8.0


# ===========================================================================
# RunContext
# ===========================================================================


class TestRunContext:
    """Tests for RunContext frozen dataclass."""

    def test_is_immutable(self, run_context):
        with pytest.raises(dataclasses.FrozenInstanceError):
            run_context.port = 9999

    def test_defaults(self):
        ctx = RunContext(
            target_ip="localhost",
            port=6379,
            cluster_mode=False,
            tls_mode=False,
            valkey_path=Path("/tmp"),
        )
        assert ctx.cores is None
        assert ctx.tool_config is None


# ===========================================================================
# Registry
# ===========================================================================


class TestRegistry:
    """Tests for tool registry functions."""

    def test_register_tool_decorator(self):
        assert "valkey-benchmark" in _TOOL_REGISTRY
        assert "cachecannon" in _TOOL_REGISTRY

    def test_create_tool_valkey_benchmark(self):
        tool = create_tool("valkey-benchmark")
        assert isinstance(tool, ValkeyBenchmarkTool)

    def test_create_tool_cachecannon(self):
        tool = create_tool("cachecannon")
        assert isinstance(tool, CachecannonTool)

    def test_create_tool_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown tool"):
            create_tool("nonexistent-tool")

    def test_available_tools_includes_both(self):
        tools = available_tools()
        assert "valkey-benchmark" in tools
        assert "cachecannon" in tools

    def test_register_custom_tool(self):
        @register_tool("custom-test-tool")
        class CustomTool(BenchmarkTool):
            @property
            def name(self):
                return "custom-test-tool"

            def supports_command(self, command):
                return True

            def supports_command_ratio(self):
                return False

            def run(self, scenario, context):
                return None

        try:
            tool = create_tool("custom-test-tool")
            assert tool.name == "custom-test-tool"
        finally:
            _TOOL_REGISTRY.pop("custom-test-tool", None)


# ===========================================================================
# ValkeyBenchmarkTool
# ===========================================================================


class TestValkeyBenchmarkTool:
    """Tests for ValkeyBenchmarkTool."""

    def test_name(self):
        assert ValkeyBenchmarkTool().name == "valkey-benchmark"

    def test_supports_read_commands(self):
        tool = ValkeyBenchmarkTool()
        for cmd in ("GET", "MGET", "LRANGE", "SISMEMBER", "ZSCORE", "ZRANGE"):
            assert tool.supports_command(cmd), f"Should support {cmd}"

    def test_supports_write_commands(self):
        tool = ValkeyBenchmarkTool()
        for cmd in ("SET", "INCR", "LPUSH", "RPUSH", "SADD", "HSET", "ZADD"):
            assert tool.supports_command(cmd), f"Should support {cmd}"

    def test_does_not_support_unknown(self):
        assert not ValkeyBenchmarkTool().supports_command("FT.SEARCH")

    def test_does_not_support_command_ratio(self):
        assert ValkeyBenchmarkTool().supports_command_ratio() is False

    def test_run_builds_correct_command(self, run_context):
        tool = ValkeyBenchmarkTool(benchmark_path="/usr/bin/vb")
        scenario = {
            "command": "SET",
            "duration": 30,
            "data_size": 128,
            "pipeline": 16,
            "clients": 50,
        }
        cmd = tool._build_command(scenario, run_context)
        assert cmd[0] == "/usr/bin/vb"
        assert "-h" in cmd
        assert "127.0.0.1" in cmd
        assert "-p" in cmd
        assert "6379" in cmd
        assert "--duration" in cmd
        assert "30" in cmd
        assert "-t" in cmd
        assert "SET" in cmd
        assert "--csv" in cmd

    def test_run_parses_csv(self):
        result = ValkeyBenchmarkTool._parse_csv(SAMPLE_CSV)
        assert result is not None
        assert result.rps == 150000.0
        assert result.avg_latency_ms == 0.5
        assert result.p99_latency_ms == 1.2

    def test_run_returns_none_on_failure(self, run_context):
        tool = ValkeyBenchmarkTool()
        with patch("subprocess.run", side_effect=Exception("boom")):
            result = tool.run({"command": "SET"}, run_context)
            assert result is None

    def test_tls_flags(self, tls_context):
        tool = ValkeyBenchmarkTool()
        cmd = tool._build_command({"command": "GET"}, tls_context)
        assert "--tls" in cmd
        assert "--cert" in cmd
        assert "--cacert" in cmd

    def test_taskset(self, tls_context):
        tool = ValkeyBenchmarkTool()
        cmd = tool._build_command({"command": "GET"}, tls_context)
        assert cmd[0] == "taskset"
        assert cmd[1] == "-c"
        assert cmd[2] == "0-3"

    def test_requests_mode(self, run_context):
        tool = ValkeyBenchmarkTool()
        cmd = tool._build_command({"command": "SET", "requests": 100000}, run_context)
        assert "-n" in cmd
        assert "100000" in cmd
        assert "--duration" not in cmd

    def test_duration_mode(self, run_context):
        tool = ValkeyBenchmarkTool()
        cmd = tool._build_command({"command": "SET", "duration": 60}, run_context)
        assert "--duration" in cmd
        assert "60" in cmd
        assert "-n" not in cmd

    @patch("subprocess.run")
    def test_run_success(self, mock_run, run_context):
        mock_run.return_value = MagicMock(stdout=SAMPLE_CSV, returncode=0)
        tool = ValkeyBenchmarkTool()
        result = tool.run({"command": "SET", "duration": 10}, run_context)
        assert result is not None
        assert result.rps == 150000.0
        mock_run.assert_called_once()

    def test_parse_csv_empty(self):
        assert ValkeyBenchmarkTool._parse_csv("") is None

    def test_parse_csv_no_header(self):
        assert ValkeyBenchmarkTool._parse_csv("some random output\n") is None

    def test_benchmark_threads(self, run_context):
        tool = ValkeyBenchmarkTool(benchmark_threads=4)
        cmd = tool._build_command({"command": "SET"}, run_context)
        idx = cmd.index("--threads")
        assert cmd[idx + 1] == "4"


# ===========================================================================
# CachecannonTool
# ===========================================================================


class TestCachecannonTool:
    """Tests for CachecannonTool."""

    def test_name(self):
        assert CachecannonTool().name == "cachecannon"

    def test_supports_get(self):
        assert CachecannonTool().supports_command("GET") is True

    def test_supports_set(self):
        assert CachecannonTool().supports_command("SET") is True

    def test_does_not_support_other(self):
        tool = CachecannonTool()
        assert tool.supports_command("LPUSH") is False
        assert tool.supports_command("HSET") is False
        assert tool.supports_command("FT.SEARCH") is False

    def test_supports_command_ratio(self):
        assert CachecannonTool().supports_command_ratio() is True

    @patch("runners.cachecannon_tool.run_cachecannon")
    def test_run_calls_runner(self, mock_runner, run_context):
        mock_runner.return_value = {
            "rps": "50000",
            "avg_latency_ms": "1.0",
            "min_latency_ms": "0.1",
            "p50_latency_ms": "0.8",
            "p95_latency_ms": "2.0",
            "p99_latency_ms": "3.0",
            "max_latency_ms": "10.0",
        }
        tool = CachecannonTool()
        result = tool.run({"command": "GET", "duration": 30}, run_context)
        assert result is not None
        assert result.rps == 50000.0
        mock_runner.assert_called_once()

    @patch("runners.cachecannon_tool.run_cachecannon")
    def test_passes_tool_config(self, mock_runner, run_context):
        ctx = RunContext(
            target_ip="127.0.0.1",
            port=6379,
            cluster_mode=False,
            tls_mode=False,
            valkey_path=Path("/tmp/valkey"),
            tool_config={"timeout": 600},
        )
        mock_runner.return_value = None
        tool = CachecannonTool()
        tool.run({"command": "SET"}, ctx)
        _, kwargs = mock_runner.call_args
        assert kwargs.get("timeout") == 600

    @patch("runners.cachecannon_tool.run_cachecannon")
    def test_passes_command_ratio(self, mock_runner, run_context):
        mock_runner.return_value = None
        tool = CachecannonTool()
        tool.run({"command": "GET", "command_ratio": "80:20"}, run_context)
        mock_runner.assert_called_once()

    @patch("runners.cachecannon_tool.run_cachecannon")
    def test_returns_none_on_failure(self, mock_runner, run_context):
        mock_runner.return_value = None
        result = CachecannonTool().run({"command": "GET"}, run_context)
        assert result is None

    @patch("runners.cachecannon_tool.run_cachecannon")
    def test_populates_tail_latencies(self, mock_runner, run_context):
        mock_runner.return_value = {
            "rps": "50000",
            "avg_latency_ms": "1.0",
            "min_latency_ms": "0.1",
            "p50_latency_ms": "0.8",
            "p95_latency_ms": "2.0",
            "p99_latency_ms": "3.0",
            "max_latency_ms": "10.0",
            "p90_latency_ms": "1.5",
            "p999_latency_ms": "7.0",
            "p9999_latency_ms": "9.0",
        }
        result = CachecannonTool().run({"command": "GET"}, run_context)
        assert result is not None
        assert result.p90_latency_ms == 1.5
        assert result.p999_latency_ms == 7.0
        assert result.p9999_latency_ms == 9.0
        extras = result.extra_latencies()
        assert "p90_latency_ms" in extras
        assert "p999_latency_ms" in extras
