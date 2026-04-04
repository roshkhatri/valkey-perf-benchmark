# Benchmark Configuration Schema

This document defines the two standard configuration formats used by the benchmarking framework. All configs are JSON arrays where each element is an independent benchmark configuration.

## Format 1: Core Benchmark Config (command-based)

Used for standard Valkey command benchmarking (SET, GET, RPUSH, etc.).

```json
[
  {
    "requests": [10000000],
    "duration": 120,
    "keyspacelen": [10000000],
    "data_sizes": [16, 64, 256],
    "pipelines": [1, 10, 100],
    "clients": [50],
    "commands": ["SET", "GET", "RPUSH"],
    "cluster_mode": false,
    "tls_mode": false,
    "warmup": 10,
    "io-threads": [1, 4, 8],
    "benchmark-threads": 2,
    "server_cpu_range": "0-1",
    "client_cpu_range": "2-3",
    "port": 6379
  }
]
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `keyspacelen` | `int[]` | Number of distinct keys |
| `data_sizes` | `int[]` | Payload sizes in bytes |
| `pipelines` | `int[]` | Pipeline depths |
| `clients` | `int[]` | Concurrent client connections |
| `commands` | `string[]` | Valkey commands to benchmark |
| `cluster_mode` | `bool \| string` | Enable cluster mode (`true`/`false`/`"yes"`/`"no"`) |
| `tls_mode` | `bool \| string` | Enable TLS (`true`/`false`/`"yes"`/`"no"`) |
| `warmup` | `int` | Warmup seconds before measurement (≥ 0) |

One of `requests` or `duration` is required (not both):

| Field | Type | Description |
|-------|------|-------------|
| `requests` | `int[]` | Total requests per benchmark run |
| `duration` | `int` | Test duration in seconds |

### Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `io-threads` | `int \| int[]` | `null` | Server I/O threads |
| `benchmark-threads` | `int` | `null` | valkey-benchmark thread count |
| `server_cpu_range` | `string` | `null` | CPU pinning for server (e.g., `"0-3"`, `"0,2,4"`) |
| `client_cpu_range` | `string` | `null` | CPU pinning for client |
| `port` | `int` | `6379` | Server port |
| `seed` | `bool` | `true` | Enable random seed (`false` to disable) |
| `module_startup_args` | `string` | `null` | Extra args for module startup |

### Supported Commands

**Write:** `SET`, `MSET`, `INCR`, `LPUSH`, `RPUSH`, `LPOP`, `RPOP`, `SADD`, `HSET`, `ZADD`, `XADD`, `SPOP`, `ZPOPMIN`

**Read:** `GET`, `MGET`, `LRANGE`, `SISMEMBER`, `ZSCORE`, `ZRANGE`

### Benchmark Tool Selection

When using `--benchmark-tool cachecannon`, only `GET` and `SET` commands are routed to cachecannon. All other commands automatically use valkey-benchmark regardless of the flag.

---

## Format 2: Module Test Config (test_groups-based)

Used for module testing (FTS, vector search, etc.) with structured scenarios.

```json
[
  {
    "test_groups": [
      {
        "group": 1,
        "description": "Basic search test",
        "scenarios": [
          {
            "id": "a",
            "type": "write",
            "cluster_execution": "single",
            "setup_commands": ["FT.CREATE idx ON HASH PREFIX 1 doc: SCHEMA title TEXT"],
            "flush_before": true,
            "dataset": "datasets/search_terms.csv",
            "maxdocs": 50000,
            "clients": 1000,
            "sequential": true,
            "command": "HSET doc:{tag}:__rand_int__ title \"__field:term__\""
          },
          {
            "id": "b",
            "type": "read",
            "cluster_execution": "parallel",
            "dataset": "datasets/search_terms.csv",
            "clients": 1000,
            "duration": 60,
            "warmup": 20,
            "command": "FT.SEARCH idx \"__field:term__\""
          }
        ]
      }
    ],
    "cluster_mode": false,
    "tls_mode": false,
    "port": 6379,
    "io-threads": 2,
    "modules": [
      {
        "path": "../valkey-search/.build-release/libsearch.so",
        "startup_args": ["--use-coordinator"]
      }
    ]
  }
]
```

### Top-Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `test_groups` | `object[]` | Yes | Array of test group objects |
| `cluster_mode` | `bool \| bool[]` | Yes | Single value or array for multi-mode |
| `tls_mode` | `bool` | Yes | Enable TLS |
| `port` | `int` | No | Server port (default: 6379) |
| `io-threads` | `int` | No | Server I/O threads |
| `modules` | `object[]` | No | Modules to load |

### Test Group Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `group` | `int` | No | Group identifier for `--groups` filtering |
| `description` | `string` | No | Human-readable description |
| `scenarios` | `object[]` | Yes | Non-empty array of scenario objects |

### Scenario Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `string` | Yes | Unique scenario identifier (for `--scenarios` filtering) |
| `type` | `string` | Yes | `"write"` or `"read"` |
| `command` | `string` | Yes | Full command string |
| `cluster_execution` | `string` | No | `"single"` (default) or `"parallel"` |
| `setup_commands` | `string[]` | No | Commands to run before scenario |
| `flush_before` | `bool` | No | Flush DB before this scenario |
| `dataset` | `string` | No | Path to dataset file |
| `maxdocs` | `int` | No | Max documents for write scenarios |
| `clients` | `int` | No | Concurrent connections |
| `pipeline` | `int` | No | Pipeline depth (default: 1) |
| `duration` | `int` | No | Duration in seconds |
| `requests` | `int` | No | Total requests |
| `warmup` | `int` | No | Warmup seconds |
| `sequential` | `bool` | No | Use sequential key access |
| `seed` | `bool` | No | Enable random seed |
| `options` | `object` | No | Flag variants (key=flag, value=id suffix) |
| `profiling` | `object` | No | Per-scenario profiling override |

### Cluster Mode Array

When `cluster_mode` is an array, the framework runs all scenarios for each mode:

```json
"cluster_mode": [false, true]
```

Filter with `--cluster-mode-filter false` or `--cluster-mode-filter true`.

### Multi-Node Cluster Fields

| Field | Type | Description |
|-------|------|-------------|
| `cluster_nodes` | `int` | Number of cluster nodes |
| `cluster_ports` | `int[]` | Port for each node |
| `cpu_allocation` | `object` | CPU pinning (see below) |
| `bind_ip` | `string` | Bind address |

### CPU Allocation (new format, recommended)

```json
"cpu_allocation": {
  "cores_per_server": 8,
  "cores_per_client": 8
}
```

Or with explicit ranges:

```json
"cpu_allocation": {
  "cores_per_server": 8,
  "cores_per_client": 8,
  "servers": ["0-7", "8-15"],
  "clients": ["16-23", "24-31"]
}
```

Cannot be combined with `server_cpu_range`/`client_cpu_range`.

---

## Shared Optional Fields

These fields apply to both config formats:

| Field | Type | Description |
|-------|------|-------------|
| `config_sets` | `object[]` | Server CONFIG SET variations to iterate |
| `profiling_sets` | `object[]` | Profiling configurations to iterate |
| `monitoring` | `object` | CPU monitoring settings |
| `dataset_generation` | `object` | Auto-generate datasets |
| `query_generation` | `object` | Auto-generate query files |

---

## Validation Rules

1. Core configs must have either `requests` or `duration`, not both
2. `keyspacelen`, `data_sizes`, `pipelines`, `clients` must be arrays of positive integers
3. `commands` must be a non-empty array of non-empty strings
4. `warmup` must be a non-negative integer
5. `cpu_allocation` and `server_cpu_range`/`client_cpu_range` are mutually exclusive
6. `test_groups` must be a non-empty array with each group containing a non-empty `scenarios` array
7. `port` must be between 1 and 65535
