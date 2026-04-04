"""Cachecannon benchmark runner adapter.

Generates TOML configs from our JSON benchmark config, runs cachecannon,
and parses its JSON output into the standard metrics format used by
MetricsProcessor. Only supports GET and SET commands.
"""

import json
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

SUPPORTED_COMMANDS = {"GET", "SET"}


def is_cachecannon_available(path: str = "cachecannon") -> bool:
    """Check if cachecannon binary is available."""
    return shutil.which(path) is not None


def supports_command(command: str) -> bool:
    """Return True if cachecannon supports this command."""
    return command.upper() in SUPPORTED_COMMANDS


def _build_toml_config(
    *,
    target_ip: str,
    port: int,
    duration: Optional[int],
    requests: Optional[int],
    warmup: int,
    data_size: int,
    keyspacelen: int,
    pipeline: int,
    clients: int,
    command: str,
    cluster_mode: bool,
    tls_mode: bool,
    threads: Optional[int] = None,
    cpu_list: Optional[str] = None,
    cachecannon_config: Optional[Dict] = None,
    command_ratio: Optional[Dict] = None,
) -> str:
    """Generate a cachecannon TOML config string from benchmark parameters."""
    cfg = cachecannon_config or {}

    if command_ratio:
        for key in command_ratio:
            if key.upper() not in SUPPORTED_COMMANDS:
                raise ValueError(f"Unsupported command in command_ratio: {key}")
        total = sum(command_ratio.values())
        if total != 100:
            raise ValueError(f"command_ratio must sum to 100, got {total}")
        get_pct = command_ratio.get("GET", command_ratio.get("get", 0))
        set_pct = command_ratio.get("SET", command_ratio.get("set", 0))
    else:
        cmd_upper = command.upper()
        if cmd_upper == "SET":
            get_pct, set_pct = 0, 100
        elif cmd_upper == "GET":
            get_pct, set_pct = 100, 0
        else:
            raise ValueError(f"Unsupported command for cachecannon: {command}")

    # Duration: cachecannon requires a duration string
    dur = duration if duration else 60
    warmup_val = warmup if warmup else 0

    eff_threads = cfg.get("threads", threads)
    eff_cpu_list = cfg.get("cpu_list", cpu_list)

    lines = [
        "[general]",
        f'duration = "{dur}s"',
        f'warmup = "{warmup_val}s"',
    ]
    if eff_threads:
        lines.append(f"threads = {eff_threads}")
    if eff_cpu_list:
        lines.append(f'cpu_list = "{eff_cpu_list}"')

    lines += [
        "",
        "[target]",
        f'endpoints = ["{target_ip}:{port}"]',
        'protocol = "resp"',
    ]
    if cluster_mode:
        lines.append("cluster = true")
    if tls_mode:
        lines.append("tls = true")

    connect_timeout = cfg.get("connect_timeout", "5s")
    request_timeout = cfg.get("request_timeout", "1s")

    lines += [
        "",
        "[connection]",
        f"connections = {clients}",
        f"pipeline_depth = {pipeline}",
        f'connect_timeout = "{connect_timeout}"',
        f'request_timeout = "{request_timeout}"',
    ]

    # Prefill for GET-only workloads so the keyspace is populated
    prefill = (
        "true"
        if (command_ratio and get_pct > 0)
        or (not command_ratio and command.upper() == "GET")
        else "false"
    )
    lines += [
        "",
        "[workload]",
        f"prefill = {prefill}",
    ]

    lines += [
        "",
        "[workload.keyspace]",
        "length = 16",
        f"count = {keyspacelen}",
        'distribution = "uniform"',
    ]

    lines += [
        "",
        "[workload.commands]",
        f"get = {get_pct}",
        f"set = {set_pct}",
    ]

    lines += [
        "",
        "[workload.values]",
        f"length = {data_size}",
    ]

    lines += [
        "",
        "[timestamps]",
        "enabled = true",
        'mode = "userspace"',
    ]

    lines += [
        "",
        "[admin]",
        'format = "json"',
    ]

    return "\n".join(lines) + "\n"


