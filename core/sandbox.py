"""Workspace confinement and bounded subprocess primitives."""
from __future__ import annotations

import os
import signal
import subprocess
import tempfile
import threading
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
        list(command),
        cwd=str(cwd),
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False,
        start_new_session=True,
    )

    stdout_chunks: list[bytes] = []
    stderr_chunks: list[bytes] = []
    captured = {"stdout": 0, "stderr": 0}
    lock = threading.Lock()

    def drain(stream, chunks, key: str) -> None:
        if stream is None:
            return
        while True:
            chunk = stream.read(65536)
            if not chunk:
                return
            with lock:
                remaining = max_output_bytes - captured[key]
                if remaining > 0:
                    keep = chunk[:remaining]
                    chunks.append(keep)
                    captured[key] += len(keep)

    stdout_thread = threading.Thread(
        target=drain, args=(process.stdout, stdout_chunks, "stdout"), daemon=True
    )
    stderr_thread = threading.Thread(
        target=drain, args=(process.stderr, stderr_chunks, "stderr"), daemon=True
    )
    stdout_thread.start()
    stderr_thread.start()

    timed_out = False
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()

    stdout_thread.join(timeout=2)
    stderr_thread.join(timeout=2)
    if stdout_thread.is_alive() or stderr_thread.is_alive():
        raise RuntimeError("bounded process output reader did not terminate")

    stdout = b"".join(stdout_chunks)
    stderr = b"".join(stderr_chunks)
    output_limited = captured["stdout"] + captured["stderr"] >= max_output_bytes
    return {
        "ok": process.returncode == 0 and not timed_out and not output_limited,
        "returncode": process.returncode,
        "stdout": stdout.decode("utf-8", errors="replace"),
        "stderr": stderr.decode("utf-8", errors="replace"),
        "timed_out": timed_out,
        "output_limited": output_limited,
        **({"error": "command output exceeded configured limit"} if output_limited else {}),
        **({"error": "command timed out and process group was terminated"} if timed_out else {}),
    }
