"""End-to-end integration tests for config → tool → metrics pipeline."""

from pathlib import Path

import pytest

from .conftest import PROJECT_ROOT

from benchmark import expand_matrix, load_configs, validate_config
from process_metrics import MetricsProcessor
from runners import BenchmarkResult, available_tools, create_tool
from valkey_benchmark import ClientRunner, READ_COMMANDS, WRITE_COMMANDS


CONFIGS_DIR = PROJECT_ROOT / "configs"

ALL_STANDARD_COMMANDS = set(READ_COMMANDS + WRITE_COMMANDS)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _all_scenarios(configs):
    """Flatten all scenarios from loaded configs."""
    scenarios = []
    for cfg in configs:
        for group in cfg.get("test_groups", []):
            scenarios.extend(group.get("scenarios", []))
    return scenarios


# ---------------------------------------------------------------------------
# 1. Config → Scenarios end-to-end
# ---------------------------------------------------------------------------


class TestConfigToScenariosEndToEnd:
    """Load real config files and verify the full JSON → validate → expand pipeline."""

    def test_benchmark_configs_produces_13_scenarios(self):
        configs = load_configs(str(CONFIGS_DIR / "benchmark-configs.json"))
        scenarios = _all_scenarios(configs)
        assert len(scenarios) == 13
        commands = {s["command"] for s in scenarios}
        assert "SET" in commands
        assert "GET" in commands

    def test_arm_config_matrix_expands_to_12(self):
        configs = load_configs(str(CONFIGS_DIR / "benchmark-config-arm.json"))
        scenarios = _all_scenarios(configs)
        # 2 commands × 3 data_sizes × 2 pipelines = 12
        assert len(scenarios) == 12

    def test_tag_arm_config_matrix_expands_to_8(self):
        configs = load_configs(str(CONFIGS_DIR / "benchmark-config-tag-arm.json"))
        scenarios = _all_scenarios(configs)
        # 2 commands × 2 data_sizes × 2 pipelines = 8
        assert len(scenarios) == 8

    def test_cluster_tls_config_produces_11_scenarios(self):
        configs = load_configs(str(CONFIGS_DIR / "benchmark-configs-cluster-tls.json"))
        scenarios = _all_scenarios(configs)
        assert len(scenarios) == 11
        assert configs[0]["cluster_mode"] is True
        assert configs[0]["tls_mode"] is True

    def test_module_config_unchanged(self):
        configs = load_configs(str(CONFIGS_DIR / "module-test-arm.json"))
        scenarios = _all_scenarios(configs)
        assert len(scenarios) == 2
        # cluster_mode is a list [false, true], not coerced to bool
        assert isinstance(configs[0]["cluster_mode"], list)

    def test_arm_config_preserves_top_level_fields(self):
        configs = load_configs(str(CONFIGS_DIR / "benchmark-config-arm.json"))
        cfg = configs[0]
        assert "io-threads" in cfg
        assert "server_cpu_range" in cfg
        assert "client_cpu_range" in cfg

    def test_read_commands_have_auto_populate(self):
        configs = load_configs(str(CONFIGS_DIR / "benchmark-configs.json"))
        scenarios = _all_scenarios(configs)
        get_scenarios = [s for s in scenarios if s["command"] == "GET"]
        assert len(get_scenarios) > 0
        for s in get_scenarios:
            assert s.get("auto_populate") is True


# ---------------------------------------------------------------------------
# 2. Tool selection end-to-end
# ---------------------------------------------------------------------------


def _make_runner_with_tools(primary_name, fallback_name=None):
    """Build a ClientRunner and manually assign tools."""
    config = {
        "test_groups": [{"group": 1, "scenarios": [{"id": "test", "command": "GET"}]}]
    }
    runner = ClientRunner(
        commit_id="test123",
        config=config,
        cluster_mode=False,
        tls_mode=False,
        target_ip="127.0.0.1",
        results_dir=Path("/tmp"),
        valkey_path="/tmp/valkey",
        valkey_benchmark_path="/tmp/valkey-benchmark",
    )
    runner.tool = create_tool(primary_name, **_tool_kwargs(primary_name))
    if fallback_name:
        runner.fallback_tool = create_tool(fallback_name, **_tool_kwargs(fallback_name))
    return runner


def _tool_kwargs(name):
    if name == "valkey-benchmark":
        return {"benchmark_path": "/tmp/vb"}
    return {}


