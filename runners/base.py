"""Benchmark tool abstraction layer.

Defines the pluggable BenchmarkTool interface, RunContext for execution
parameters, BenchmarkResult for standardized output, and a registry
for tool discovery and instantiation.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Dict, List, Optional, Type


@dataclass(frozen=True)
class RunContext:
    """Immutable execution context passed to every benchmark tool run."""

    target_ip: str
    port: int
    cluster_mode: bool
    tls_mode: bool
    valkey_path: Path
    cores: Optional[str] = None
    tool_config: Optional[dict] = None


@dataclass
class BenchmarkResult:
    """Standardized benchmark output with core and extended latency fields.

    Core fields are required by MetricsProcessor. Extended fields default
    to 0.0 and are only populated when the tool provides them.
    """

    # Core fields (required by MetricsProcessor.create_metrics)
    rps: float
    avg_latency_ms: float
    min_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    max_latency_ms: float

    # Extended latency percentiles
    p90_latency_ms: float = 0.0
    p999_latency_ms: float = 0.0
    p9999_latency_ms: float = 0.0
    p1_latency_ms: float = 0.0
    p5_latency_ms: float = 0.0
    p10_latency_ms: float = 0.0

    _CORE_FIELDS = (
        "rps",
        "avg_latency_ms",
        "min_latency_ms",
        "p50_latency_ms",
        "p95_latency_ms",
        "p99_latency_ms",
        "max_latency_ms",
    )

    def to_row_dict(self) -> Dict[str, str]:
        """Return core fields as string dict compatible with MetricsProcessor."""
        return {k: str(getattr(self, k)) for k in self._CORE_FIELDS}

    def extra_latencies(self) -> Dict[str, float]:
        """Return only non-zero extended latency fields."""
        return {
            f.name: getattr(self, f.name)
            for f in fields(self)
            if f.name not in self._CORE_FIELDS
            and not f.name.startswith("_")
            and getattr(self, f.name) != 0.0
        }


class BenchmarkTool(ABC):
    """Abstract base class for benchmark tool implementations."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique tool identifier."""

    @abstractmethod
    def supports_command(self, command: str) -> bool:
        """Return True if this tool can benchmark the given command."""

    @abstractmethod
    def supports_command_ratio(self) -> bool:
        """Return True if this tool supports mixed read/write ratios."""

    @abstractmethod
    def run(self, scenario: dict, context: RunContext) -> Optional[BenchmarkResult]:
        """Execute a benchmark scenario. Return None on failure."""


# --- Registry ---

_TOOL_REGISTRY: Dict[str, Type[BenchmarkTool]] = {}


def register_tool(name: str):
    """Class decorator that registers a BenchmarkTool implementation."""

    def decorator(cls: Type[BenchmarkTool]) -> Type[BenchmarkTool]:
        _TOOL_REGISTRY[name] = cls
        return cls

    return decorator


def create_tool(name: str, **kwargs) -> BenchmarkTool:
    """Instantiate a registered tool by name."""
    if name not in _TOOL_REGISTRY:
        raise ValueError(
            f"Unknown tool '{name}'. Available: {list(_TOOL_REGISTRY.keys())}"
        )
    return _TOOL_REGISTRY[name](**kwargs)


def available_tools() -> List[str]:
    """Return names of all registered tools."""
    return list(_TOOL_REGISTRY.keys())
