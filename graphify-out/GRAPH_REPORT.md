# Graph Report - /home/rvkhatri/Projects/valkey-perf-benchmark  (2026-04-13)

## Corpus Check
- 59 files · ~80,783 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1385 nodes · 2196 edges · 40 communities detected
- Extraction: 74% EXTRACTED · 26% INFERRED · 0% AMBIGUOUS · INFERRED: 573 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]

## God Nodes (most connected - your core abstractions)
1. `ClientRunner` - 108 edges
2. `MetricsProcessor` - 96 edges
3. `GitRepoFixture` - 90 edges
4. `ServerLauncher` - 79 edges
5. `BenchmarkTool` - 60 edges
6. `RunContext` - 59 edges
7. `PerformanceProfiler` - 39 edges
8. `ServerBuilder` - 34 edges
9. `BenchmarkBuilder` - 33 edges
10. `BenchmarkResult` - 32 edges

## Surprising Connections (you probably didn't know these)
- `Unit tests for process_metrics.py — MetricsProcessor.create_metrics.` --uses--> `MetricsProcessor`  [INFERRED]
  /home/rvkhatri/Projects/valkey-perf-benchmark/tests/test_metrics_processor.py → /home/rvkhatri/Projects/valkey-perf-benchmark/process_metrics.py
- `A MetricsProcessor with typical constructor args.` --uses--> `MetricsProcessor`  [INFERRED]
  /home/rvkhatri/Projects/valkey-perf-benchmark/tests/test_metrics_processor.py → /home/rvkhatri/Projects/valkey-perf-benchmark/process_metrics.py
- `A MetricsProcessor with all optional constructor args set.` --uses--> `MetricsProcessor`  [INFERRED]
  /home/rvkhatri/Projects/valkey-perf-benchmark/tests/test_metrics_processor.py → /home/rvkhatri/Projects/valkey-perf-benchmark/process_metrics.py
- `Tests for MetricsProcessor.write_metrics.` --uses--> `MetricsProcessor`  [INFERRED]
  /home/rvkhatri/Projects/valkey-perf-benchmark/tests/test_metrics_processor.py → /home/rvkhatri/Projects/valkey-perf-benchmark/process_metrics.py
- `Helper for creating and managing temporary git repositories.` --uses--> `MetricsProcessor`  [INFERRED]
  /home/rvkhatri/Projects/valkey-perf-benchmark/tests/integration/conftest.py → /home/rvkhatri/Projects/valkey-perf-benchmark/process_metrics.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.03
Nodes (92): ABC, available_tools(), BenchmarkResult, BenchmarkTool, create_tool(), Benchmark tool abstraction layer.  Defines the pluggable BenchmarkTool interface, Class decorator that registers a BenchmarkTool implementation., Instantiate a registered tool by name. (+84 more)

### Community 1 - "Community 1"
Cohesion: 0.03
Nodes (95): _apply_config_to_servers(), BenchmarkBuilder, Build valkey-benchmark from latest unstable for benchmarking., Clone and compile latest Valkey unstable for valkey-benchmark binary., Execute a command with optional check and fail loudly if needed., Clone latest unstable branch if directory doesn't exist., Build valkey-benchmark and return path to binary., Remove the benchmark directory. (+87 more)

### Community 2 - "Community 2"
Cohesion: 0.03
Nodes (73): GitRepoFixture, mock_valkey_repo(), Run git command in repo directory., Create a commit with optional file changes. Returns commit SHA., Create a new branch from a reference., Checkout a branch or commit., Get current HEAD commit SHA., Create minimal Valkey directory structure for testing. (+65 more)

### Community 3 - "Community 3"
Cohesion: 0.03
Nodes (19): _make_config(), Unit tests for benchmark.py: validate_config, parse_bool, and validation helpers, Build a minimal valid unified config, applying overrides., TestGetActivePorts, TestParseBool, TestValidateConfigCachecannon, TestValidateConfigCommandRatio, TestValidateConfigMatrix (+11 more)

### Community 4 - "Community 4"
Cohesion: 0.02
Nodes (19): Unit tests for utils/compare_benchmark_results.py statistical functions., Tests for stats-only formatting., Tests for common/unique configuration extraction., TestAverageMultipleRuns, TestCalculateConfidenceInterval, TestCalculateConfidenceIntervalPercentage, TestCalculateMean, TestCalculatePercentageChange (+11 more)

