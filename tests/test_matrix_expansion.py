"""Unit tests for expand_matrix() in benchmark.py."""

import copy

from benchmark import expand_matrix


class TestNoMatrix:
    """Tests for groups without a matrix field."""

    def test_no_matrix_passthrough(self):
        """Group without matrix key is returned unchanged."""
        group = {"scenarios": [{"id": "set", "command": "SET"}]}
        result = expand_matrix(group)
        assert result["scenarios"] == group["scenarios"]

    def test_empty_matrix_passthrough(self):
        """Group with empty matrix dict is returned unchanged."""
        group = {"scenarios": [{"id": "get", "command": "GET"}], "matrix": {}}
        result = expand_matrix(group)
        assert result["scenarios"] == group["scenarios"]
        assert "matrix" not in result


class TestCartesianExpansion:
    """Tests for Cartesian product expansion."""

    def test_single_dimension_expansion(self):
        """1 scenario x 2 data_sizes = 2 expanded scenarios."""
        group = {
            "scenarios": [{"id": "set", "command": "SET"}],
            "matrix": {"data_size": [16, 64]},
        }
        result = expand_matrix(group)
        assert len(result["scenarios"]) == 2
        assert result["scenarios"][0]["data_size"] == 16
        assert result["scenarios"][1]["data_size"] == 64

    def test_multi_dimension_cartesian_product(self):
        """2 scenarios x 2 data_sizes x 2 pipelines = 8 expanded scenarios."""
        group = {
            "scenarios": [
                {"id": "set", "command": "SET"},
                {"id": "get", "command": "GET"},
            ],
            "matrix": {"data_size": [16, 64], "pipeline": [1, 10]},
        }
        result = expand_matrix(group)
        assert len(result["scenarios"]) == 8

    def test_multiple_scenarios_each_expanded(self):
        """3 scenarios x 2 data_sizes = 6 expanded scenarios."""
        group = {
            "scenarios": [
                {"id": "a", "command": "A"},
                {"id": "b", "command": "B"},
                {"id": "c", "command": "C"},
            ],
            "matrix": {"data_size": [16, 64]},
        }
        result = expand_matrix(group)
        assert len(result["scenarios"]) == 6


class TestOverrideAndFields:
    """Tests for scenario override precedence and field preservation."""

    def test_scenario_override_takes_precedence(self):
        """Explicit scenario-level data_size=32 is kept over matrix values."""
        group = {
            "scenarios": [{"id": "set", "command": "SET", "data_size": 32}],
            "matrix": {"data_size": [16, 64]},
        }
        result = expand_matrix(group)
        assert all(s["data_size"] == 32 for s in result["scenarios"])

    def test_expansion_preserves_all_scenario_fields(self):
        """All original scenario fields are preserved in expanded scenarios."""
        group = {
            "scenarios": [
                {"id": "set", "command": "SET foo bar", "type": "write", "warmup": 5}
            ],
            "matrix": {"data_size": [16]},
        }
        result = expand_matrix(group)
        s = result["scenarios"][0]
        assert s["command"] == "SET foo bar"
        assert s["type"] == "write"
        assert s["warmup"] == 5


class TestIdSuffix:
    """Tests for auto-generated ID suffixes."""

    def test_id_suffix_generation(self):
        """IDs contain matrix key prefixes and values."""
        group = {
            "scenarios": [{"id": "set"}],
            "matrix": {
                "data_size": [16],
                "pipeline": [1],
                "clients": [50],
                "keyspacelen": [10000000],
            },
        }
        result = expand_matrix(group)
        assert result["scenarios"][0]["id"] == "set_d16_p1_c50_k10000000"


class TestImmutability:
    """Tests that the original group is not mutated."""

    def test_original_group_not_mutated(self):
        """expand_matrix does not modify the input dict."""
        group = {
            "scenarios": [{"id": "set", "command": "SET"}],
            "matrix": {"data_size": [16, 64]},
        }
        original = copy.deepcopy(group)
        expand_matrix(group)
        assert group == original
