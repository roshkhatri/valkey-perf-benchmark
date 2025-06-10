"""Launch local Valkey servers for benchmark runs."""

import os
import subprocess
import time
from typing import Iterable

from logger import Logger

VALKEY_SERVER = "src/valkey-server"
VALKEY_CLI = "src/valkey-cli"


class ServerLauncher:
    """Manage Valkey server instances."""

    def __init__(self, commit_id: str, valkey_path: str = "../valkey") -> None:
        self.commit_id = commit_id
        self.valkey_path = valkey_path

    def launch_all_servers(self, cluster_mode: str, tls_mode: str) -> None:
        """Start a server and optionally configure cluster mode."""
        self._launch_server(tls_mode=tls_mode, cluster_mode=cluster_mode)
        if cluster_mode == "yes":
            self._setup_cluster(tls_mode=tls_mode)

    def _run(self, command: Iterable[str], check: bool = True) -> None:
        """Execute a command with optional check."""
        try:
            Logger.info(f"Running: {' '.join(command)}")
            subprocess.run(command, check=check)
        except subprocess.CalledProcessError as e:
            Logger.error(f"Command failed with error: {e}")
        except Exception as e:
            Logger.error(f"An error occurred: {e}")

    def _launch_server(self, tls_mode: str, cluster_mode: str) -> None:
        """Start a Valkey server instance."""
        log_file = f"results/{self.commit_id}/valkey_log_cluster_{'enabled' if (cluster_mode == 'yes') else 'disabled'}.log"

        if tls_mode == "yes":
            cmd = [
                "taskset",
                "-c",
                "0-1",
                f"{self.valkey_path}/{VALKEY_SERVER}",
                "--tls-port",
                "6379",
                "--port",
                "0",
                "--tls-cert-file",
                "./tests/tls/valkey.crt",
                "--tls-key-file",
                "./tests/tls/valkey.key",
                "--tls-ca-cert-file",
                "./tests/tls/ca.crt",
                "--daemonize",
                "yes",
                "--maxmemory-policy",
                "allkeys-lru",
                "--appendonly",
                "no",
                "--cluster-enabled",
                cluster_mode,
                "--logfile",
                log_file,
                "--save",
                "''",
            ]
        else:
            cmd = [
                "taskset",
                "-c",
                "0-1",
                f"{self.valkey_path}/{VALKEY_SERVER}",
                "--port",
                "6379",
                "--daemonize",
                "yes",
                "--maxmemory-policy",
                "allkeys-lru",
                "--appendonly",
                "no",
                "--cluster-enabled",
                cluster_mode,
                "--logfile",
                log_file,
                "--save",
                "''",
            ]

        self._run(cmd)
        Logger.info(
            f"Started Valkey Server with TLS {'enabled' if (tls_mode == 'yes') else 'disabled'} and Cluster mode {'enabled' if (cluster_mode == 'yes') else 'disabled'} at port 6379"
        )
        time.sleep(3)

    def _setup_cluster(self, tls_mode: str) -> None:
        """Configure a single instance cluster."""
        Logger.info("Setting up cluster configuration...")
        time.sleep(2)

        base_cmd = [VALKEY_CLI]
        if tls_mode == "yes":
            base_cmd += [
                "--tls",
                "--cert",
                "./tests/tls/valkey.crt",
                "--key",
                "./tests/tls/valkey.key",
                "--cacert",
                "./tests/tls/ca.crt",
            ]

        reset_cmd = base_cmd + ["CLUSTER", "RESET", "HARD"]
        add_slots_cmd = base_cmd + ["CLUSTER", "ADDSLOTSRANGE", "0", "16383"]

        self._run(reset_cmd)
        time.sleep(2)
        self._run(add_slots_cmd)
        time.sleep(2)

