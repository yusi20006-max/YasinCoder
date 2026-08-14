"""Cross-platform runtime discovery and process helpers.

The core project must not assume Termux, a POSIX shell, or developer-specific
filesystem paths. Platform-specific behavior is kept behind this module.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence


@dataclass(frozen=True)
class RuntimeInfo:
    """Normalized runtime information exposed to the rest of the application."""

    system: str
    release: str
    machine: str
    python: str
    is_termux: bool
    is_wsl: bool

    @property
    def family(self) -> str:
        if self.is_termux:
            return "termux"
        if self.is_wsl:
            return "wsl"
        system = self.system.lower()
        if system == "windows":
            return "windows"
        if system == "darwin":
            return "macos"
        if system == "linux":
            return "linux"
        return "other"


def detect_runtime() -> RuntimeInfo:
    """Detect the host without requiring a specific OS or shell."""

    system = platform.system()
    is_termux = bool(os.environ.get("TERMUX_VERSION")) or "com.termux" in os.environ.get(
        "PREFIX", ""
    )
    is_wsl = system == "Linux" and "microsoft" in platform.release().lower()
    return RuntimeInfo(
        system=system,
        release=platform.release(),
        machine=platform.machine(),
        python=platform.python_version(),
        is_termux=is_termux,
        is_wsl=is_wsl,
    )


def user_data_dir(app_name: str = "YasinCoder") -> Path:
    """Return a writable per-user data directory using native OS conventions."""

    runtime = detect_runtime()
    if runtime.system == "Windows":
        root = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA")
        base = Path(root) if root else Path.home() / "AppData" / "Roaming"
    elif runtime.system == "Darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / app_name


def config_dir(app_name: str = "YasinCoder") -> Path:
    """Return a native per-user configuration directory."""

    runtime = detect_runtime()
    if runtime.system == "Windows":
        root = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA")
        base = Path(root) if root else Path.home() / "AppData" / "Roaming"
    elif runtime.system == "Darwin":
        base = Path.home() / "Library" / "Preferences"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / app_name


def cache_dir(app_name: str = "YasinCoder") -> Path:
    """Return a native per-user cache directory."""

    runtime = detect_runtime()
    if runtime.system == "Windows":
        root = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        base = Path(root) if root else Path.home() / "AppData" / "Local"
    elif runtime.system == "Darwin":
        base = Path.home() / "Library" / "Caches"
    else:
        base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    return base / app_name


def find_command(name: str) -> str | None:
    """Find an executable through PATH without assuming a shell."""

    return shutil.which(name)


def command_available(*names: str) -> bool:
    """Return true when at least one candidate executable is available."""

    return any(find_command(name) for name in names)


def run_command(
    args: Sequence[str],
    *,
    cwd: str | os.PathLike[str] | None = None,
    env: Mapping[str, str] | None = None,
    timeout: float | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a program directly, never through shell=True."""

    if not args:
        raise ValueError("args must not be empty")
    return subprocess.run(
        list(args),
        cwd=cwd,
        env=dict(env) if env is not None else None,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
        shell=False,
    )
