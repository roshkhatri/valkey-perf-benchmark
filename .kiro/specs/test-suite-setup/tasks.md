# Implementation Plan: Test Suite Setup

## Overview

Add a comprehensive test suite to the valkey-perf-benchmark repository using pytest and Hypothesis. Tests target pure logic functions across the codebase with both unit tests and property-based tests.

## Tasks

- [x] 1. Set up test infrastructure
  - [x] 1.1 Add pytest and hypothesis to requirements and create test configuration
    - Add `pytest>=7.0` and `hypothesis>=6.0` to a `requirements-test.txt` file
    - Create `pytest.ini` or add `[tool.pytest.ini_options]` section to configure test discovery for `tests/` directory
    - _Requirements: 1.1, 1.2, 1.3_
  - [x] 1.2 Create `tests/conftest.py` with path setup and shared fixtures
    - Add repo root to `sys.path` for imports
    - Create shared fixtures: `minimal_valid_config`, `minimal_test_groups_config`, `sample_benchmark_data`, `minimal_client_runner`
    - _Requirements: 1.1, 1.2_

- [x] 2. Implement CPU utils tests
  - [x] 2.1 Create `tests/test_cpu_utils.py` with unit tests for `parse_core_range` and `calculate_cpu_ranges`
    - Test simple range "0-3", comma-separated "0,2,4", mixed "0-3,8-11"
    - Test invalid inputs: empty string, reversed range, negative values, malformed strings
    - Test `calculate_cpu_ranges` with various cluster_nodes, cores_per_unit, offset values
    - Test `validate_explicit_cpu_ranges` with overlapping and non-overlapping ranges
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3_
  - [ ]* 2.2 Write property test: CPU range parse round-trip
    - **Property 1: CPU range parse round-trip**
    - **Validates: Requirements 2.5**
  - [ ]* 2.3 Write property test: calculate_cpu_ranges correctness
    - **Property 2: calculate_cpu_ranges produces correct count and boundaries**
    - **Validates: Requirements 3.1**
  - [ ]* 2.4 Write property test: non-overlapping CPU ranges pass validation
    - **Property 3: Non-overlapping CPU ranges pass validation**
    - **Validates: Requirements 3.4**

- [x] 3. Implement statistical calculation tests
  - [x] 3.1 Create `tests/test_compare_benchmark.py` with unit tests for statistical functions
    - Test `calculate_mean` with normal lists, lists with None, empty list
    - Test `calculate_stdev` with single value, empty list, normal lists
    - Test `calculate_confidence_interval` and `calculate_prediction_interval` edge cases (<=1 values)
    - Test `calculate_percentage_change` with normal values and zero old value
    - Test `average_multiple_runs` with single and multiple runs
    - Test `discover_config_keys` excludes metric fields
    - Test `group_by_command` groups correctly
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 14.1, 14.2, 14.3, 14.4, 14.5, 14.6_
  - [ ]* 3.2 Write property test: mean bounded by min/max
    - **Property 4: Mean is bounded by min and max**
    - **Validates: Requirements 4.6**
  - [ ]* 3.3 Write property test: stdev non-negative
    - **Property 5: Standard deviation is non-negative**
    - **Validates: Requirements 4.7**
  - [ ]* 3.4 Write property test: confidence interval bounds ordered
    - **Property 6: Confidence interval bounds are ordered**
    - **Validates: Requirements 4.8**
  - [ ]* 3.5 Write property test: prediction interval wider than confidence interval
    - **Property 7: Prediction interval is at least as wide as confidence interval**
    - **Validates: Requirements 4.9**

- [x] 4. Implement deep merge tests
  - [x] 4.1 Create `tests/test_deep_merge.py` with unit tests for `deep_merge`
    - Test flat dict merge with override precedence
    - Test nested dict recursive merge
    - Test merge with non-dict override values replacing dicts
    - _Requirements: 5.1, 5.2_
  - [ ]* 4.2 Write property test: deep merge immutability
    - **Property 8: Deep merge does not modify originals**
    - **Validates: Requirements 5.3**
  - [ ]* 4.3 Write property test: deep merge identity
    - **Property 9: Deep merge identity with empty override**
    - **Validates: Requirements 5.4**

