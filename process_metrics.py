import json
import time
from logger import Logger


class MetricsProcessor:
    def __init__(self, commit_id, cluster_mode, tls_mode):
        self.commit_id = commit_id
        self.cluster_mode = cluster_mode
        self.tls_mode = tls_mode

    def parse_csv_output(self, output, command, data_size, pipeline):
        """
        Parses valkey-benchmark CSV output and returns structured dict.
        Expected format:
        "SET","123456.78","0.12","0.10","0.11","0.15","0.20","0.25"
        """
        lines = output.strip().split("\n")
        if len(lines) < 2:
            Logger.warning("Unexpected CSV format in benchmark output.")
            return None

        labels = lines[0].replace('"', "").split(",")
        values = lines[1].replace('"', "").split(",")

        if len(values) != len(labels):
            Logger.warning("Mismatch between CSV labels and values")
            return None

        data = dict(zip(labels, values))

        return {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "commit": self.commit_id,
            "command": command,
            "data_size": int(data_size),
            "pipeline": int(pipeline),
            "rps": float(data.get("rps", 0)),
            "avg_latency_ms": float(data.get("avg_latency_ms", 0)),
            "min_latency_ms": float(data.get("min_latency_ms", 0)),
            "p50_latency_ms": float(data.get("p50_latency_ms", 0)),
            "p95_latency_ms": float(data.get("p95_latency_ms", 0)),
            "p99_latency_ms": float(data.get("p99_latency_ms", 0)),
            "max_latency_ms": float(data.get("max_latency_ms", 0)),
            "cluster_mode": self.cluster_mode,
            "tls": self.tls_mode
        }

    def write_metrics(self, results_dir, new_metrics):
        """
        Writes metrics to JSON file.
        """
        metrics_file = results_dir / "metrics.json"
        metrics = []

        if metrics_file.exists() and metrics_file.stat().st_size > 0:
            try:
                with metrics_file.open("r", encoding="utf-8") as f:
                    metrics = json.load(f)
            except json.JSONDecodeError:
                Logger.warning(f"Could not decode JSON from {metrics_file}, starting fresh.")

        # Extend metrics with new_metrics as it's a list.
        metrics.extend(new_metrics)

        with metrics_file.open("w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=4)

        Logger.info(f"Metrics written to {metrics_file}")