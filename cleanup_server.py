import subprocess
import os
import signal

from logger import Logger

class ServerCleaner:
    @staticmethod
    def kill_valkey_servers():
        Logger.info("Killing any running valkey-server processes...")
        subprocess.run(["pkill", "-9", "valkey-server"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    @staticmethod
    def flush_all(target_ip="127.0.0.1", tls=False):
        cli = ["src/valkey-cli", "-h", target_ip, "-p", "6379"]
        if tls:
            cli += [
                "--tls",
                "--cert", "./tests/tls/valkey.crt",
                "--key", "./tests/tls/valkey.key",
                "--cacert", "./tests/tls/ca.crt"
            ]
        cmd = cli + ["FLUSHALL"]
        Logger.info(f"Running: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)