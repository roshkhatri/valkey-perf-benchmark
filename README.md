# Valkey Performance Benchmark

A comprehensive benchmarking tool for [Valkey](https://github.com/valkey-io/valkey), an in-memory data structure store. This tool allows you to measure performance across different configurations, including TLS and cluster modes.

## Features

- Benchmark Valkey server with various commands (SET, GET, RPUSH, etc.)
- Test with different data sizes and pipeline configurations
- Support for TLS and cluster mode testing [WIP only for non TLS and non cluster mode]
- Automatic server setup and teardown
- Detailed performance metrics collection and reporting
- Compare performance between different Valkey versions/commits

## Prerequisites

- Git
- Python 3.6+
- Linux environment (for taskset CPU pinning)
- Build tools required by Valkey (gcc, make, etc.)

## Project Structure

```
valkey-perf-benchmark/
├── configs/                  # Benchmark configuration files
│   └── benchmark-configs.json
├── results/                  # Benchmark results stored here
├── benchmark.py              # Main entry point
├── valkey_build.py           # Handles building Valkey from source
├── valkey_server.py          # Manages Valkey server instances
├── valkey_benchmark.py       # Runs benchmark tests
├── process_metrics.py        # Processes and formats benchmark results
├── cleanup_server.py         # Utilities for cleaning up server processes
└── logger.py                 # Logging utilities
```

## Usage

### Basic Usage

```bash
# Run both server and client benchmarks with default configuration
python benchmark.py

# Run only the server component
python benchmark.py --mode server

# Run only the client component against a specific server
python benchmark.py --mode client --target_ip 192.168.1.100

# Use a specific configuration file
python benchmark.py --config ./configs/my-custom-config.json

# Benchmark a specific commit
python benchmark.py --commit 1a2b3c4d
```

### PR Comparison Mode

Compare performance between your local PR changes and the unstable branch:

```bash
python benchmark.py --mode pr
```

## Configuration

Create benchmark configurations in JSON format. Example:

```json
[
  {
    "requests": [10000000],
    "keyspacelen": [10000000],
    "data_sizes": [16, 64, 256],
    "pipelines": [1, 10, 100],
    "commands": ["SET", "GET"],
    "cluster_modes": ["yes", "no"],
    "tls_modes": ["yes", "no"],
    "warmup": [10]
  }
]
```

### Configuration Parameters

- `requests`: Number of requests to perform
- `keyspacelen`: Key space size (number of distinct keys)
- `data_sizes`: Size of data in bytes
- `pipelines`: Number of commands to pipeline
- `commands`: Redis commands to benchmark
- `cluster_modes`: Whether to enable cluster mode ("yes" or "no")
- `tls_modes`: Whether to enable TLS ("yes" or "no")
- `warmup`: Warmup time in seconds before benchmarking

## Results

Benchmark results are stored in the `results/` directory, organized by commit ID:

```
results/
└── <commit-id>/
    ├── logs.txt                         # Benchmark logs
    ├── metrics.json                     # Performance metrics in JSON format
    └── valkey_log_cluster_disabled.log  # Valkey server logs
```

## Building Valkey

The tool can automatically build Valkey from source:

```python
from valkey_build import ServerBuilder

# Build Valkey from a specific commit with TLS enabled
builder = ServerBuilder(commit_id="1a2b3c4d", tls_mode="yes")
valkey_path = builder.checkout_and_build()
```

## License

This project is licensed under the same license as Valkey.