- [x] 5. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement config validation and parse_bool tests
  - [x] 6.1 Create `tests/test_benchmark_config.py` with unit tests for `validate_config` and `parse_bool`
    - Test missing required keys raises ValueError
    - Test both requests and duration raises ValueError
    - Test neither requests nor duration raises ValueError
    - Test valid commands-based config passes
    - Test valid test_groups-based config passes
    - Test `parse_bool` with True/False, "yes"/"no"/"true"/"false"/"1"/"0"
    - Test validation helpers: `_validate_positive_int_list`, `_validate_positive_int`, `_validate_non_negative_int`
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 7.1, 7.2, 7.3_
  - [ ]* 6.2 Write property test: parse_bool consistency
    - **Property 10: parse_bool consistency with Python bool for non-string/non-bool values**
    - **Validates: Requirements 7.4**

- [x] 7. Implement metrics processor tests
  - [x] 7.1 Create `tests/test_metrics_processor.py` with unit tests for `MetricsProcessor`
    - Test `create_metrics` with valid benchmark data returns all required fields
    - Test `create_metrics` with empty/None data returns None
    - Test `create_metrics` with non-numeric values uses defaults
    - Test requests mode vs duration mode in output
    - _Requirements: 8.1, 8.2, 8.3_
  - [ ]* 7.2 Write property test: metrics latency non-negative
    - **Property 11: Metrics latency values are non-negative**
    - **Validates: Requirements 8.4**

- [x] 8. Implement benchmark command and CSV parsing tests
  - [x] 8.1 Create `tests/test_benchmark_command.py` with unit tests for `_build_benchmark_command`
    - Test simple format produces correct flags
    - Test TLS mode includes TLS flags
    - Test CPU pinning prepends taskset
    - Test duration mode uses --duration instead of -n
    - _Requirements: 9.1, 9.2, 9.3, 9.4_
  - [x] 8.2 Create `tests/test_csv_parsing.py` with unit tests for `_parse_csv_row` and `_find_csv_start`
    - Test valid CSV output returns parsed dict
    - Test empty/None input returns None
    - Test missing CSV header returns None
    - Test `_find_csv_start` finds correct header line index
    - _Requirements: 10.1, 10.2, 10.3, 10.4_

- [x] 9. Implement scenario expansion tests
  - [x] 9.1 Create `tests/test_scenario_expansion.py` with unit tests for `_expand_scenario_options`
    - Test scenario with no options returns single-element list
    - Test scenario with options returns correct variants with id suffix and command flag
    - _Requirements: 11.1, 11.2_
  - [ ]* 9.2 Write property test: scenario expansion count
    - **Property 12: Scenario expansion count matches options count**
    - **Validates: Requirements 11.3**

- [x] 10. Implement postgres utility and server utility tests
  - [x] 10.1 Create `tests/test_postgres_utils.py` with unit tests for postgres pure logic functions
    - Test `_is_list_subset` with subset and non-subset cases
    - Test `_is_config_subset` with subset and non-subset configs
    - Test `_is_config_array_subset` with matching and non-matching arrays
    - Test `detect_field_type` with bool, int, float, str, None
    - Test `analyze_metrics_schema` includes all data fields plus core fields
    - Test `convert_metrics_to_rows` produces correct tuples
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.8_
  - [ ]* 10.2 Write property test: list subset detection
    - **Property 13: List subset detection**
    - **Validates: Requirements 12.9**
  - [ ]* 10.3 Write property test: config subset reflexivity
    - **Property 14: Config subset reflexivity**
    - **Validates: Requirements 12.10**
  - [x] 10.4 Create `tests/test_server_utils.py` with unit tests for `_parse_cluster_info`
    - Test valid cluster info string returns correct dict
    - Test empty string returns empty dict
    - _Requirements: 13.1, 13.2_

- [x] 11. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- All tests use only pure logic functions — no external services required
