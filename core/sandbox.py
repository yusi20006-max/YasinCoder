"""Workspace confinement and safe subprocess primitives."""
from __future__ import annotations

import os
import signal
import subprocess
from pathlib import Path
from typing import Sequence


class SandboxViolation(RuntimeError):
    """Raised when an operation attempts to leave the configured workspace."""


def safe_path(path: str | os.PathLike[str], root: str | os.PathLike[str]) -> Path:
    """Resolve *path* under *root* and reject traversal/symlink escapes."""
    root_path = Path(root).expanduser().resolve()
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = root_path / candidate
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(root_path)
    except ValueError as exc:
        raise SandboxViolation("workspace escape rejected") from exc
    return resolved


def run_process(
    command: Sequence[str],
    *,
    cwd: Path,
    timeout: float = 60,
    env: dict[str, str] | None = None,
) -> dict[str, object]:
    """Run a bounded process and terminate its whole process group on timeout."""
    if timeout <= 0 or timeout > 3600:
        raise ValueError("timeout must be between 0 and 3600 seconds")
    process = subprocess.Popen(
        list(command),
        cwd=str(cwd),
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
        return {
            "ok": process.returncode == 0,
            "returncode": process.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "timed_out": False,
        }
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGTERM)
            process.communicate(timeout=2)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.communicate()
        return {
            "ok": False,
            "returncode": process.returncode,
            "stdout": process.stdout.read() if process.stdout else "",
            "stderr": process.stderr.read() if process.stderr else "",
            "timed_out": True,
            "error": "command timed out and process group was terminated",
        }
