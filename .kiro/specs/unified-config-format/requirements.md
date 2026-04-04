# Requirements Document

## Introduction

The valkey-perf-benchmark project currently supports two distinct configuration formats: a "commands-based" format for standard Valkey benchmarks and a "test_groups-based" format for module benchmarks. This duality causes code duplication across config validation, scenario iteration, command building, and execution paths. This feature removes the commands-based format entirely, standardizing on `test_groups` as the only supported configuration format. All existing commands-based config files will be manually migrated to the test_groups format, and the dual code paths will be consolidated.

## Glossary

- **Unified_Config**: The single configuration schema that uses `test_groups` as the only structure for all benchmark configurations
- **Config_Validator**: The component that validates a Unified_Config against the schema, checking required fields, types, value ranges, and cross-field constraints
- **Scenario**: A single benchmark test case within a test group, containing a command, client count, duration or request count, and optional dataset/setup information
- **Scenario_Iterator**: The component that generates executable scenario data from a validated Unified_Config, replacing the separate `_iterate_simple_scenarios` and `_iterate_test_groups_scenarios` paths
- **Command_Builder**: The component that constructs valkey-benchmark CLI commands from scenario data, replacing the branching `_build_benchmark_command` logic
- **Scenario_Executor**: The component that runs a single benchmark scenario and collects results, replacing the separate `_execute_simple_scenario` and `_execute_test_groups_scenario` paths
- **Auto_Population**: The automatic pre-population of keyspace data for read commands (e.g., populating SET data before running GET benchmarks) using the READ_POPULATE_MAP

## Requirements

### Requirement 1: Single Configuration Format

**User Story:** As a benchmark operator, I want a single configuration format for all benchmarks, so that I do not need to learn and maintain two different config structures.

#### Acceptance Criteria

1. THE Unified_Config SHALL use `test_groups` as the only supported structure for all benchmark configurations
2. WHEN a config is loaded that does not contain `test_groups`, THE Config_Validator SHALL raise a ValueError with a descriptive message
3. THE system SHALL remove the `uses_test_groups` flag and all format-branching code from the runtime path
4. THE Unified_Config SHALL support all shared top-level fields including `cluster_mode`, `tls_mode`, `warmup`, `io-threads`, `benchmark-threads`, `server_cpu_range`, `client_cpu_range`, `cpu_allocation`, `port`, `modules`, `bind_ip`, `cluster_nodes`, `cluster_ports`, `seed`, `config_sets`, `profiling_sets`, and `monitoring`

### Requirement 2: Config File Migration

**User Story:** As a benchmark operator, I want all existing config files converted to the test_groups format, so that the project is consistent.

#### Acceptance Criteria

1. THE system SHALL migrate all existing commands-based config files in `configs/` to the test_groups format
2. WHEN a commands-based config has multiple parameter values (e.g., multiple data_sizes, pipelines), THE migrated config SHALL contain one scenario per combination (Cartesian product)
3. WHEN a commands-based config contains a read command from READ_POPULATE_MAP, THE migrated scenario SHALL include `auto_populate: true` and the corresponding `populate_command`
4. WHEN a commands-based config uses `duration` mode, THE migrated scenarios SHALL use `duration` on each scenario
5. WHEN a commands-based config uses `requests` mode, THE migrated scenarios SHALL use `requests` on each scenario

### Requirement 3: Configuration Validation

**User Story:** As a benchmark operator, I want comprehensive validation of my configuration, so that errors are caught early with clear messages before benchmark execution begins.

#### Acceptance Criteria

1. WHEN a config is missing `test_groups`, THE Config_Validator SHALL raise a ValueError with a descriptive message
2. WHEN a config contains `test_groups` that is not a non-empty list, THE Config_Validator SHALL raise a ValueError
3. WHEN a scenario within a test group is missing the required `command` field, THE Config_Validator SHALL raise a ValueError identifying the group index and scenario index
4. WHEN a scenario specifies both `requests` and `duration`, THE Config_Validator SHALL raise a ValueError
5. WHEN a scenario specifies `clients` with a non-positive integer, THE Config_Validator SHALL raise a ValueError
6. WHEN a Unified_Config specifies both `cpu_allocation` and explicit `server_cpu_range`/`client_cpu_range`, THE Config_Validator SHALL raise a ValueError
7. WHEN a Unified_Config specifies a `port` outside the range 1-65535, THE Config_Validator SHALL raise a ValueError
8. WHEN `cluster_mode` is a list, THE Config_Validator SHALL accept it as valid for multi-mode execution
9. WHEN a Unified_Config passes all validation checks, THE Config_Validator SHALL return without error
10. WHEN a scenario command string is empty or whitespace-only, THE Config_Validator SHALL raise a ValueError
11. WHEN a scenario specifies `maxdocs` with a non-positive value, THE Config_Validator SHALL raise a ValueError

