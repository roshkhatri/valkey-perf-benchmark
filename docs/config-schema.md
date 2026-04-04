# Benchmark Configuration Schema

Complete reference for the unified `test_groups` configuration format.

All configs are JSON objects (or arrays of objects). Each must contain a `test_groups` array with one or more test group objects.

## Quick Start Examples

### Simple Config

```json
{
  "duration": 120,
  "cluster_mode": false,
  "tls_mode": false,
  "warmup": 10,
  "test_groups": [
    {
      "scenarios": [
        {"id": "set", "type": "write", "command": "SET", "clients": 50, "pipeline": 10, "keyspacelen": 10000000, "data_size": 16},
        {"id": "get", "type": "read", "command": "GET", "clients": 50, "pipeline": 10, "keyspacelen": 10000000, "data_size": 16, "auto_populate": true, "populate_command": "SET"}
      ]
    }
  ]
}
```

### Matrix Config

```json
{
  "duration": 180,
  "cluster_mode": false,
  "tls_mode": false,
  "warmup": 30,
  "io-threads": [1, 9],
  "server_cpu_range": "0-8",
  "client_cpu_range": "96-191",
  "test_groups": [
    {
      "matrix": {
        "data_size": [16, 96, 2048],
        "pipeline": [1, 10],
        "clients": [1600],
        "keyspacelen": [3000000]
      },
      "scenarios": [
        {"id": "set", "type": "write", "command": "SET"},
        {"id": "get", "type": "read", "command": "GET", "auto_populate": true, "populate_command": "SET"}
      ]
    }
  ]
}
```

### Module Test Config

```json
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
          "maxdocs": 1000,
          "clients": 10,
          "sequential": true,
          "command": "HSET doc:{tag}:__rand_int__ title \"__field:term__\""
        },
        {
          "id": "b",
          "type": "read",
          "cluster_execution": "parallel",
          "dataset": "datasets/search_terms.csv",
          "clients": 10,
          "duration": 30,
          "warmup": 5,
          "command": "FT.SEARCH idx \"__field:term__\""
        }
      ]
    }
  ],
  "cluster_mode": false,
  "tls_mode": false,
  "modules": [{"path": "../valkey-search/.build-release/libsearch.so", "startup_args": ["--use-coordinator"]}]
}
```

### Cachecannon with `command_ratio`

```json
{
  "duration": 120,
  "cluster_mode": false,
  "tls_mode": false,
  "warmup": 10,
  "cachecannon": {
    "threads": 4,
    "cpu_list": "8-11"
  },
  "test_groups": [
    {
      "scenarios": [
        {
          "id": "mixed_80_20",
          "type": "read",
          "command": "GET",
          "command_ratio": {"GET": 80, "SET": 20},
          "clients": 50,
          "pipeline": 10,
          "keyspacelen": 10000000,
          "data_size": 64
        }
      ]
    }
  ]
}
```

---

## Top-Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `test_groups` | `object[]` | Yes | Array of test group objects |
| `cluster_mode` | `bool \| bool[]` | Yes | Enable cluster mode; array for multi-mode runs |
| `tls_mode` | `bool` | Yes | Enable TLS |
| `duration` | `int` | No | Default test duration in seconds |
| `requests` | `int[]` | No | Default total requests per run |
| `warmup` | `int` | No | Default warmup seconds (≥ 0) |
| `io-threads` | `int \| int[]` | No | Server I/O threads |
| `benchmark-threads` | `int` | No | valkey-benchmark thread count |
| `server_cpu_range` | `string` | No | CPU pinning for server (e.g., `"0-3"`, `"0,2,4"`) |
| `client_cpu_range` | `string` | No | CPU pinning for client |
| `port` | `int` | No | Server port (default: 6379) |
| `seed` | `bool` | No | Enable random seed (default: true) |
| `module_startup_args` | `string` | No | Extra args for module startup |
| `cachecannon` | `object` | No | Cachecannon tool tuning (see below) |
| `server_startup_config` | `object` | No | Server startup overrides (see below) |
| `modules` | `object[]` | No | Modules to load |
| `config_sets` | `object[]` | No | Server CONFIG SET variations to iterate |
| `profiling_sets` | `object[]` | No | Profiling configurations to iterate |
| `monitoring` | `object` | No | CPU monitoring settings |
| `dataset_generation` | `object` | No | Auto-generate datasets |
| `query_generation` | `object` | No | Auto-generate query files |

