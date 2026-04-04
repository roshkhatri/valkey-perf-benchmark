"""Unit tests for benchmark.py: validate_config, parse_bool, and validation helpers."""

import pytest

from benchmark import (
    validate_config,
    parse_bool,
    _validate_positive_int_list,
    _validate_positive_int,
    _validate_non_negative_int,
    _validate_positive_int_or_list,
    validate_cpu_allocation,
    validate_test_groups,
    _get_active_ports,
    _validate_matrix,
    _validate_command_ratio,
    _validate_cachecannon,
    _validate_server_startup_config,
)


# --- Helpers -----------------------------------------------------------------


def _make_config(**overrides) -> dict:
    """Build a minimal valid unified config, applying overrides."""
    cfg = {
        "cluster_mode": False,
        "tls_mode": False,
        "test_groups": [{"scenarios": [{"id": "s1", "command": "SET foo bar"}]}],
    }
    cfg.update(overrides)
    return cfg


# ---------------------------------------------------------------------------
# validate_config — test_groups required
# ---------------------------------------------------------------------------


class TestValidateConfigTestGroupsRequired:
    def test_missing_test_groups_raises_valueerror(self):
        with pytest.raises(ValueError, match="must have 'test_groups'"):
            validate_config({"cluster_mode": False, "tls_mode": False})

    def test_empty_test_groups_raises_valueerror(self):
        with pytest.raises(ValueError, match="non-empty list"):
            validate_config(_make_config(test_groups=[]))


# ---------------------------------------------------------------------------
# validate_config — scenario validation
# ---------------------------------------------------------------------------


class TestValidateConfigScenarios:
    def test_scenario_missing_command_raises_valueerror(self):
        cfg = _make_config(test_groups=[{"scenarios": [{"id": "s1"}]}])
        with pytest.raises(ValueError, match="non-empty 'command' string"):
            validate_config(cfg)

    def test_scenario_empty_command_raises_valueerror(self):
        cfg = _make_config(test_groups=[{"scenarios": [{"command": "  "}]}])
        with pytest.raises(ValueError, match="non-empty 'command' string"):
            validate_config(cfg)

    def test_scenario_both_requests_and_duration_raises_valueerror(self):
        cfg = _make_config(
            test_groups=[
                {"scenarios": [{"command": "GET key", "requests": 100, "duration": 10}]}
            ]
        )
        with pytest.raises(ValueError, match="cannot have both"):
            validate_config(cfg)

    def test_scenario_nonpositive_clients_raises_valueerror(self):
        cfg = _make_config(
            test_groups=[{"scenarios": [{"command": "GET key", "clients": 0}]}]
        )
        with pytest.raises(ValueError, match="clients must be a positive integer"):
            validate_config(cfg)


# ---------------------------------------------------------------------------
# validate_config — matrix validation
# ---------------------------------------------------------------------------


class TestValidateConfigMatrix:
    def test_matrix_valid_dict_passes(self):
        cfg = _make_config(
            test_groups=[
                {
                    "scenarios": [{"command": "GET key"}],
                    "matrix": {"data_size": [64, 128], "clients": [10]},
                }
            ]
        )
        validate_config(cfg)  # should not raise

    def test_matrix_invalid_value_type_raises(self):
        cfg = _make_config(
            test_groups=[
                {"scenarios": [{"command": "GET key"}], "matrix": {"data_size": 64}}
            ]
        )
        with pytest.raises(ValueError, match="must be a list"):
            validate_config(cfg)

    def test_matrix_invalid_key_raises(self):
        cfg = _make_config(
            test_groups=[
                {"scenarios": [{"command": "GET key"}], "matrix": {"bad_key": [1]}}
            ]
        )
        with pytest.raises(ValueError, match="unknown key"):
            validate_config(cfg)

    def test_matrix_empty_list_raises(self):
        cfg = _make_config(
            test_groups=[
                {"scenarios": [{"command": "GET key"}], "matrix": {"data_size": []}}
            ]
        )
        with pytest.raises(ValueError, match="must not be empty"):
            validate_config(cfg)


# ---------------------------------------------------------------------------
# validate_config — cachecannon section
# ---------------------------------------------------------------------------


