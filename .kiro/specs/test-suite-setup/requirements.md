# Requirements Document

## Introduction

This feature adds a comprehensive test suite to the valkey-perf-benchmark repository, which currently has zero tests. The goal is to enable the team to confidently add new functionality without introducing regressions. The test suite focuses on unit tests for pure logic functions and property-based tests for parsing and validation functions across the codebase.

## Glossary

- **Test_Suite**: The collection of automated unit tests and property-based tests covering the valkey-perf-benchmark codebase
- **Parser**: A function that converts string input into structured data (e.g., `parse_core_range`, `parse_bool`)
- **Validator**: A function that checks input data against defined constraints and raises errors for invalid input (e.g., `validate_config`, `validate_explicit_cpu_ranges`)
- **Statistical_Calculator**: A function that computes statistical measures from numeric data (e.g., `calculate_mean`, `calculate_stdev`, `calculate_confidence_interval`)
- **Deep_Merge**: The `deep_merge` function that recursively merges two dictionaries, with override values taking precedence
- **CPU_Range**: A string format representing CPU core assignments (e.g., "0-3", "0,2,4", "0-3,8-11")
- **Metrics_Processor**: The `MetricsProcessor` class that parses benchmark CSV output into structured metrics dictionaries and writes them to JSON files
- **PBT_Library**: The property-based testing library (Hypothesis) used to generate random inputs for property tests

## Requirements

### Requirement 1: Test Framework Setup

**User Story:** As a developer, I want a properly configured test framework with property-based testing support, so that I can run tests easily and consistently.

#### Acceptance Criteria

1. THE Test_Suite SHALL use pytest as the test runner and Hypothesis as the PBT_Library
2. THE Test_Suite SHALL be organized in a `tests/` directory at the repository root
3. WHEN a developer runs `pytest`, THE Test_Suite SHALL discover and execute all tests without manual configuration

### Requirement 2: CPU Range Parsing Tests

**User Story:** As a developer, I want tests for CPU core range parsing, so that changes to CPU allocation logic do not break core assignment.

#### Acceptance Criteria

1. WHEN a valid simple range string (e.g., "0-3") is provided, THE Parser SHALL return the correct list of core IDs
2. WHEN a valid comma-separated string (e.g., "0,2,4") is provided, THE Parser SHALL return the correct list of core IDs
3. WHEN a valid mixed range string (e.g., "0-3,8-11") is provided, THE Parser SHALL return the correct list of core IDs
4. WHEN an invalid range string is provided (empty, malformed, negative values, reversed range), THE Parser SHALL raise a ValueError
5. FOR ALL valid CPU_Range strings, parsing SHALL produce a sorted list of non-negative integers consistent with the input specification (round-trip property)

### Requirement 3: CPU Range Calculation and Validation Tests

**User Story:** As a developer, I want tests for CPU range calculation and overlap validation, so that server and client CPU assignments remain correct and non-overlapping.

#### Acceptance Criteria

1. WHEN `calculate_cpu_ranges` is called with cluster_nodes, cores_per_unit, and offset, THE Statistical_Calculator SHALL return the correct number of ranges with correct core boundaries
2. WHEN `validate_explicit_cpu_ranges` is called with overlapping server and client ranges, THE Validator SHALL raise a ValueError identifying the overlapping cores
3. WHEN `validate_explicit_cpu_ranges` is called with non-overlapping ranges, THE Validator SHALL complete without error
4. FOR ALL non-overlapping server and client CPU_Range pairs, validation SHALL succeed

### Requirement 4: Statistical Calculation Tests

**User Story:** As a developer, I want tests for statistical functions, so that benchmark result comparisons remain mathematically correct.

#### Acceptance Criteria