class TestToolSelectionEndToEnd:
    """Test tool registry + tool selection logic end-to-end."""

    def test_registry_has_both_tools(self):
        tools = available_tools()
        assert "valkey-benchmark" in tools
        assert "cachecannon" in tools

    def test_create_valkey_tool_supports_all_standard_commands(self):
        tool = create_tool("valkey-benchmark", benchmark_path="/tmp/vb")
        for cmd in ALL_STANDARD_COMMANDS:
            assert tool.supports_command(cmd), f"{cmd} should be supported"

    def test_create_cachecannon_tool_supports_only_get_set(self):
        tool = create_tool("cachecannon")
        assert tool.supports_command("GET")
        assert tool.supports_command("SET")
        assert not tool.supports_command("RPUSH")

    def test_tool_selection_prefers_primary_for_supported_command(self):
        runner = _make_runner_with_tools("cachecannon", "valkey-benchmark")
        selected = runner._select_tool({"command": "GET"})
        assert selected.name == "cachecannon"

    def test_tool_selection_falls_back_for_unsupported_command(self):
        runner = _make_runner_with_tools("cachecannon", "valkey-benchmark")
        selected = runner._select_tool({"command": "RPUSH"})
        assert selected.name == "valkey-benchmark"

    def test_command_ratio_requires_supporting_tool(self):
        runner = _make_runner_with_tools("valkey-benchmark")
        with pytest.raises(ValueError, match="command_ratio"):
            runner._select_tool(
                {"command": "GET", "command_ratio": {"GET": 80, "SET": 20}}
            )


# ---------------------------------------------------------------------------
# 3. BenchmarkResult → Metrics end-to-end
# ---------------------------------------------------------------------------


class TestBenchmarkResultToMetricsEndToEnd:
    """Test BenchmarkResult → MetricsProcessor → metrics dict flow."""

    def test_result_to_metrics_preserves_all_required_keys(self):
        result = BenchmarkResult(
            rps=100000.0,
            avg_latency_ms=0.5,
            min_latency_ms=0.1,
            p50_latency_ms=0.4,
            p95_latency_ms=0.8,
            p99_latency_ms=1.2,
            max_latency_ms=5.0,
        )
        row = result.to_row_dict()
        processor = MetricsProcessor(
            commit_id="abc123",
            cluster_mode=False,
            tls_mode=False,
            commit_time="2024-01-01T00:00:00Z",
        )
        metrics = processor.create_metrics(
            benchmark_data=row,
            command="GET",
            data_size=16,
            pipeline=1,
            clients=50,
            requests=100000,
        )
        assert metrics is not None
        for key in (
            "timestamp",
            "commit",
            "command",
            "data_size",
            "pipeline",
            "clients",
            "rps",
            "avg_latency_ms",
            "min_latency_ms",
            "p50_latency_ms",
            "p95_latency_ms",
            "p99_latency_ms",
            "max_latency_ms",
            "cluster_mode",
            "tls",
            "benchmark_mode",
        ):
            assert key in metrics, f"Missing key: {key}"

    def test_extra_latencies_merge_into_metrics(self):
        result = BenchmarkResult(
            rps=100000.0,
            avg_latency_ms=0.5,
            min_latency_ms=0.1,
            p50_latency_ms=0.4,
            p95_latency_ms=0.8,
            p99_latency_ms=1.2,
            max_latency_ms=5.0,
            p999_latency_ms=2.5,
        )
        extras = result.extra_latencies()
        assert "p999_latency_ms" in extras
        assert extras["p999_latency_ms"] == 2.5

        # Merge into metrics dict
        row = result.to_row_dict()
        processor = MetricsProcessor(
            commit_id="abc123",
            cluster_mode=False,
            tls_mode=False,
            commit_time="2024-01-01T00:00:00Z",
        )
        metrics = processor.create_metrics(
            benchmark_data=row,
            command="GET",
            data_size=16,
            pipeline=1,
            clients=50,
            requests=100000,
        )
        metrics.update(extras)
        assert metrics["p999_latency_ms"] == 2.5

    def test_metrics_schema_backward_compatible(self):
        result = BenchmarkResult(
            rps=50000.0,
            avg_latency_ms=1.0,
            min_latency_ms=0.2,
            p50_latency_ms=0.8,
            p95_latency_ms=1.5,
            p99_latency_ms=2.0,
            max_latency_ms=10.0,
        )
        processor = MetricsProcessor(
            commit_id="abc123",
            cluster_mode=False,
            tls_mode=False,
            commit_time="2024-01-01T00:00:00Z",
        )
        metrics = processor.create_metrics(
            benchmark_data=result.to_row_dict(),
            command="SET",
            data_size=16,
            pipeline=1,
            clients=50,
            requests=100000,
        )
        # Keys expected by push_to_postgres
        required = {
            "timestamp",
            "commit",
            "repository",
            "command",
            "data_size",
            "pipeline",
            "clients",
            "rps",
            "avg_latency_ms",
            "min_latency_ms",
            "p50_latency_ms",
            "p95_latency_ms",
            "p99_latency_ms",
            "max_latency_ms",
            "cluster_mode",
            "tls",
            "benchmark_mode",
        }
        assert required.issubset(metrics.keys())