class TestValidateConfigCachecannon:
    def test_cachecannon_section_valid_passes(self):
        cfg = _make_config(cachecannon={"threads": 4})
        validate_config(cfg)  # should not raise

    def test_cachecannon_section_invalid_threads_raises(self):
        cfg = _make_config(cachecannon={"threads": -1})
        with pytest.raises(ValueError, match="cachecannon.threads"):
            validate_config(cfg)


# ---------------------------------------------------------------------------
# validate_config — command_ratio
# ---------------------------------------------------------------------------


class TestValidateConfigCommandRatio:
    def test_command_ratio_valid_passes(self):
        cfg = _make_config(
            test_groups=[
                {
                    "scenarios": [
                        {"command": "GET key", "command_ratio": {"GET": 70, "SET": 30}}
                    ]
                }
            ]
        )
        validate_config(cfg)  # should not raise

    def test_command_ratio_not_summing_to_100_raises(self):
        cfg = _make_config(
            test_groups=[
                {
                    "scenarios": [
                        {"command": "GET key", "command_ratio": {"GET": 50, "SET": 40}}
                    ]
                }
            ]
        )
        with pytest.raises(ValueError, match="sum to 100"):
            validate_config(cfg)

    def test_command_ratio_empty_key_raises(self):
        cfg = _make_config(
            test_groups=[
                {"scenarios": [{"command": "GET key", "command_ratio": {"": 100}}]}
            ]
        )
        with pytest.raises(ValueError, match="non-empty strings"):
            validate_config(cfg)

    def test_command_ratio_negative_value_raises(self):
        cfg = _make_config(
            test_groups=[
                {
                    "scenarios": [
                        {
                            "command": "GET key",
                            "command_ratio": {"GET": -10, "SET": 110},
                        }
                    ]
                }
            ]
        )
        with pytest.raises(ValueError, match="positive integers"):
            validate_config(cfg)


# ---------------------------------------------------------------------------
# validate_config — server_startup_config
# ---------------------------------------------------------------------------


class TestValidateConfigServerStartupConfig:
    def test_server_startup_config_valid_passes(self):
        cfg = _make_config(server_startup_config={"maxmemory": "1gb", "save": ""})
        validate_config(cfg)  # should not raise

    def test_server_startup_config_empty_key_raises(self):
        cfg = _make_config(server_startup_config={"": "value"})
        with pytest.raises(ValueError, match="non-empty strings"):
            validate_config(cfg)

    def test_server_startup_config_absent_passes(self):
        cfg = _make_config()
        validate_config(cfg)  # should not raise


# ---------------------------------------------------------------------------
# validate_config — full valid config
# ---------------------------------------------------------------------------


class TestValidateConfigValid:
    def test_valid_unified_config_passes(self):
        cfg = _make_config(
            port=6379,
            cachecannon={"threads": 2},
            server_startup_config={"maxmemory": "1gb"},
            test_groups=[
                {
                    "scenarios": [
                        {
                            "command": "SET foo bar",
                            "clients": 50,
                            "command_ratio": {"SET": 100},
                        },
                    ],
                    "matrix": {"data_size": [64], "pipeline": [1]},
                }
            ],
        )
        validate_config(cfg)  # should not raise


# ---------------------------------------------------------------------------
# validate_config — mutation of cluster_mode / tls_mode
# ---------------------------------------------------------------------------


class TestValidateConfigMutation:
    def test_cluster_mode_string_converted(self, minimal_valid_config):
        minimal_valid_config["cluster_mode"] = "yes"
        validate_config(minimal_valid_config)
        assert minimal_valid_config["cluster_mode"] is True

    def test_tls_mode_string_converted(self, minimal_valid_config):
        minimal_valid_config["tls_mode"] = "false"
        validate_config(minimal_valid_config)
        assert minimal_valid_config["tls_mode"] is False


# ---------------------------------------------------------------------------
# parse_bool
# ---------------------------------------------------------------------------