1. WHEN `calculate_mean` is called with a list containing None values, THE Statistical_Calculator SHALL compute the mean of only the non-None values
2. WHEN `calculate_mean` is called with an empty list, THE Statistical_Calculator SHALL return 0.0
3. WHEN `calculate_stdev` is called with a single value or empty list, THE Statistical_Calculator SHALL return 0.0
4. WHEN `calculate_confidence_interval` is called with one or fewer values, THE Statistical_Calculator SHALL return (0.0, 0.0)
5. WHEN `calculate_prediction_interval` is called with one or fewer values, THE Statistical_Calculator SHALL return (0.0, 0.0)
6. FOR ALL non-empty lists of numeric values, `calculate_mean` SHALL return a value within the range [min(values), max(values)]
7. FOR ALL lists with two or more numeric values, `calculate_stdev` SHALL return a non-negative value
8. FOR ALL lists with two or more numeric values, the confidence interval lower bound SHALL be less than or equal to the upper bound
9. FOR ALL lists with two or more numeric values, the prediction interval SHALL be wider than or equal to the confidence interval

### Requirement 5: Deep Merge Tests

**User Story:** As a developer, I want tests for dictionary deep merging, so that benchmark configuration composition remains correct.

#### Acceptance Criteria

1. WHEN `deep_merge` is called with two flat dictionaries, THE Deep_Merge function SHALL return a dictionary containing all keys from both inputs with override values taking precedence
2. WHEN `deep_merge` is called with nested dictionaries, THE Deep_Merge function SHALL recursively merge nested structures
3. WHEN `deep_merge` is called, THE Deep_Merge function SHALL not modify the original input dictionaries
4. FOR ALL pairs of dictionaries, deep merging with an empty override SHALL return a dictionary equal to the base

### Requirement 6: Configuration Validation Tests

**User Story:** As a developer, I want tests for configuration validation, so that invalid benchmark configurations are caught before execution.

#### Acceptance Criteria

1. WHEN `validate_config` is called with a config missing required keys, THE Validator SHALL raise a ValueError
2. WHEN `validate_config` is called with a config specifying both 'requests' and 'duration', THE Validator SHALL raise a ValueError
3. WHEN `validate_config` is called with a config specifying neither 'requests' nor 'duration', THE Validator SHALL raise a ValueError
4. WHEN `validate_config` is called with a valid commands-based config, THE Validator SHALL complete without error
5. WHEN `validate_config` is called with a valid test_groups-based config, THE Validator SHALL complete without error

### Requirement 7: Parse Bool Tests

**User Story:** As a developer, I want tests for boolean parsing, so that CLI flag interpretation remains consistent.

#### Acceptance Criteria

1. WHEN `parse_bool` is called with boolean values, THE Parser SHALL return the same boolean value
2. WHEN `parse_bool` is called with string values ("yes", "true", "1"), THE Parser SHALL return True
3. WHEN `parse_bool` is called with string values ("no", "false", "0"), THE Parser SHALL return False
4. WHEN `parse_bool` is called with non-boolean, non-string values, THE Parser SHALL return the truthiness of the value

### Requirement 8: Metrics Processing Tests

**User Story:** As a developer, I want tests for metrics creation, so that benchmark result parsing and output remain correct.

#### Acceptance Criteria

1. WHEN `create_metrics` is called with valid benchmark data, THE Metrics_Processor SHALL return a dictionary containing all required metric fields
2. WHEN `create_metrics` is called with empty benchmark data, THE Metrics_Processor SHALL return None
3. WHEN `create_metrics` is called with non-numeric metric values, THE Metrics_Processor SHALL use default values (0.0) for unparseable fields
4. FOR ALL valid benchmark data inputs, `create_metrics` SHALL produce a dictionary where all latency values are non-negative floats

### Requirement 9: Benchmark Command Building Tests

**User Story:** As a developer, I want tests for benchmark command construction, so that CLI commands passed to valkey-benchmark remain correct.

#### Acceptance Criteria

1. WHEN `_build_benchmark_command` is called in simple format, THE ClientRunner SHALL produce a command list containing the correct flags for requests, keyspacelen, data_size, pipeline, clients, and command
2. WHEN `_build_benchmark_command` is called with TLS enabled, THE ClientRunner SHALL include TLS-related flags in the command
3. WHEN `_build_benchmark_command` is called with CPU pinning cores, THE ClientRunner SHALL prepend taskset with the correct core range
4. WHEN `_build_benchmark_command` is called with duration mode, THE ClientRunner SHALL use --duration instead of -n flag

