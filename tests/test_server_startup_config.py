"""Tests for server_startup_config support in _build_server_command."""

import pytest

from valkey_server import ServerLauncher

LOG_FILE = "/tmp/test.log"


@pytest.fixture
def launcher():
    sl = ServerLauncher(results_dir="/tmp", valkey_path="/tmp/valkey")
    sl.config = None
    sl.modules = []
    return sl


def _build(launcher, server_startup_config=None):
    return launcher._build_server_command(
        port=6379,
        bind_ip=None,
        cpu_range=None,
        tls_mode=False,
        cluster_mode=False,
        io_threads=None,
        module_path=None,
        log_file=LOG_FILE,
        server_startup_config=server_startup_config,
    )


def test_build_server_command_default_without_startup_config(launcher):
    cmd = _build(launcher)
    assert "--maxmemory-policy" in cmd
    assert cmd[cmd.index("--maxmemory-policy") + 1] == "allkeys-lru"
    assert "--appendonly" in cmd
    assert cmd[cmd.index("--appendonly") + 1] == "no"
    assert "--protected-mode" in cmd
    assert cmd[cmd.index("--protected-mode") + 1] == "no"
    assert "--save" in cmd
    assert cmd[cmd.index("--save") + 1] == "''"


def test_build_server_command_override_default(launcher):
    cmd = _build(launcher, {"maxmemory-policy": "volatile-lfu"})
    assert cmd[cmd.index("--maxmemory-policy") + 1] == "volatile-lfu"
    # Other defaults still present
    assert cmd[cmd.index("--appendonly") + 1] == "no"


def test_build_server_command_add_new_param(launcher):
    cmd = _build(launcher, {"maxmemory": "1gb"})
    assert "--maxmemory" in cmd
    assert cmd[cmd.index("--maxmemory") + 1] == "1gb"
    # Defaults still present
    assert cmd[cmd.index("--maxmemory-policy") + 1] == "allkeys-lru"


def test_build_server_command_override_and_add(launcher):
    cmd = _build(launcher, {"maxmemory-policy": "volatile-lfu", "maxmemory": "1gb"})
    assert cmd[cmd.index("--maxmemory-policy") + 1] == "volatile-lfu"
    assert cmd[cmd.index("--maxmemory") + 1] == "1gb"
    assert cmd[cmd.index("--appendonly") + 1] == "no"


def test_build_server_command_no_mutation(launcher):
    original = {"maxmemory": "1gb"}
    original_copy = original.copy()
    _build(launcher, original)
    assert original == original_copy
