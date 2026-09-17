"""Workspace confinement and bounded subprocess primitives."""
from __future__ import annotations

import os
import signal
import subprocess
import tempfile
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


def secure_tempdir(prefix: str = "yasincoder-") -> tempfile.TemporaryDirectory[str]:
    """Create a private temporary directory that is removed on context exit."""
    return tempfile.TemporaryDirectory(prefix=prefix, ignore_cleanup_errors=False)


def run_process(
    command: Sequence[str],
    *,
    cwd: Path,
    timeout: float = 60,
    env: dict[str, str] | None = None,
    max_output_bytes: int = 1_048_576,
) -> dict[str, object]:
    """Run a bounded process and terminate its whole process group on limits."""
    if timeout <= 0 or timeout > 3600:
        raise ValueError("timeout must be between 0 and 3600 seconds")
    if max_output_bytes < 1024 or max_output_bytes > 16 * 1024 * 1024:
        raise ValueError("max_output_bytes must be between 1024 and 16777216")
    if not command:
        raise ValueError("command must not be empty")
    cwd = Path(cwd).expanduser().resolve()
    if not cwd.is_dir():
        raise SandboxViolation("working directory does not exist")
    process = subprocess.Popen(
        list(command), cwd=str(cwd), env=env, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=False, start_new_session=True,
    )
    timed_out = False
    output_limited = False
    try:
        stdout_b, stderr_b = process.communicate(timeout=timeout)
        if len(stdout_b) + len(stderr_b) > max_output_bytes:
            output_limited = True
            keep = max_output_bytes // 2
            stdout_b, stderr_b = stdout_b[:keep], stderr_b[:keep]
        stdout = stdout_b.decode("utf-8", errors="replace")
        stderr = stderr_b.decode("utf-8", errors="replace")
        return {
            "ok": process.returncode == 0 and not output_limited,
            "returncode": process.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "timed_out": False,
            "output_limited": output_limited,
            **({"error": "command output exceeded configured limit"} if output_limited else {}),
        }
    except subprocess.TimeoutExpired:
        timed_out = True
        try:
            os.killpg(process.pid, signal.SIGTERM)
            process.communicate(timeout=2)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.communicate()
        stdout = (process.stdout.read() if process.stdout else b"")
        stderr = (process.stderr.read() if process.stderr else b"")
        if len(stdout) + len(stderr) > max_output_bytes:
            keep = max_output_bytes // 2
            stdout, stderr = stdout[:keep], stderr[:keep]
            output_limited = True
        return {
            "ok": False,
            "returncode": process.returncode,
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
            "timed_out": timed_out,
            "output_limited": output_limited,
            "error": "command timed out and process group was terminated",
        }