class TestParseBool:
    def test_true(self):
        assert parse_bool(True) is True

    def test_false(self):
        assert parse_bool(False) is False

    @pytest.mark.parametrize("val", ["yes", "true", "1", "YES", "True", "TRUE"])
    def test_truthy_strings(self, val):
        assert parse_bool(val) is True

    @pytest.mark.parametrize("val", ["no", "false", "0", "NO", "False", "FALSE"])
    def test_falsy_strings(self, val):
        assert parse_bool(val) is False

    def test_unrecognized_string_returns_false(self):
        assert parse_bool("maybe") is False

    def test_non_string_non_bool_uses_builtin(self):
        assert parse_bool(42) is True
        assert parse_bool(0) is False


# ---------------------------------------------------------------------------
# _validate_positive_int_list
# ---------------------------------------------------------------------------


class TestValidatePositiveIntList:
    def test_valid_list(self):
        _validate_positive_int_list([1, 2, 3], "test")

    def test_empty_list_accepted(self):
        _validate_positive_int_list([], "test")

    def test_not_a_list_raises(self):
        with pytest.raises(ValueError):
            _validate_positive_int_list("not a list", "test")

    def test_contains_zero_raises(self):
        with pytest.raises(ValueError):
            _validate_positive_int_list([1, 0, 3], "test")

    def test_contains_negative_raises(self):
        with pytest.raises(ValueError):
            _validate_positive_int_list([1, -1], "test")

    def test_contains_non_int_raises(self):
        with pytest.raises(ValueError):
            _validate_positive_int_list([1, 2.5], "test")


# ---------------------------------------------------------------------------
# _validate_positive_int
# ---------------------------------------------------------------------------


class TestValidatePositiveInt:
    def test_valid(self):
        _validate_positive_int(5, "test")

    def test_zero_raises(self):
        with pytest.raises(ValueError):
            _validate_positive_int(0, "test")

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            _validate_positive_int(-1, "test")

    def test_non_int_raises(self):
        with pytest.raises(ValueError):
            _validate_positive_int(3.14, "test")


# ---------------------------------------------------------------------------
# _validate_non_negative_int
# ---------------------------------------------------------------------------


class TestValidateNonNegativeInt:
    def test_zero_valid(self):
        _validate_non_negative_int(0, "test")

    def test_positive_valid(self):
        _validate_non_negative_int(10, "test")

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            _validate_non_negative_int(-1, "test")

    def test_non_int_raises(self):
        with pytest.raises(ValueError):
            _validate_non_negative_int(1.5, "test")


# ---------------------------------------------------------------------------
# validate_cpu_allocation
# ---------------------------------------------------------------------------


class TestValidateCpuAllocation:
    def test_no_cpu_fields_passes(self):
        validate_cpu_allocation({})

    def test_mutually_exclusive_raises(self):
        cfg = {
            "cpu_allocation": {"cores_per_server": 2, "cores_per_client": 2},
            "server_cpu_range": "0-3",
        }
        with pytest.raises(ValueError, match="Cannot use both"):
            validate_cpu_allocation(cfg)

    def test_mutually_exclusive_with_client_range_raises(self):
        cfg = {
            "cpu_allocation": {"cores_per_server": 2, "cores_per_client": 2},
            "client_cpu_range": "4-7",
        }
        with pytest.raises(ValueError, match="Cannot use both"):
            validate_cpu_allocation(cfg)

    def test_missing_cores_per_client_raises(self):
        cfg = {"cpu_allocation": {"cores_per_server": 4}}
        with pytest.raises(ValueError, match="requires both"):
            validate_cpu_allocation(cfg)

    def test_missing_cores_per_server_raises(self):
        cfg = {"cpu_allocation": {"cores_per_client": 4}}
        with pytest.raises(ValueError, match="requires both"):
            validate_cpu_allocation(cfg)

    def test_zero_cores_per_server_raises(self):
        cfg = {"cpu_allocation": {"cores_per_server": 0, "cores_per_client": 2}}
        with pytest.raises(ValueError, match="must be positive"):
            validate_cpu_allocation(cfg)

    def test_negative_cores_per_client_raises(self):
        cfg = {"cpu_allocation": {"cores_per_server": 2, "cores_per_client": -1}}
        with pytest.raises(ValueError, match="must be positive"):
            validate_cpu_allocation(cfg)

    def test_valid_cpu_allocation_passes(self):
        cfg = {"cpu_allocation": {"cores_per_server": 4, "cores_per_client": 4}}
        validate_cpu_allocation(cfg)

    def test_old_style_with_both_ranges_calls_validation(self):
        cfg = {"server_cpu_range": "0", "client_cpu_range": "1"}
        validate_cpu_allocation(cfg)

    def test_old_style_with_only_server_range(self):
        cfg = {"server_cpu_range": "0-3"}
        validate_cpu_allocation(cfg)