# ---------------------------------------------------------------------------
# 4. Mixed config combinations
# ---------------------------------------------------------------------------


class TestMixedConfigCombinations:
    """Validate configs that exercise multiple features together."""

    def test_config_with_matrix_and_cachecannon_section(self):
        cfg = {
            "cluster_mode": False,
            "tls_mode": False,
            "cachecannon": {"threads": 4},
            "test_groups": [
                {
                    "group": 1,
                    "matrix": {"data_size": [16, 64], "pipeline": [1, 10]},
                    "scenarios": [
                        {"id": "set", "command": "SET", "clients": 50, "duration": 60}
                    ],
                }
            ],
        }
        validate_config(cfg)
        expanded = expand_matrix(cfg["test_groups"][0])
        assert len(expanded["scenarios"]) == 4

    def test_config_with_command_ratio_validates(self):
        cfg = {
            "cluster_mode": False,
            "tls_mode": False,
            "test_groups": [
                {
                    "group": 1,
                    "scenarios": [
                        {
                            "id": "mixed",
                            "command": "GET",
                            "clients": 50,
                            "duration": 60,
                            "command_ratio": {"GET": 80, "SET": 20},
                        }
                    ],
                }
            ],
        }
        validate_config(cfg)  # Should not raise

    def test_config_with_server_startup_config_validates(self):
        cfg = {
            "cluster_mode": False,
            "tls_mode": False,
            "server_startup_config": {"maxmemory": "1gb"},
            "test_groups": [
                {
                    "group": 1,
                    "scenarios": [
                        {"id": "set", "command": "SET", "clients": 50, "duration": 60}
                    ],
                }
            ],
        }
        validate_config(cfg)  # Should not raise

    def test_config_with_all_features_combined(self):
        cfg = {
            "cluster_mode": False,
            "tls_mode": False,
            "cachecannon": {"threads": 4},
            "server_startup_config": {"maxmemory": "1gb"},
            "test_groups": [
                {
                    "group": 1,
                    "matrix": {"data_size": [16, 64], "pipeline": [1]},
                    "scenarios": [
                        {
                            "id": "mixed",
                            "command": "GET",
                            "clients": 50,
                            "duration": 60,
                            "command_ratio": {"GET": 80, "SET": 20},
                        }
                    ],
                }
            ],
        }
        validate_config(cfg)
        expanded = expand_matrix(cfg["test_groups"][0])
        assert len(expanded["scenarios"]) == 2

    def test_matrix_expansion_preserves_command_ratio(self):
        group = {
            "group": 1,
            "matrix": {"data_size": [16, 64]},
            "scenarios": [
                {
                    "id": "mixed",
                    "command": "GET",
                    "clients": 50,
                    "duration": 60,
                    "command_ratio": {"GET": 80, "SET": 20},
                }
            ],
        }
        expanded = expand_matrix(group)
        for s in expanded["scenarios"]:
            assert s["command_ratio"] == {"GET": 80, "SET": 20}

    def test_matrix_expansion_preserves_auto_populate(self):
        group = {
            "group": 1,
            "matrix": {"data_size": [16, 64]},
            "scenarios": [
                {
                    "id": "get",
                    "command": "GET",
                    "clients": 50,
                    "duration": 60,
                    "auto_populate": True,
                    "populate_command": "SET",
                }
            ],
        }
        expanded = expand_matrix(group)
        for s in expanded["scenarios"]:
            assert s["auto_populate"] is True
            assert s["populate_command"] == "SET"
