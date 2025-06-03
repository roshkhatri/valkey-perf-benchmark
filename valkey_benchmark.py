import subprocess
import time
import json
import os
from itertools import product
from process_metrics import MetricsProcessor
from logger import Logger

VALKEY_CLI = "src/valkey-cli"
VALKEY_BENCHMARK = "src/valkey-benchmark"

class ClientRunner:
    def __init__(self, commit_id, config, cluster_mode, tls_mode, target_ip, results_dir, valkey_path):
        self.commit_id = commit_id
        self.config = config
        self.cluster_mode = True if cluster_mode == "yes" else False
        self.tls_mode = True if tls_mode == "yes" else False
        self.target_ip = target_ip
        self.results_dir = results_dir
        self.valkey_cli = f"{valkey_path}/{VALKEY_CLI}"
        self.valkey_benchmark = f"{valkey_path}/{VALKEY_BENCHMARK}"
        
    def ping_server(self):
        try:
            cmd = [self.valkey_cli,
                   "-h", self.target_ip,
                   "-p", "6379",
                   "ping"]
            Logger.info(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            if "PONG" in result.stdout:
                Logger.info("Server is running")
            else:
                Logger.error("Server did not respond with PONG")
                exit(1)
        except subprocess.CalledProcessError as e:
            Logger.error(f"Command failed with error: {e}")
        except Exception as e:
            Logger.error(f"An error occurred: {e}")


    def run_benchmark_config(self):
        combinations = self._generate_combinations()
        metrics_processor = MetricsProcessor(self.commit_id, self.cluster_mode, self.tls_mode)
        metric_json = []

        Logger.info(f"=== Starting benchmark: TLS={self.tls_mode}, Cluster={self.cluster_mode} ===")
        for (requests, keyspacelen, data_size, pipeline, command, warmup) in combinations:
            Logger.info(f"--> Running {command} with data size {data_size}, pipeline {pipeline}")
            Logger.info(f"requests: {requests}, keyspacelen: {keyspacelen}, data_size: {data_size}, pipeline: {pipeline}, warmup: {warmup}")
            
            # Optionally flush keyspace if needed
            if command in ["SET", "RPUSH", "LPUSH", "SADD"]:
                Logger.info("Flushing keyspace before benchmark...")
                flush_cmd = self._build_cli_command(self.tls_mode) + ["FLUSHALL", "SYNC"]
                self._run(flush_cmd)
                time.sleep(2)

            # Warmup phase
            if warmup:
                bench_cmd = self._build_benchmark_command(self.tls_mode, requests, keyspacelen, data_size, pipeline, command)
                try:
                    Logger.info(f"Starting warmup for {warmup} seconds...")
                    proc = subprocess.Popen(bench_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    time.sleep(warmup)
                    proc.terminate()
                    proc.wait(timeout=5)  # Wait for process to terminate
                    Logger.info(f"Warmup completed after {warmup} seconds")
                except Exception as e:
                    Logger.error(f"Warmup failed: {e}")
                    
            # Run benchmark
            Logger.info("Starting benchmark...")
            bench_cmd = self._build_benchmark_command(self.tls_mode, requests, keyspacelen, data_size, pipeline, command)
            try:
                proc = subprocess.run(bench_cmd, capture_output=True, text=True, check=True)
                # Log the benchmark output
                Logger.info(f"Benchmark output:\n{proc.stdout}")
                if proc.stderr:
                    Logger.warning(f"Benchmark stderr:\n{proc.stderr}")

                metrics = metrics_processor.parse_csv_output(proc.stdout, command, data_size, pipeline)
                Logger.info(f"Benchmark completed: {metrics}")
                if metrics:
                    metric_json.append(metrics)
            except subprocess.CalledProcessError as e:
                Logger.error(f"Benchmark failed: {e}")
                if e.stdout:
                    Logger.info(f"Benchmark stdout:\n{e.stdout}")
                if e.stderr:
                    Logger.error(f"Benchmark stderr:\n{e.stderr}")

        # in case no benchmarks ran successfully)
        if not metric_json:
            Logger.warning("No metrics collected, skipping metrics write")
            return
            
        metrics_processor.write_metrics(self.results_dir, metric_json)

    def _generate_combinations(self):
        return list(product(
            self.config["requests"],
            self.config["keyspacelen"],
            self.config["data_sizes"],
            self.config["pipelines"],
            self.config["commands"],
            self.config["warmup"]
        ))

    def _build_cli_command(self, tls):
        cmd = [self.valkey_cli, "-h", self.target_ip, "-p", "6379"]
        if tls:
            cmd += ["--tls", "--cert", "./tests/tls/valkey.crt",
                    "--key", "./tests/tls/valkey.key",
                    "--cacert", "./tests/tls/ca.crt"]
        return cmd

    def _build_benchmark_command(self, tls, requests, keyspacelen, data_size, pipeline, command):
        cmd = [self.valkey_benchmark, "-h", self.target_ip, "-p", "6379",
               "-n", str(requests), "-r", str(keyspacelen), "-d", str(data_size),
               "-P", str(pipeline), "-t", command, "--csv"]
        if tls:
            cmd += ["--tls", "--cert", "./tests/tls/valkey.crt",
                    "--key", "./tests/tls/valkey.key",
                    "--cacert", "./tests/tls/ca.crt"]
        return cmd

    def _run(self, cmd):
        try:
            Logger.info(f"Running: {' '.join(cmd)}")
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            Logger.error(f"Command failed with error: {e}")
        except Exception as e:
            Logger.error(f"An error occurred: {e}")
