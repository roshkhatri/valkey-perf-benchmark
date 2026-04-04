# Implementation Plan: Unified Config Format

## Overview

Remove the commands-based config format entirely, standardize on test_groups, migrate all config files, consolidate dual code paths in benchmark.py and valkey_benchmark.py, and update the test suite.

## Tasks

- [ ] 1. Migrate config files from commands format to test_groups format
  - [ ] 1.1 Migrate `configs/benchmark-configs.json` to test_groups format
    - Convert 13 commands into 13 scenarios with duration mode
    - Add `auto_populate`/`populate_command` for read commands (GET, MGET, LRANGE, SPOP, ZPOPMIN, XRANGE)
    - Set `type`, `data_size`, `pipeline`, `clients`, `keyspacelen`, `warmup`, `benchmark_threads` per scenario
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  - [ ] 1.2 Migrate `configs/benchmark-config-arm.json` to test_groups format
    - Cartesian product: 2 commands × 3 data_sizes × 2 pipelines = 12 scenarios
    - Preserve `io-threads`, `server_cpu_range`, `client_cpu_range` as top-level fields
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  - [ ] 1.3 Migrate `configs/benchmark-config-tag-arm.json` to test_groups format
    - Cartesian product: 2 commands × 2 data_sizes × 2 pipelines = 8 scenarios
    - _Requirements: 2.1, 2.2, 2.3_
  - [ ] 1.4 Migrate `configs/benchmark-configs-cluster-tls.json` to test_groups format
    - Convert 11 commands into 11 scenarios with requests mode
    - Preserve `io-threads`, `server_cpu_range`, `client_cpu_range` as top-level fields
    - _Requirements: 2.1, 2.2, 2.5_

- [ ] 2. Refactor config validation to only support test_groups format
  - [ ] 2.1 Refactor `validate_config` in `benchmark.py`
    - Remove `REQUIRED_KEYS` constant
    - Remove `has_commands` branch and commands-specific validation
    - Make `test_groups` required (raise ValueError if missing)
    - Add per-scenario validation: non-empty command, no both requests+duration, positive clients, positive maxdocs
    - Keep shared field validation (port, cpu_allocation, cluster_mode, tls_mode)
    - _Requirements: 1.1, 1.2, 3.1, 3.2, 3.3, 3.4, 3.5, 3.7, 3.8, 3.9, 3.10, 3.11_
  - [ ] 2.2 Update `load_configs` in `benchmark.py`
    - Add empty array check (raise ValueError)
    - Remove any format detection logic
    - _Requirements: 7.1_
  - [ ]* 2.3 Update `tests/test_benchmark_config.py` for unified validation
    - Remove commands-format-specific tests
    - Add tests for new per-scenario validation (empty command, both requests+duration, non-positive clients, non-positive maxdocs)
    - Update existing test_groups validation tests
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.10, 3.11, 8.2, 8.5_
  - [ ]* 2.4 Write property test for valid configs pass validation
    - **Property 1: Valid configs pass validation**
    - **Validates: Requirements 3.9**

- [ ] 3. Consolidate scenario iteration in `valkey_benchmark.py`
  - [ ] 3.1 Refactor `ClientRunner._iterate_scenarios` to single path
    - Remove `_iterate_simple_scenarios()` method
    - Remove `_iterate_test_groups_scenarios()` method
    - Implement single iteration over `test_groups` with group/scenario filtering
    - Include `run_num` loop for `self.runs` support
    - _Requirements: 4.1, 4.2, 4.3, 4.4_
  - [ ] 3.2 Remove `_generate_combinations()` method
    - No longer needed since Cartesian product is done at migration time
    - _Requirements: 4.1_
  - [ ] 3.3 Remove `uses_test_groups` from `ClientRunner.__init__` and all callers
    - Remove parameter from `__init__`
    - Remove from `run_benchmark_matrix()` in `benchmark.py`
    - Remove format detection in `main()` (`uses_test_groups = "test_groups" in config`)
    - _Requirements: 1.3_
  - [ ]* 3.4 Write property tests for scenario iteration
    - **Property 2: Group filtering**
    - **Validates: Requirements 4.2**
    - **Property 3: Scenario filtering**
    - **Validates: Requirements 4.3**
    - **Property 5: Iterator produces at least one scenario**
    - **Validates: Requirements 4.5**

- [ ] 4. Consolidate command building in `valkey_benchmark.py`
  - [ ] 4.1 Refactor `_build_benchmark_command` to scenario-only interface
    - Remove positional args (requests, keyspacelen, data_size, pipeline, clients, command, seed_val, sequential, duration, warmup)
    - Always take a scenario dict
    - Use `-t command` for built-in commands (single word, in READ_COMMANDS + WRITE_COMMANDS)
    - Use `-- command_string` for custom commands (multi-word or not in built-in list)
    - Read `data_size`, `keyspacelen`, `pipeline`, `clients`, `duration`, `requests`, `warmup`, `benchmark_threads`, `sequential` from scenario dict
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8_
  - [ ]* 4.2 Update `tests/test_benchmark_command.py` for scenario-based interface
    - Rewrite tests to pass scenario dicts instead of positional args
    - Add tests for built-in vs custom command detection
    - _Requirements: 8.4_
  - [ ]* 4.3 Write property test for command builder flag correctness
    - **Property 6: Command builder flag correctness**
    - **Validates: Requirements 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8**

- [ ] 5. Consolidate scenario execution in `valkey_benchmark.py`
  - [ ] 5.1 Refactor `_execute_scenario` to single unified path
    - Remove `_execute_simple_scenario()` method
    - Remove `_execute_test_groups_scenario()` method
    - Handle `flush_before`, `setup_commands`, `auto_populate` in unified path
    - Handle warmup, parallel execution, profiling in unified path
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_
  - [ ] 5.2 Update `_populate_keyspace` to work with scenario dict
    - Read `populate_command`, `requests`/`keyspacelen`, `data_size`, `pipeline`, `clients` from scenario
    - Call `_build_benchmark_command` with scenario dict
    - _Requirements: 6.4_
  - [ ]* 5.3 Write property test for failure marker completeness
    - **Property 7: Failure marker completeness**
    - **Validates: Requirements 6.5**

- [ ] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Update test fixtures and add migration validation tests
  - [ ] 7.1 Update `tests/conftest.py` fixtures
    - Remove `minimal_valid_config` (commands format) or convert to test_groups format
    - Update `minimal_client_runner` to not use `uses_test_groups` parameter
    - _Requirements: 8.5_
  - [ ]* 7.2 Add `tests/test_config_migration.py` to validate all migrated config files
    - Load each config file in `configs/` and verify it passes validation
    - Verify correct number of scenarios in each migrated file
    - Verify read command scenarios have `auto_populate: true`
    - _Requirements: 8.3_
  - [ ]* 7.3 Write property test for options expansion count
    - **Property 4: Options expansion count**
    - **Validates: Requirements 4.4**

- [ ] 8. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- `configs/module-test-arm.json` is already in test_groups format and needs no changes
- The `_expand_scenario_options` method is unchanged — it already works with scenario dicts
- Property tests validate universal correctness properties; unit tests validate specific examples and edge cases
