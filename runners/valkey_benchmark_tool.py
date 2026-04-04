"""ValkeyBenchmarkTool — wraps the valkey-benchmark CLI.

Builds command lines, executes via subprocess, and parses CSV output
into BenchmarkResult instances.
"""

import csv
import logging
import subprocess
from typing import List, Optional

from runners.base import BenchmarkResult, BenchmarkTool, RunContext, register_tool
from valkey_benchmark import READ_COMMANDS, WRITE_COMMANDS

_ALL_COMMANDS = set(READ_COMMANDS + WRITE_COMMANDS)


@register_tool("valkey-benchmark")
class ValkeyBenchmarkTool(BenchmarkTool):
    """Benchmark tool backed by ``valkey-benchmark``."""

    def __init__(
        self,
        benchmark_path: str = "src/valkey-benchmark",
        benchmark_threads: Optional[int] = None,
    ) -> None:
        self._benchmark_path = benchmark_path
        self._benchmark_threads = benchmark_threads

    @property
    def name(self) -> str:
        return "valkey-benchmark"

    def supports_command(self, command: str) -> bool:
        """True for all standard valkey-benchmark commands."""
        return command.upper() in _ALL_COMMANDS

    def supports_command_ratio(self) -> bool:
        return False

    def run(self, scenario: dict, context: RunContext) -> Optional[BenchmarkResult]:
        """Build command, execute, parse CSV, return result or None."""
        cmd = self._build_command(scenario, context)
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                cwd=context.valkey_path,
                timeout=scenario.get("timeout", 300),
            )
        except Exception as exc:
            logging.error("valkey-benchmark failed: %s", exc)
            return None

        return self._parse_csv(proc.stdout)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_command(self, scenario: dict, context: RunContext) -> List[str]:
        """Assemble the valkey-benchmark CLI invocation."""
        cmd: List[str] = []

        # CPU pinning
        if context.cores:
            cmd += ["taskset", "-c", context.cores]

        cmd.append(self._benchmark_path)

        # TLS
        if context.tls_mode:
            cmd += [
                "--tls",
                "--cert",
                "./tests/tls/valkey.crt",
                "--key",
                "./tests/tls/valkey.key",
                "--cacert",
                "./tests/tls/ca.crt",
            ]

        cmd += ["-h", context.target_ip, "-p", str(context.port)]

        # Duration vs requests
        duration = scenario.get("duration")
        requests = scenario.get("requests")
        if duration is not None:
            cmd += ["--duration", str(duration)]
        elif requests is not None:
            cmd += ["-n", str(requests)]

        # Standard params
        for flag, key in (("-d", "data_size"), ("-P", "pipeline"), ("-c", "clients")):
            val = scenario.get(key)
            if val is not None:
                cmd += [flag, str(val)]

        if self._benchmark_threads is not None:
            cmd += ["--threads", str(self._benchmark_threads)]

        # Command: builtin via -t, custom via --
        command = scenario.get("command", "")
        if command.upper() in _ALL_COMMANDS:
            cmd += ["-t", command]
        else:
            cmd += ["--", command]

        cmd.append("--csv")
        return cmd

    @staticmethod
    def _parse_csv(stdout: str) -> Optional[BenchmarkResult]:
        """Parse valkey-benchmark CSV output into a BenchmarkResult."""
        if not stdout:
            return None
        lines = stdout.splitlines()
        # Find CSV header
        start = None
        for i, line in enumerate(lines):
            if line.startswith('"test"') or line.startswith("test,"):
                start = i
                break
        if start is None:
            return None

        reader = csv.DictReader(lines[start:])
        for row in reader:
            try:
                return BenchmarkResult(
                    rps=float(row.get("rps", 0)),
                    avg_latency_ms=float(row.get("avg_latency_ms", 0)),
                    min_latency_ms=float(row.get("min_latency_ms", 0)),
                    p50_latency_ms=float(row.get("p50_latency_ms", 0)),
                    p95_latency_ms=float(row.get("p95_latency_ms", 0)),
                    p99_latency_ms=float(row.get("p99_latency_ms", 0)),
                    max_latency_ms=float(row.get("max_latency_ms", 0)),
                )
            except (ValueError, TypeError) as exc:
                logging.error("CSV parse error: %s", exc)
                return None
        return None
