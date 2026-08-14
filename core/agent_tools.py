"""Explicit coding-agent tools with workspace confinement and permissions."""
from __future__ import annotations

import json
import shlex
import subprocess
from pathlib import Path
from typing import Any

from .permissions import PermissionDenied, PermissionPolicy
from .sandbox import SandboxViolation, run_process, safe_path


NETWORK_COMMANDS = {
    "curl", "wget", "nc", "netcat", "ssh", "scp", "sftp", "ftp",
    "telnet", "ping", "nslookup", "dig", "host", "git-clone",
}
ADMIN_COMMANDS = {
    "sudo", "su", "mount", "umount", "iptables", "nft", "useradd",
    "userdel", "passwd", "chown", "chmod", "pkill", "killall",
}
GIT_COMMANDS = {"git"}


def _policy(payload: dict[str, Any]) -> PermissionPolicy:
    value = payload.get("permissions")
    if isinstance(value, PermissionPolicy):
        return value
    return PermissionPolicy.from_mapping(value)


def _root(payload: dict[str, Any]) -> Path:
    root = payload.get("root") or Path.cwd()
    return Path(root).expanduser().resolve()


def _audit(tool: str, capability: str, ok: bool, **extra: Any) -> dict[str, Any]:
    entry = {"tool": tool, "capability": capability, "ok": ok}
    entry.update(extra)
    return entry


def _denied(tool: str, capability: str) -> dict[str, Any]:
    return {"ok": False, "tool": tool, "error": str(PermissionDenied(capability)), "audit": _audit(tool, capability, False)}


def _require(policy: PermissionPolicy, tool: str, capability: str) -> dict[str, Any] | None:
    if not policy.allows(capability):
        return _denied(tool, capability)
    return None


def _workspace_info(root: Path) -> dict[str, Any]:
    return {"ok": True, "tool": "workspace.info", "root": str(root), "exists": root.exists(), "audit": _audit("workspace.info", "read", True)}


def _file_read(payload: dict[str, Any], root: Path) -> dict[str, Any]:
    denied = _require(_policy(payload), "file.read", "read")
    if denied:
        return denied
    path = safe_path(payload["path"], root)
    if not path.is_file():
        return {"ok": False, "tool": "file.read", "error": "file not found", "audit": _audit("file.read", "read", False)}
    content = path.read_text(encoding="utf-8")
    return {"ok": True, "tool": "file.read", "path": str(path), "content": content, "audit": _audit("file.read", "read", True)}


def _file_write(payload: dict[str, Any], root: Path) -> dict[str, Any]:
    policy = _policy(payload)
    path = safe_path(payload["path"], root)
    content = str(payload.get("content", ""))
    if not payload.get("apply", False):
        return {"ok": True, "tool": "file.write", "path": str(path), "applied": False, "content": content, "audit": _audit("file.write", "write", True, applied=False)}
    denied = _require(policy, "file.write", "write")
    if denied:
        return denied
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return {"ok": True, "tool": "file.write", "path": str(path), "applied": True, "audit": _audit("file.write", "write", True, applied=True)}


def _search(payload: dict[str, Any], root: Path) -> dict[str, Any]:
    denied = _require(_policy(payload), "search", "read")
    if denied:
        return denied
    pattern = str(payload.get("pattern", ""))
    try:
        result = subprocess.run(["rg", "--line-number", "--hidden", "--glob", "!.git", pattern, str(root)], capture_output=True, text=True, timeout=15)
        return {"ok": result.returncode in (0, 1), "tool": "search", "output": result.stdout, "error": result.stderr, "audit": _audit("search", "read", result.returncode in (0, 1))}
    except (FileNotFoundError, subprocess.TimeoutExpired):
        matches = []
        for path in root.rglob("*"):
            if not path.is_file() or ".git" in path.parts:
                continue
            try:
                for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                    if pattern in line:
                        matches.append(f"{path}:{index}:{line}")
            except (UnicodeDecodeError, OSError):
                continue
        return {"ok": True, "tool": "search", "output": "\n".join(matches), "fallback": True, "audit": _audit("search", "read", True, fallback=True)}


def _shell(payload: dict[str, Any], root: Path, tool_name: str = "shell.exec") -> dict[str, Any]:
    policy = _policy(payload)
    command = str(payload.get("command", "")).strip()
    if not command:
        return {"ok": False, "tool": tool_name, "error": "empty command", "audit": _audit(tool_name, "execute", False)}
    try:
        argv = shlex.split(command)
    except ValueError as exc:
        return {"ok": False, "tool": tool_name, "error": str(exc), "audit": _audit(tool_name, "execute", False)}
    if not argv:
        return {"ok": False, "tool": tool_name, "error": "empty command", "audit": _audit(tool_name, "execute", False)}
    executable = Path(argv[0]).name.lower()
    if executable in GIT_COMMANDS:
        capability = "git"
    elif executable in NETWORK_COMMANDS:
        capability = "network"
    elif executable in ADMIN_COMMANDS:
        capability = "admin"
    else:
        capability = "execute"
    denied = _require(policy, tool_name, capability)
    if denied:
        return denied
    result = run_process(argv, cwd=root, timeout=float(payload.get("timeout", 60)))
    result.update({"tool": tool_name, "command": command, "audit": _audit(tool_name, capability, bool(result.get("ok")))})
    return result


def execute(name: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = dict(payload or {})
    root = _root(payload)
    try:
        if name == "workspace.info":
            return _workspace_info(root)
        if name == "file.read":
            return _file_read(payload, root)
        if name == "file.write":
            return _file_write(payload, root)
        if name == "search":
            return _search(payload, root)
        if name == "shell.exec":
            return _shell(payload, root)
        if name == "git.exec":
            payload["command"] = "git " + " ".join(shlex.quote(str(x)) for x in payload.get("args", []))
            return _shell(payload, root, "git.exec")
        if name == "test.run":
            return _shell(payload, root, "test.run")
        return {"ok": False, "tool": name, "error": "unknown tool"}
    except (KeyError, SandboxViolation, OSError, UnicodeError, ValueError) as exc:
        return {"ok": False, "tool": name, "error": str(exc), "audit": _audit(name, "read", False)}