One of `requests` or `duration` may be set at top level as a default (not both). Scenario-level values override.

---

## `cachecannon` Section

Tuning parameters passed to cachecannon when `--benchmark-tool cachecannon` is used.

| Field | Type | Description |
|-------|------|-------------|
| `threads` | `int` | Number of cachecannon threads (positive integer) |
| `cpu_list` | `string` | CPU affinity list (e.g., `"8-11"`) |
| `connect_timeout` | `int` | Connection timeout in milliseconds |
| `request_timeout` | `int` | Request timeout in milliseconds |

```json
{
  "cachecannon": {
    "threads": 4,
    "cpu_list": "8-11",
    "connect_timeout": 5000,
    "request_timeout": 10000
  }
}
```

---

## `server_startup_config` Section

Key-value pairs passed as server startup overrides. Both keys and values must be strings.

```json
{
  "server_startup_config": {
    "maxmemory-policy": "allkeys-lru",
    "appendonly": "no",
    "save": ""
  }
}
```

| Constraint | Rule |
|------------|------|
| Type | `dict` of `string` → `string` |
| Keys | Non-empty strings |
| Values | Strings |

---

## Test Group Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `group` | `int` | No | Group identifier for `--groups` filtering |
| `description` | `string` | No | Human-readable description |
| `scenarios` | `object[]` | Yes | Non-empty array of scenario objects |
| `matrix` | `object` | No | Matrix expansion (see below) |

---

## `matrix` Object

Generates Cartesian product of parameter combinations, expanding each scenario into multiple variants.

### Allowed Keys

| Key | ID Suffix | Example |
|-----|-----------|---------|
| `data_size` | `d` | `d16` |
| `pipeline` | `p` | `p10` |
| `clients` | `c` | `c1600` |
| `keyspacelen` | `k` | `k3000000` |

Each key maps to a list of positive integers.

### Behavior

Given a matrix and 2 scenarios (`set`, `get`), each combination produces a new scenario with an auto-generated ID:

```
set_d16_p1_c1600_k3000000
set_d16_p10_c1600_k3000000
set_d96_p1_c1600_k3000000
...
get_d16_p1_c1600_k3000000
...
```

### Override Rules