def _parse_json_output(stdout: str, command: str) -> Optional[Dict]:
    """Parse cachecannon JSON (NDJSON) output into our metrics dict format.

    Cachecannon emits one JSON object per line with a ``type`` field.
    We extract the final ``result`` line.
    """
    result_line = None
    for line in stdout.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if obj.get("type") == "result":
                result_line = obj
        except json.JSONDecodeError:
            continue

    if not result_line:
        logging.warning("No 'result' line found in cachecannon JSON output")
        return None

    def _ns_to_ms(ns_val):
        """Convert nanoseconds to milliseconds."""
        try:
            return round(float(ns_val) / 1_000_000, 3)
        except (TypeError, ValueError):
            return 0.0

    # Map cachecannon result fields to our standard metrics dict.
    # The exact field names depend on cachecannon's JSON schema;
    # we handle both flat and nested latency structures.
    rps = float(result_line.get("throughput", 0))

    # Latency may be nested under a per-command key or at top level
    latency = result_line.get("latency", {})
    if not latency:
        # Try command-specific latency
        cmd_key = command.lower() + "_latency"
        latency = result_line.get(cmd_key, {})

    return {
        "rps": str(rps),
        "avg_latency_ms": str(_ns_to_ms(latency.get("avg", 0))),
        "min_latency_ms": str(_ns_to_ms(latency.get("min", 0))),
        "p50_latency_ms": str(_ns_to_ms(latency.get("p50", 0))),
        "p95_latency_ms": str(_ns_to_ms(latency.get("p95", 0))),
        "p99_latency_ms": str(_ns_to_ms(latency.get("p99", 0))),
        "max_latency_ms": str(_ns_to_ms(latency.get("max", 0))),
    }


def run_cachecannon(
    *,
    target_ip: str = "127.0.0.1",
    port: int = 6379,
    duration: Optional[int] = None,
    requests: Optional[int] = None,
    warmup: int = 0,
    data_size: int = 64,
    keyspacelen: int = 1000000,
    pipeline: int = 32,
    clients: int = 16,
    command: str = "GET",
    cluster_mode: bool = False,
    tls_mode: bool = False,
    threads: Optional[int] = None,
    cpu_list: Optional[str] = None,
    cachecannon_path: str = "cachecannon",
    timeout: Optional[int] = None,
    cachecannon_config: Optional[Dict] = None,
    command_ratio: Optional[Dict] = None,
) -> Optional[Dict]:
    """Run a single cachecannon benchmark and return parsed metrics dict.

    Returns a dict compatible with ``MetricsProcessor.create_metrics``
    (string values matching CSV-row convention), or ``None`` on failure.
    """
    if not supports_command(command):
        raise ValueError(f"cachecannon only supports GET/SET, got: {command}")

    toml_content = _build_toml_config(
        target_ip=target_ip,
        port=port,
        duration=duration,
        requests=requests,
        warmup=warmup,
        data_size=data_size,
        keyspacelen=keyspacelen,
        pipeline=pipeline,
        clients=clients,
        command=command,
        cluster_mode=cluster_mode,
        tls_mode=tls_mode,
        threads=threads,
        cpu_list=cpu_list,
        cachecannon_config=cachecannon_config,
        command_ratio=command_ratio,
    )

    # Write TOML to a temp file
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".toml", prefix="cachecannon_", delete=False
    ) as f:
        f.write(toml_content)
        toml_path = f.name

    try:
        logging.info(f"Running cachecannon: {cachecannon_path} {toml_path}")
        logging.debug(f"TOML config:\n{toml_content}")

        result = subprocess.run(
            [cachecannon_path, toml_path],
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if result.returncode != 0:
            logging.error(
                f"cachecannon failed (exit {result.returncode}): {result.stderr}"
            )
            return None

        logging.info(f"cachecannon output:\n{result.stdout}")
        return _parse_json_output(result.stdout, command)

    except subprocess.TimeoutExpired:
        logging.error(f"cachecannon timed out after {timeout}s")
        return None
    except FileNotFoundError:
        logging.error(f"cachecannon binary not found at: {cachecannon_path}")
        return None
    finally:
        Path(toml_path).unlink(missing_ok=True)