### Requirement 10: CSV Parsing Tests

**User Story:** As a developer, I want tests for benchmark CSV output parsing, so that result extraction from valkey-benchmark output remains correct.

#### Acceptance Criteria

1. WHEN `_parse_csv_row` is called with valid CSV output containing a header and data row, THE ClientRunner SHALL return a dictionary with the parsed values
2. WHEN `_parse_csv_row` is called with empty or None input, THE ClientRunner SHALL return None
3. WHEN `_parse_csv_row` is called with output that has no CSV header, THE ClientRunner SHALL return None
4. WHEN `_find_csv_start` is called with lines containing a CSV header, THE ClientRunner SHALL return the correct line index of the header

### Requirement 11: Scenario Expansion Tests

**User Story:** As a developer, I want tests for scenario option expansion, so that test group configuration variants are generated correctly.

#### Acceptance Criteria

1. WHEN `_expand_scenario_options` is called with a scenario that has no options, THE ClientRunner SHALL return a list containing only the original scenario
2. WHEN `_expand_scenario_options` is called with a scenario that has options, THE ClientRunner SHALL return one variant per option with the correct id suffix and command flag appended
3. FOR ALL scenarios with N options, `_expand_scenario_options` SHALL return exactly N variants

### Requirement 12: Postgres Utility Pure Logic Tests

**User Story:** As a developer, I want tests for the pure logic functions in the PostgreSQL utilities, so that config subset detection and schema analysis remain correct.

#### Acceptance Criteria

1. WHEN `_is_list_subset` is called with a list that is a subset of another list, THE function SHALL return True
2. WHEN `_is_list_subset` is called with a list that is not a subset, THE function SHALL return False
3. WHEN `_is_config_subset` is called with a config dict that is a subset of another, THE function SHALL return True
4. WHEN `_is_config_subset` is called with a config dict that is not a subset, THE function SHALL return False
5. WHEN `_is_config_array_subset` is called with a config array where each element has a superset match, THE function SHALL return True
6. WHEN `detect_field_type` is called with various Python types, THE function SHALL return the correct PostgreSQL type string
7. WHEN `analyze_metrics_schema` is called with metrics data, THE function SHALL return a schema dict containing all fields from the data plus core fields (id, created_at)
8. WHEN `convert_metrics_to_rows` is called with valid metrics and column order, THE function SHALL return tuples matching the column order with correct values
9. FOR ALL pairs of lists A and B where A is a subset of B, `_is_list_subset(A, B)` SHALL return True
10. FOR ALL config dicts, `_is_config_subset(config, config)` SHALL return True (reflexivity)

### Requirement 13: Server Cluster Info Parsing Tests

**User Story:** As a developer, I want tests for cluster info parsing, so that cluster state detection remains correct.

#### Acceptance Criteria

1. WHEN `_parse_cluster_info` is called with a valid cluster info response string, THE ServerLauncher SHALL return a dictionary with all key-value pairs correctly parsed
2. WHEN `_parse_cluster_info` is called with an empty string, THE ServerLauncher SHALL return an empty dictionary

### Requirement 13: Benchmark Result Comparison Utility Tests

**User Story:** As a developer, I want tests for the benchmark comparison utilities, so that result grouping, averaging, and percentage change calculations remain correct.

#### Acceptance Criteria

1. WHEN `calculate_percentage_change` is called with a new and old value, THE Statistical_Calculator SHALL return the correct percentage change
2. WHEN `calculate_percentage_change` is called with an old value of zero, THE Statistical_Calculator SHALL return 0.0
3. WHEN `average_multiple_runs` is called with multiple runs of identical configuration, THE Statistical_Calculator SHALL return a single averaged result with correct mean and stdev values
4. WHEN `average_multiple_runs` is called with a single run, THE Statistical_Calculator SHALL return the run with zero standard deviations
5. WHEN `discover_config_keys` is called with benchmark data, THE Statistical_Calculator SHALL return only configuration keys, excluding metric and metadata fields
6. WHEN `group_by_command` is called with benchmark items, THE Statistical_Calculator SHALL group items by their command field
