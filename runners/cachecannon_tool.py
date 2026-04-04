"""CachecannonTool — wraps the cachecannon benchmark runner.

Delegates to ``cachecannon_runner.run_cachecannon`` and maps its output
into a BenchmarkResult, including extended tail-latency percentiles when
the runner provides them.
"""

import logging
from typing import Optional

from runners.base import BenchmarkResult, BenchmarkTool, RunContext, register_tool
from cachecannon_runner import run_cachecannon, supports_command as _cc_supports


@register_tool("cachecannon")
class CachecannonTool(BenchmarkTool):
    """Benchmark tool backed by cachecannon."""

    def __init__(self, binary_path: str = "cachecannon") -> None:
        self._binary_path = binary_path

    @property
    def name(self) -> str:
        return "cachecannon"

    def supports_command(self, command: str) -> bool:
        """True for GET and SET only."""
        return _cc_supports(command)

    def supports_command_ratio(self) -> bool:
        return True

    def run(
        self, scenario: dict, context: RunContext
    ) -> Optional[BenchmarkResult]:
        """Execute cachecannon and return parsed result or None."""
        row = run_cachecannon(
            target_ip=context.target_ip,
            port=context.port,
            duration=scenario.get("duration"),
            requests=scenario.get("requests"),
            warmup=scenario.get("warmup", 0),
            data_size=scenario.get("data_size", 64),
            keyspacelen=scenario.get("keyspacelen", 1000000),
            pipeline=scenario.get("pipeline", 32),
            clients=scenario.get("clients", 16),
            command=scenario.get("command", "GET"),
            cluster_mode=context.cluster_mode,
            tls_mode=context.tls_mode,
            threads=scenario.get("threads"),
            cpu_list=context.cores,
            cachecannon_path=self._binary_path,
            **(context.tool_config or {}),
        )
        if row is None:
            return None

        def _f(key: str) -> float:
            try:
                return float(row.get(key, 0))
            except (ValueError, TypeError):
                return 0.0

        return BenchmarkResult(
            rps=_f("rps"),
            avg_latency_ms=_f("avg_latency_ms"),
            min_latency_ms=_f("min_latency_ms"),
            p50_latency_ms=_f("p50_latency_ms"),
            p95_latency_ms=_f("p95_latency_ms"),
            p99_latency_ms=_f("p99_latency_ms"),
            max_latency_ms=_f("max_latency_ms"),
            p90_latency_ms=_f("p90_latency_ms"),
            p999_latency_ms=_f("p999_latency_ms"),
            p9999_latency_ms=_f("p9999_latency_ms"),
        )