### Community 5 - "Community 5"
Cohesion: 0.04
Nodes (17): Tests for cachecannon_runner module., Tests for _parse_json_output()., Tests for supports_command()., Tests for run_cachecannon()., Tests for cachecannon_config parameter in _build_toml_config()., Tests for command_ratio parameter in _build_toml_config()., Tests for new params in run_cachecannon()., Tests for _build_toml_config(). (+9 more)

### Community 6 - "Community 6"
Cohesion: 0.05
Nodes (70): average_multiple_runs(), calculate_confidence_interval(), calculate_confidence_interval_percentage(), calculate_mean(), calculate_percentage_change(), calculate_prediction_interval(), calculate_prediction_interval_percentage(), calculate_stdev() (+62 more)

### Community 7 - "Community 7"
Cohesion: 0.04
Nodes (7): Unit tests for postgres utility pure logic functions.  Tests cover: - _is_list_s, TestAnalyzeMetricsSchema, TestConvertMetricsToRows, TestDetectFieldType, TestIsConfigArraySubset, TestIsConfigSubset, TestIsListSubset

### Community 8 - "Community 8"
Cohesion: 0.08
Nodes (21): MockBenchmarkBinary, Creates a standalone mock valkey-benchmark executable., Create the mock benchmark script., _make_runner(), Integration tests for benchmark execution flow., Test benchmark execution with mock binary., Run the mock benchmark binary and return stdout lines., Test benchmark command construction. (+13 more)

### Community 9 - "Community 9"
Cohesion: 0.07
Nodes (14): _all_scenarios(), _make_runner_with_tools(), End-to-end integration tests for config → tool → metrics pipeline., Test tool registry + tool selection logic end-to-end., Test BenchmarkResult → MetricsProcessor → metrics dict flow., Flatten all scenarios from loaded configs., Validate configs that exercise multiple features together., Load real config files and verify the full JSON → validate → expand pipeline. (+6 more)

### Community 10 - "Community 10"
Cohesion: 0.06
Nodes (33): create_sample_metrics(), git_repo(), metrics_processor(), minimal_benchmark_config(), minimal_client_runner(), minimal_config_file(), minimal_test_groups_config(), minimal_valid_config() (+25 more)

### Community 11 - "Community 11"
Cohesion: 0.08
Nodes (12): _make_csv(), Unit tests for pure logic methods on ClientRunner from valkey_benchmark.py., Build CSV stdout string from a list of metric dicts., Tests for ClientRunner._is_cme., Tests for ClientRunner._should_use_parallel., Tests for ClientRunner._create_failure_marker., Tests for ClientRunner._aggregate_parallel_results., Return a (stdout, stderr, port) tuple with valid CSV. (+4 more)

### Community 12 - "Community 12"
Cohesion: 0.07
Nodes (20): Unit tests for expand_matrix() in benchmark.py., Tests that the original group is not mutated., expand_matrix does not modify the input dict., Group without matrix key is returned unchanged., Group with empty matrix dict is returned unchanged., Tests for Cartesian product expansion., 1 scenario x 2 data_sizes = 2 expanded scenarios., 2 scenarios x 2 data_sizes x 2 pipelines = 8 expanded scenarios. (+12 more)

### Community 13 - "Community 13"
Cohesion: 0.07
Nodes (5): Unit tests for utils/cpu_utils.py — parse_core_range, calculate_cpu_ranges, vali, TestCalculateCpuRanges, TestParseCoreRangeInvalid, TestParseCoreRangeValid, TestValidateExplicitCpuRanges

### Community 14 - "Community 14"
Cohesion: 0.07
Nodes (19): base_cmd_params(), Unit tests for ClientRunner._build_benchmark_command., When self.cores is set, taskset is prepended., Test duration mode uses --duration instead of -n., When duration is provided, --duration is used instead of -n., Without duration, -n flag is used with requests count., Test simple format (no scenario) produces correct flags., Simple format command includes all expected positional flags. (+11 more)

### Community 15 - "Community 15"
Cohesion: 0.07
Nodes (16): Unit tests for ClientRunner._parse_csv_row and _find_csv_start., Finds index of an unquoted CSV header line., Returns None when no CSV header is present., Returns None for an empty list of lines., Finds header when it is the very first line., Test _parse_csv_row parses benchmark CSV output., Valid CSV output with header and data row returns a dict., Test _find_csv_start finds correct header line index. (+8 more)

### Community 16 - "Community 16"
Cohesion: 0.07
Nodes (11): processor(), processor_with_optionals(), Unit tests for process_metrics.py — MetricsProcessor.create_metrics., A MetricsProcessor with typical constructor args., A MetricsProcessor with all optional constructor args set., Tests for MetricsProcessor.write_metrics., TestCreateMetricsBenchmarkMode, TestCreateMetricsEmpty (+3 more)