Scenario-level values take precedence over matrix values. If a scenario already has `data_size: 32`, the matrix `data_size` values are ignored for that scenario (but the suffix still reflects the scenario's value).

```json
{
  "matrix": {"data_size": [16, 64], "pipeline": [1, 10]},
  "scenarios": [
    {"id": "set", "type": "write", "command": "SET"},
    {"id": "fixed", "type": "write", "command": "SET", "data_size": 32}
  ]
}
```

---

## Scenario Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `string` | Yes | Unique scenario identifier (for `--scenarios` filtering) |
| `type` | `string` | Yes | `"write"` or `"read"` |
| `command` | `string` | Yes | Full command string (non-empty) |
| `clients` | `int` | No | Concurrent connections (positive integer) |
| `pipeline` | `int` | No | Pipeline depth (default: 1) |
| `data_size` | `int` | No | Payload size in bytes |
| `keyspacelen` | `int` | No | Number of distinct keys |
| `duration` | `int` | No | Duration in seconds |
| `requests` | `int` | No | Total requests |
| `warmup` | `int` | No | Warmup seconds |
| `auto_populate` | `bool` | No | Auto-populate keyspace before read |
| `populate_command` | `string` | No | Command for auto-population (e.g., `"SET"`) |
| `command_ratio` | `object` | No | Mixed workload ratio (cachecannon only, see below) |
| `sequential` | `bool` | No | Use sequential key access |
| `seed` | `bool` | No | Enable random seed |
| `cluster_execution` | `string` | No | `"single"` (default) or `"parallel"` |
| `setup_commands` | `string[]` | No | Commands to run before scenario |
| `flush_before` | `bool` | No | Flush DB before this scenario |
| `dataset` | `string` | No | Path to dataset file |
| `maxdocs` | `int` | No | Max documents for write scenarios |
| `options` | `object` | No | Flag variants (key=flag, value=id suffix) |
| `profiling` | `object` | No | Per-scenario profiling override |

A scenario cannot have both `requests` and `duration`.

---

## `command_ratio` Object

Defines mixed read/write workload ratios. **Only supported by cachecannon.**

```json
{
  "command_ratio": {"GET": 80, "SET": 20}
}
```

| Constraint | Rule |
|------------|------|
| Type | `dict` of `string` → `int` |
| Keys | Non-empty command strings |
| Values | Positive integers |
| Sum | Must equal 100 |

---

## Cluster Mode

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

### CPU Allocation

```json
"cpu_allocation": {
  "cores_per_server": 8,
  "cores_per_client": 8
}
```

Or with explicit ranges:

```json
"cpu_allocation": {
  "servers": ["0-7", "8-15"],
  "clients": ["16-23", "24-31"]
}
```

`cpu_allocation` and `server_cpu_range`/`client_cpu_range` are mutually exclusive.

---

## Supported Commands

**Write:** `SET`, `MSET`, `INCR`, `LPUSH`, `RPUSH`, `LPOP`, `RPOP`, `SADD`, `HSET`, `ZADD`, `XADD`, `SPOP`, `ZPOPMIN`

**Read:** `GET`, `MGET`, `LRANGE`, `SISMEMBER`, `ZSCORE`, `ZRANGE`

cachecannon supports `GET` and `SET` only. All other commands use valkey-benchmark regardless of `--benchmark-tool`.

---

## Validation Rules

1. Config must have `test_groups` (required)
2. Each test group must have a non-empty `scenarios` array
3. Each scenario must have a non-empty `command` string
4. A scenario cannot have both `requests` and `duration`
5. `clients` must be a positive integer (when present)
6. `matrix` keys must be from: `data_size`, `pipeline`, `clients`, `keyspacelen`
7. `matrix` values must be non-empty lists of positive integers
8. `command_ratio` keys must be non-empty strings, values positive integers summing to 100
9. `cachecannon` must be a dict; `threads` must be a positive integer
10. `server_startup_config` must be a dict of non-empty string keys to string values
11. `cpu_allocation` and `server_cpu_range`/`client_cpu_range` are mutually exclusive
12. `port` must be between 1 and 65535
13. `warmup` must be a non-negative integer
14. `io-threads` must be a positive integer or list of positive integers

---

## Migration Guide

The old commands-based format has been removed. All configs must use `test_groups`.

**Before (removed):**
```json
{
  "commands": ["SET", "GET"],
  "data_sizes": [16, 64],
  "pipelines": [1, 10],
  "clients": [50],
  "keyspacelen": [10000000]
}
```

**After:**
```json
{
  "test_groups": [
    {
      "scenarios": [
        {"id": "set", "type": "write", "command": "SET", "clients": 50, "pipeline": 10, "keyspacelen": 10000000, "data_size": 16},
        {"id": "get", "type": "read", "command": "GET", "clients": 50, "pipeline": 10, "keyspacelen": 10000000, "data_size": 16}
      ]
    }
  ]
}
```

Or use `matrix` for Cartesian product expansion:

```json
{
  "test_groups": [
    {
      "matrix": {
        "data_size": [16, 64],
        "pipeline": [1, 10],
        "clients": [50],
        "keyspacelen": [10000000]
      },
      "scenarios": [
        {"id": "set", "type": "write", "command": "SET"},
        {"id": "get", "type": "read", "command": "GET", "auto_populate": true, "populate_command": "SET"}
      ]
    }
  ]
}
```