### Requirement 4: Consolidated Scenario Iteration

**User Story:** As a developer, I want a single scenario iteration path, so that adding new benchmark features does not require changes in two separate code paths.

#### Acceptance Criteria

1. THE Scenario_Iterator SHALL produce scenario data from the `test_groups` structure using a single code path
2. WHEN `groups_to_run` is specified, THE Scenario_Iterator SHALL skip groups not in the filter set
3. WHEN `scenario_filter` is specified, THE Scenario_Iterator SHALL skip scenarios not in the filter set
4. WHEN a scenario has `options`, THE Scenario_Iterator SHALL expand them into variant scenarios using the existing `_expand_scenario_options` logic
5. FOR ALL valid Unified_Configs, the Scenario_Iterator SHALL produce at least one scenario

### Requirement 5: Consolidated Command Building

**User Story:** As a developer, I want a single command-building path, so that benchmark CLI construction logic is not duplicated.

#### Acceptance Criteria

1. THE Command_Builder SHALL construct valkey-benchmark commands from scenario data without branching on config format
2. WHEN a scenario includes a `dataset` field, THE Command_Builder SHALL include `--dataset` with the resolved absolute path
3. WHEN a scenario includes TLS mode, THE Command_Builder SHALL include TLS certificate flags (`--tls`, `--cert`, `--key`, `--cacert`)
4. WHEN a scenario includes CPU pinning via a cpu_range, THE Command_Builder SHALL prepend `taskset -c` with the specified range
5. WHEN a scenario specifies `duration`, THE Command_Builder SHALL use the `--duration` flag
6. WHEN a scenario specifies `requests`, THE Command_Builder SHALL use the `-n` flag
7. WHEN a scenario specifies `sequential: true`, THE Command_Builder SHALL include the `--sequential` flag
8. WHEN a scenario specifies `benchmark_threads`, THE Command_Builder SHALL include the `--threads` flag

### Requirement 6: Consolidated Scenario Execution

**User Story:** As a developer, I want a single execution path for all scenarios, so that result collection and error handling are consistent.

#### Acceptance Criteria

1. THE Scenario_Executor SHALL execute scenarios using a single code path
2. WHEN a scenario has `flush_before: true`, THE Scenario_Executor SHALL flush the database before execution
3. WHEN a scenario has `setup_commands`, THE Scenario_Executor SHALL execute them before the benchmark
4. WHEN a scenario has `auto_populate: true`, THE Scenario_Executor SHALL populate the keyspace with the corresponding write command before running the read benchmark
5. WHEN a scenario execution fails, THE Scenario_Executor SHALL create a failure marker with group ID, scenario ID, error message, and timestamp
6. WHEN a scenario completes successfully, THE Scenario_Executor SHALL parse CSV output and return structured metrics

### Requirement 7: Corner Case Handling

**User Story:** As a benchmark operator, I want robust handling of edge cases in configuration and execution, so that unexpected inputs produce clear errors instead of silent failures.

#### Acceptance Criteria

1. WHEN a config file contains an empty JSON array, THE Config_Validator SHALL raise a ValueError indicating no configurations found
2. WHEN a scenario specifies `clients` as zero, THE Config_Validator SHALL raise a ValueError
3. WHEN a scenario dataset file path does not exist, THE Command_Builder SHALL raise a FileNotFoundError with the missing path
4. IF a benchmark process returns a non-zero exit code, THEN THE Scenario_Executor SHALL log the error and return a failure marker instead of crashing

### Requirement 8: Expanded Test Coverage

**User Story:** As a developer, I want comprehensive tests for the unified config system, so that regressions are caught early.

#### Acceptance Criteria

1. THE Test_Suite SHALL include property-based tests verifying that the Scenario_Iterator produces the correct number of scenarios from generated configs
2. THE Test_Suite SHALL include unit tests for each Config_Validator error condition
3. THE Test_Suite SHALL include unit tests verifying all migrated config files load and validate successfully
4. THE Test_Suite SHALL include unit tests for Command_Builder output with various scenario parameter combinations
5. THE Test_Suite SHALL include edge-case tests for empty configs, missing fields, and invalid types
