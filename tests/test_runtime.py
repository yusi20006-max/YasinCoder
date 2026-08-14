import os
import platform
import sys
from pathlib import Path

from core.runtime import (
    cache_dir,
    command_available,
    config_dir,
    detect_runtime,
    find_command,
    run_command,
    user_data_dir,
)


def test_runtime_detection_is_normalized():
    runtime = detect_runtime()
    assert runtime.system
    assert runtime.python
    assert runtime.family in {"termux", "wsl", "windows", "linux", "macos", "other"}


def test_user_directories_are_path_objects():
    assert isinstance(user_data_dir(), Path)
    assert isinstance(config_dir(), Path)
    assert isinstance(cache_dir(), Path)


def test_command_discovery_matches_path():
    python_name = "python" if os.name != "nt" else "python.exe"
    path = find_command(python_name) or find_command(Path(sys.executable).name)
    assert path
    assert command_available(python_name, Path(sys.executable).name)


def test_run_command_does_not_require_shell():
    result = run_command([sys.executable, "-c", "print('runtime-ok')"])
    assert result.returncode == 0
    assert result.stdout.strip() == "runtime-ok"


def test_missing_command_is_reported_cleanly():
    assert find_command("__yasin_command_that_should_not_exist__") is None
