import argparse
import json
from pathlib import Path
from itertools import product

from logger import Logger
from valkey_benchmark import ClientRunner
from valkey_build import ServerBuilder
from valkey_server import ServerLauncher
from cleanup_server import ServerCleaner

RESULTS_DIR = Path("results")
REQUIRED_KEYS = ["requests", "keyspacelen", "data_sizes", "pipelines", "commands", "cluster_modes", "tls_modes", "warmup"]


def parse_args():
    parser = argparse.ArgumentParser(description="Valkey Benchmarking Tool")
    parser.add_argument("--mode", choices=["server", "client", "both", "pr"], default="both")
    parser.add_argument("--commit", default="unstable")
    parser.add_argument("--target_ip", default="127.0.0.1", help="Only needed for client mode")
    parser.add_argument("--config", default="./configs/benchmark-configs.json")
    return parser.parse_args()


def validate_config(config):
    for key in REQUIRED_KEYS:
        if key not in config:
            raise ValueError(f"Missing required config key: {key}")


def load_config(config_path):
    with open(config_path, "r") as f:
        configs = json.load(f)
        for config in configs:
            validate_config(config)
        
        return configs


def ensure_results_dir(commit_id):
    commit_results_path = RESULTS_DIR / commit_id
    commit_results_path.mkdir(parents=True, exist_ok=True)
    return commit_results_path


def run_pipeline(commit_id, config, mode, target_ip):
    results_dir = ensure_results_dir(commit_id)
    Logger.init_logging(results_dir / "logs.txt")

    tls_modes=config.get("tls_modes")
    for tls_mode in tls_modes: 
        builder = ServerBuilder(commit_id=commit_id, tls_mode=tls_mode)
        if builder.check_if_built():
            valkey_path = builder.get_valkey_path()
        else:
            valkey_path = builder.checkout_and_build()

        cluster_modes = config.get("cluster_modes")
        for cluster_mode in cluster_modes:
            Logger.info(f"Running benchmark with Cluster Mode {'enabled' if (cluster_mode == 'yes') else 'disabled'} and TLS {'enabled' if (tls_mode == 'yes') else 'disabled'}")

            if mode in ("server", "both", "pr"):
                launcher = ServerLauncher(commit_id=commit_id, valkey_path=valkey_path)
                launcher.launch_all_servers(
                    cluster_mode=cluster_mode,
                    tls_mode = tls_mode
                )

            if mode in ("client", "both", "pr"):
                runner = ClientRunner(
                    commit_id=commit_id,
                    config=config,
                    cluster_mode=cluster_mode,
                    tls_mode = tls_mode,
                    target_ip=target_ip,
                    results_dir=results_dir,
                    valkey_path=valkey_path
                )
                runner.ping_server()
                runner.run_all()
            
            ServerCleaner.kill_valkey_servers()


def main():
    args = parse_args()

    for config in load_config(args.config):
        Logger.info(f"Running benchmark with config: {config}")
        commit_ids = [args.commit] if args.mode != "pr" else ["pr", "unstable"]
        for commit_id in commit_ids:
            run_pipeline(
                commit_id=commit_id,
                config=config,
                mode=args.mode,
                target_ip=args.target_ip,
            )

if __name__ == "__main__":
    main()