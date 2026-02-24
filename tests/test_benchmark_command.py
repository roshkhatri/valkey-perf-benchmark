"""Unit tests for ClientRunner._build_benchmark_command."""

import pytest


class TestBuildBenchmarkCommandSimpleFormat:
    """Test simple format (no scenario) produces correct flags."""

    def test_simple_format_contains_all_flags(self, minimal_client_runner):
        """Simple format command includes all expected positional flags."""
        cmd = minimal_client_runner._build_benchmark_command(
            tls=False,
            requests=1000,
            keyspacelen=5000,
            data_size=64,
            pipeline=1,
            clients=50,
            command="GET",
            seed_val=42,
        )

        assert cmd[0] == "src/valkey-benchmark"
        assert "-h" in cmd
        assert cmd[cmd.index("-h") + 1] == "127.0.0.1"
        assert "-p" in cmd
        assert cmd[cmd.index("-p") + 1] == "6379"
        assert "-n" in cmd
        assert cmd[cmd.index("-n") + 1] == "1000"
        assert "-r" in cmd
        assert cmd[cmd.index("-r") + 1] == "5000"
        assert "-d" in cmd
        assert cmd[cmd.index("-d") + 1] == "64"
        assert "-P" in cmd
        assert cmd[cmd.index("-P") + 1] == "1"
        assert "-c" in cmd
        assert cmd[cmd.index("-c") + 1] == "50"
        assert "-t" in cmd
        assert cmd[cmd.index("-t") + 1] == "GET"
        assert "--seed" in cmd
        assert cmd[cmd.index("--seed") + 1] == "42"
        assert "--csv" in cmd

    def test_simple_format_no_taskset_by_default(self, minimal_client_runner):
        """Without CPU pinning, taskset should not appear."""
        cmd = minimal_client_runner._build_benchmark_command(
            requests=100,
            keyspacelen=100,
            data_size=32,
            pipeline=1,
            clients=10,
            command="SET",
            seed_val=1,
        )
        assert "taskset" not in cmd


class TestBuildBenchmarkCommandTLS:
    """Test TLS mode includes TLS flags."""

    def test_tls_flags_present(self, minimal_client_runner):
        """When tls=True, TLS cert/key/cacert flags are included."""
        cmd = minimal_client_runner._build_benchmark_command(
            tls=True,
            requests=100,
            keyspacelen=100,
            data_size=32,
            pipeline=1,
            clients=10,
            command="GET",
            seed_val=1,
        )

        assert "--tls" in cmd
        assert "--cert" in cmd
        assert cmd[cmd.index("--cert") + 1] == "./tests/tls/valkey.crt"
        assert "--key" in cmd
        assert cmd[cmd.index("--key") + 1] == "./tests/tls/valkey.key"
        assert "--cacert" in cmd
        assert cmd[cmd.index("--cacert") + 1] == "./tests/tls/ca.crt"

    def test_no_tls_flags_when_disabled(self, minimal_client_runner):
        """When tls=False, no TLS flags appear."""
        cmd = minimal_client_runner._build_benchmark_command(
            tls=False,
            requests=100,
            keyspacelen=100,
            data_size=32,
            pipeline=1,
            clients=10,
            command="GET",
            seed_val=1,
        )
        assert "--tls" not in cmd
        assert "--cert" not in cmd


class TestBuildBenchmarkCommandCPUPinning:
    """Test CPU pinning prepends taskset."""

    def test_cpu_range_param_prepends_taskset(self, minimal_client_runner):
        """Passing cpu_range prepends taskset -c <range> to the command."""
        cmd = minimal_client_runner._build_benchmark_command(
            requests=100,
            keyspacelen=100,
            data_size=32,
            pipeline=1,
            clients=10,
            command="GET",
            seed_val=1,
            cpu_range="0-3",
        )

        assert cmd[0] == "taskset"
        assert cmd[1] == "-c"
        assert cmd[2] == "0-3"
        assert cmd[3] == "src/valkey-benchmark"

    def test_self_cores_prepends_taskset(self, minimal_client_runner):
        """When self.cores is set, taskset is prepended."""
        minimal_client_runner.cores = "4-7"
        cmd = minimal_client_runner._build_benchmark_command(
            requests=100,
            keyspacelen=100,
            data_size=32,
            pipeline=1,
            clients=10,
            command="SET",
            seed_val=1,
        )

        assert cmd[0] == "taskset"
        assert cmd[1] == "-c"
        assert cmd[2] == "4-7"


class TestBuildBenchmarkCommandDuration:
    """Test duration mode uses --duration instead of -n."""

    def test_duration_flag_replaces_requests(self, minimal_client_runner):
        """When duration is provided, --duration is used instead of -n."""
        cmd = minimal_client_runner._build_benchmark_command(
            requests=None,
            keyspacelen=100,
            data_size=32,
            pipeline=1,
            clients=10,
            command="GET",
            seed_val=1,
            duration=30,
        )

        assert "--duration" in cmd
        assert cmd[cmd.index("--duration") + 1] == "30"
        assert "-n" not in cmd

    def test_no_duration_uses_requests(self, minimal_client_runner):
        """Without duration, -n flag is used with requests count."""
        cmd = minimal_client_runner._build_benchmark_command(
            requests=5000,
            keyspacelen=100,
            data_size=32,
            pipeline=1,
            clients=10,
            command="GET",
            seed_val=1,
        )

        assert "-n" in cmd
        assert cmd[cmd.index("-n") + 1] == "5000"
        assert "--duration" not in cmd