# ---------------------------------------------------------------------------
# _validate_positive_int_or_list
# ---------------------------------------------------------------------------


class TestValidatePositiveIntOrList:
    def test_valid_int(self):
        _validate_positive_int_or_list(5, "test")

    def test_zero_int_raises(self):
        with pytest.raises(ValueError, match="must be positive"):
            _validate_positive_int_or_list(0, "test")

    def test_negative_int_raises(self):
        with pytest.raises(ValueError, match="must be positive"):
            _validate_positive_int_or_list(-3, "test")

    def test_valid_list(self):
        _validate_positive_int_or_list([1, 2, 3], "test")

    def test_list_with_zero_raises(self):
        with pytest.raises(ValueError, match="must be list of positive integers"):
            _validate_positive_int_or_list([1, 0], "test")

    def test_list_with_negative_raises(self):
        with pytest.raises(ValueError, match="must be list of positive integers"):
            _validate_positive_int_or_list([1, -2], "test")

    def test_list_with_non_int_raises(self):
        with pytest.raises(ValueError, match="must be list of positive integers"):
            _validate_positive_int_or_list([1, 2.5], "test")

    def test_string_raises(self):
        with pytest.raises(ValueError, match="must be int or list"):
            _validate_positive_int_or_list("hello", "test")

    def test_float_raises(self):
        with pytest.raises(ValueError, match="must be int or list"):
            _validate_positive_int_or_list(3.14, "test")


# ---------------------------------------------------------------------------
# validate_test_groups
# ---------------------------------------------------------------------------


class TestValidateTestGroups:
    def test_no_test_groups_key_passes(self):
        validate_test_groups({})

    def test_not_a_list_raises(self):
        with pytest.raises(ValueError, match="must be a non-empty list"):
            validate_test_groups({"test_groups": "not a list"})

    def test_empty_list_raises(self):
        with pytest.raises(ValueError, match="must be a non-empty list"):
            validate_test_groups({"test_groups": []})

    def test_element_not_dict_raises(self):
        with pytest.raises(ValueError, match="must be a dict"):
            validate_test_groups({"test_groups": ["not a dict"]})

    def test_element_missing_scenarios_raises(self):
        with pytest.raises(ValueError, match="missing 'scenarios' field"):
            validate_test_groups({"test_groups": [{"group": 1}]})

    def test_empty_scenarios_raises(self):
        with pytest.raises(ValueError, match="scenarios must be a non-empty list"):
            validate_test_groups({"test_groups": [{"scenarios": []}]})

    def test_scenarios_not_list_raises(self):
        with pytest.raises(ValueError, match="scenarios must be a non-empty list"):
            validate_test_groups({"test_groups": [{"scenarios": "bad"}]})

    def test_valid_test_groups_passes(self):
        cfg = {"test_groups": [{"scenarios": [{"id": "s1", "command": "GET key"}]}]}
        validate_test_groups(cfg)


# ---------------------------------------------------------------------------
# _get_active_ports
# ---------------------------------------------------------------------------


class TestGetActivePorts:
    def test_cluster_mode_with_cluster_ports(self):
        cfg = {"cluster_mode": True, "cluster_ports": [7000, 7001, 7002]}
        assert _get_active_ports(cfg) == [7000, 7001, 7002]

    def test_non_cluster_mode_with_port(self):
        cfg = {"cluster_mode": False, "port": 6380}
        assert _get_active_ports(cfg) == [6380]

    def test_non_cluster_mode_default_port(self):
        cfg = {"cluster_mode": False}
        assert _get_active_ports(cfg) == [6379]

    def test_no_port_key_defaults_to_6379(self):
        assert _get_active_ports({}) == [6379]

    def test_cluster_mode_without_cluster_ports_falls_back(self):
        cfg = {"cluster_mode": True, "port": 6380}
        assert _get_active_ports(cfg) == [6380]