### Community 17 - "Community 17"
Cohesion: 0.07
Nodes (17): Integration tests for benchmark comparison workflow., Test metrics file format compatibility., Verify metrics file has expected structure., Test metrics with io_threads field., Test metrics with cluster mode enabled., Test generation of PR comment content., Verify comparison output is valid markdown for PR comments., Verify percentage change is shown in comparison. (+9 more)

### Community 18 - "Community 18"
Cohesion: 0.13
Nodes (25): cleanup_incomplete_commits(), create_tables(), determine_commits_to_benchmark(), _find_superset_configs(), get_commits_by_config(), get_unique_configs(), _git_commit_time(), _git_rev_list() (+17 more)

### Community 19 - "Community 19"
Cohesion: 0.08
Nodes (15): Unit tests for ClientRunner._expand_scenario_options., Variant description is unchanged when flag is empty string., Expanding options does not modify the original scenario dict., Scenario with empty options dict returns list with original scenario., Scenario with options=None returns list with original scenario., Test scenarios with options return correct variants., Single option produces one variant with id suffix and command flag., Multiple options produce one variant per option. (+7 more)

### Community 20 - "Community 20"
Cohesion: 0.08
Nodes (3): Tests for significant figures formatting based on uncertainty., Verify formatted value doesn't lose more than σ precision., TestFormatWithSigFigs

### Community 21 - "Community 21"
Cohesion: 0.1
Nodes (5): Unit tests for valkey_benchmark.py — deep_merge function., TestDeepMergeFlatDicts, TestDeepMergeImmutability, TestDeepMergeNestedDicts, TestDeepMergeNonDictOverride

### Community 22 - "Community 22"
Cohesion: 0.16
Nodes (17): analyze_metrics_schema(), convert_metrics_to_rows(), create_indexes(), create_or_update_table(), detect_field_type(), get_existing_columns(), main(), process_commit_metrics() (+9 more)

### Community 23 - "Community 23"
Cohesion: 0.21
Nodes (15): apply_transforms(), build_field_configs(), download_wikipedia(), generate_csv_dataset(), generate_dataset(), generate_queries(), main(), Build field configurations from config. (+7 more)

### Community 24 - "Community 24"
Cohesion: 0.2
Nodes (13): calculate_and_validate_cpu_ranges(), calculate_client_cpu_ranges(), calculate_cpu_ranges(), calculate_server_cpu_ranges(), parse_core_range(), CPU core range parsing and allocation utilities., Calculate CPU ranges for servers or clients., Calculate CPU ranges with validation (DRY helper). (+5 more)

### Community 25 - "Community 25"
Cohesion: 0.17
Nodes (7): PerCPUMonitor, Per-CPU monitoring for detecting scheduler issues., Background monitoring loop using mpstat., Monitor per-physical-CPU utilization., Initialize per-CPU monitor.          Args:             cpu_cores: CPU cores to m, Start monitoring per-CPU utilization., Stop monitoring and return per-CPU statistics.

### Community 26 - "Community 26"
Cohesion: 0.21
Nodes (11): _build_toml_config(), is_cachecannon_available(), _parse_json_output(), Cachecannon benchmark runner adapter.  Generates TOML configs from our JSON benc, Parse cachecannon JSON (NDJSON) output into our metrics dict format.      Cachec, Check if cachecannon binary is available., Run a single cachecannon benchmark and return parsed metrics dict.      Returns, Return True if cachecannon supports this command. (+3 more)

### Community 27 - "Community 27"
Cohesion: 0.17
Nodes (7): CPUMonitor, CPU monitoring for performance tests., Monitor CPU usage during performance tests with per-thread tracking and CPU affi, Monitoring loop - track CPU per thread and peak memory., Initialize CPU monitor with server type detection.          Args:             se, Start CPU monitoring for a test., Stop CPU monitoring and return essential statistics.

### Community 28 - "Community 28"
Cohesion: 0.18
Nodes (5): Unit tests for valkey_server.py — ServerLauncher._parse_cluster_info., Create a minimal ServerLauncher instance for testing _parse_cluster_info., server_launcher(), TestParseClusterInfoEmpty, TestParseClusterInfoValid

### Community 29 - "Community 29"
Cohesion: 0.22
Nodes (6): ModuleBuilder, Build valkey modules (.so files)., Build valkey modules from source., Initialize module builder.          Args:             module_path: Path to modul, Build the module and return path to .so file.          Returns:             Abso, Find the built .so file in the module directory.          Returns:             P

