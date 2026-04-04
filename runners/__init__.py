"""Benchmark tool abstraction layer.

Provides a pluggable interface for benchmark tools with automatic
registration and factory-based instantiation.

Usage::

    from runners import create_tool, RunContext

    tool = create_tool("valkey-benchmark", benchmark_path="src/valkey-benchmark")
    ctx = RunContext(target_ip="127.0.0.1", port=6379, ...)
    result = tool.run(scenario, ctx)
"""

from runners.base import (
    BenchmarkResult,
    BenchmarkTool,
    RunContext,
    available_tools,
    create_tool,
    register_tool,
)

# Import tool modules to trigger registration
import runners.valkey_benchmark_tool  # noqa: F401
import runners.cachecannon_tool  # noqa: F401

__all__ = [
    "BenchmarkResult",
    "BenchmarkTool",
    "RunContext",
    "available_tools",
    "create_tool",
    "register_tool",
]
