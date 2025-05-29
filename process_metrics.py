from datetime import datetime
from logger import Logger


class MetricParser:
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
            "timestamp": datetime.utcnow().isoformat(),
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