### Community 30 - "Community 30"
Cohesion: 0.24
Nodes (9): _fetch_ref(), get_commit_timestamp(), Git utilities for resolving refs and fetching commits., Resolve a git ref (branch, tag, or SHA) to a full commit SHA.      Handles shall, Try to resolve ref locally without network access., Fetch a specific ref from origin., Get ISO8601 timestamp for a commit SHA.      Args:         sha: Commit SHA (shou, resolve_ref() (+1 more)

### Community 31 - "Community 31"
Cohesion: 0.2
Nodes (7): exec_config(), mock_args(), Verify commit_id is passed through to ClientRunner, not defaulted to HEAD.  Regr, Minimal exec_config as produced by _iterate_execution_configs., Minimal args namespace for _execute_benchmark_run., commit_id passed to _execute_benchmark_run must reach ClientRunner., TestCommitIdPassthrough

### Community 32 - "Community 32"
Cohesion: 0.36
Nodes (7): _build(), Tests for server_startup_config support in _build_server_command., test_build_server_command_add_new_param(), test_build_server_command_default_without_startup_config(), test_build_server_command_no_mutation(), test_build_server_command_override_and_add(), test_build_server_command_override_default()

### Community 33 - "Community 33"
Cohesion: 0.5
Nodes (3): Verify requirements.txt is in sync with requirements.in., Every package declared in requirements.in must appear in requirements.txt., test_requirements_txt_contains_all_packages_from_requirements_in()

### Community 34 - "Community 34"
Cohesion: 1.0
Nodes (1): Context manager for Valkey client connections.

### Community 35 - "Community 35"
Cohesion: 1.0
Nodes (1): Unique tool identifier.

### Community 36 - "Community 36"
Cohesion: 1.0
Nodes (1): Return True if this tool can benchmark the given command.

### Community 37 - "Community 37"
Cohesion: 1.0
Nodes (1): Return True if this tool supports mixed read/write ratios.

### Community 38 - "Community 38"
Cohesion: 1.0
Nodes (1): Execute a benchmark scenario. Return None on failure.

### Community 39 - "Community 39"
Cohesion: 1.0
Nodes (1): Ensure we never silently fall back to 'HEAD'.

## Knowledge Gaps
- **250 isolated node(s):** `Build Valkey from source for benchmarking.`, `Compile Valkey for a specific commit.`, `Execute a command with optional check and fail loudly if needed.`, `Terminate all valkey processes.`, `Terminate all valkey processes and delete the cloned Valkey directory.` (+245 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 34`** (1 nodes): `Context manager for Valkey client connections.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 35`** (1 nodes): `Unique tool identifier.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 36`** (1 nodes): `Return True if this tool can benchmark the given command.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 37`** (1 nodes): `Return True if this tool supports mixed read/write ratios.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 38`** (1 nodes): `Execute a benchmark scenario. Return None on failure.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 39`** (1 nodes): `Ensure we never silently fall back to 'HEAD'.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ClientRunner` connect `Community 1` to `Community 0`, `Community 8`, `Community 9`, `Community 10`, `Community 11`?**
  _High betweenness centrality (0.114) - this node is a cross-community bridge._
- **Why does `MetricsProcessor` connect `Community 0` to `Community 1`, `Community 2`, `Community 8`, `Community 9`, `Community 10`, `Community 16`?**
  _High betweenness centrality (0.069) - this node is a cross-community bridge._
- **Why does `GitRepoFixture` connect `Community 2` to `Community 0`, `Community 8`, `Community 10`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **Are the 81 inferred relationships involving `ClientRunner` (e.g. with `Validate repository is in 'owner/repo' format.` and `Parse command line arguments.`) actually correct?**
  _`ClientRunner` has 81 INFERRED edges - model-reasoned connections that need verification._
- **Are the 91 inferred relationships involving `MetricsProcessor` (e.g. with `ClientRunner` and `Client-side benchmark execution logic.`) actually correct?**
  _`MetricsProcessor` has 91 INFERRED edges - model-reasoned connections that need verification._
- **Are the 78 inferred relationships involving `GitRepoFixture` (e.g. with `TestPRWorkflowSimulation` and `TestWorkflowArtifacts`) actually correct?**
  _`GitRepoFixture` has 78 INFERRED edges - model-reasoned connections that need verification._
- **Are the 60 inferred relationships involving `ServerLauncher` (e.g. with `Validate repository is in 'owner/repo' format.` and `Parse command line arguments.`) actually correct?**
  _`ServerLauncher` has 60 INFERRED edges - model-reasoned connections that need verification._