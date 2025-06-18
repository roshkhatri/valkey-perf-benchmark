#!/usr/bin/env python3
import json
import statistics
import sys


if len(sys.argv) < 3:
    print(
        "Usage: compare_benchmark_results.py BASELINE NEW [OUT_FILE]", file=sys.stderr
    )
    sys.exit(1)

baseline_file = sys.argv[1]
new_file = sys.argv[2]
out_file = sys.argv[3] if len(sys.argv) > 3 else None


def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _mean(values):
    values = [v for v in values if v is not None]
    return statistics.mean(values) if values else 0.0


def group_by_command(data):
    """Group benchmark results by command."""
    result = {}
    for item in data:
        command = item.get("command", "UNKNOWN")
        if command not in result:
            result[command] = []
        result[command].append(item)
    return result


def summarize(data_item):
    """Summarize a single benchmark result item."""
    return {
        "rps": data_item.get("rps", 0.0),
        "latency_avg_ms": data_item.get(
            "avg_latency_ms", data_item.get("latency_avg_ms", 0.0)
        ),
        "latency_p50_ms": data_item.get(
            "p50_latency_ms", data_item.get("latency_p50_ms", 0.0)
        ),
        "latency_p95_ms": data_item.get(
            "p95_latency_ms", data_item.get("latency_p95_ms", 0.0)
        ),
        "latency_p99_ms": data_item.get(
            "p99_latency_ms", data_item.get("latency_p99_ms", 0.0)
        ),
    }


def pct_change(new_v, old_v):
    return ((new_v - old_v) / old_v * 100.0) if old_v else 0.0


# Load data
baseline_data = load(baseline_file)
new_data = load(new_file)

# Group by command
baseline_by_command = group_by_command(baseline_data)
new_by_command = group_by_command(new_data)

# Get all unique commands
all_commands = sorted(
    set(list(baseline_by_command.keys()) + list(new_by_command.keys()))
)

metrics = [
    "rps",
    "latency_avg_ms",
    "latency_p50_ms",
    "latency_p95_ms",
    "latency_p99_ms",
]

# Generate comparison table
lines = ["# Benchmark Comparison by Command\n"]

for command in all_commands:
    lines.append(f"## {command}\n")
    lines.append("| Metric | Baseline | PR | Diff | % Change |")
    lines.append("| --- | --- | --- | --- | --- |")

    # Get data for this command
    baseline_items = baseline_by_command.get(command, [])
    new_items = new_by_command.get(command, [])

    # If we have multiple items for the same command, use the first one
    baseline_item = baseline_items[0] if baseline_items else {}
    new_item = new_items[0] if new_items else {}

    # Summarize
    baseline_summary = summarize(baseline_item)
    new_summary = summarize(new_item)

    # Generate metrics rows
    for metric in metrics:
        baseline_value = baseline_summary.get(metric, 0.0)
        new_value = new_summary.get(metric, 0.0)
        diff = new_value - baseline_value
        change = pct_change(new_value, baseline_value)

        # Format the row with appropriate precision
        lines.append(
            f"| {metric} | {baseline_value:.2f} | {new_value:.2f} | {diff:.2f} | {change:+.2f}% |"
        )

    lines.append("")  # Add empty line between command sections

# Join all lines
table = "\n".join(lines)

# Output
if out_file:
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(table)
print(table)
