from pathlib import Path

from core.agent_tools import execute
from core.permissions import PermissionPolicy
from core.sandbox import safe_path


READ_ONLY = PermissionPolicy().as_dict()
WRITE_POLICY = PermissionPolicy(write=True).as_dict()
EXEC_POLICY = PermissionPolicy(execute=True).as_dict()
GIT_POLICY = PermissionPolicy(git=True).as_dict()


def test_workspace_confinement(tmp_path):
    assert safe_path("src/main.py", tmp_path).is_relative_to(tmp_path.resolve())
    try:
        safe_path("../escape.txt", tmp_path)
    except RuntimeError:
        pass
    else:
        raise AssertionError("workspace escape was not rejected")


def test_write_defaults_to_dry_run(tmp_path):
    result = execute("file.write", {"path": "a.txt", "content": "new", "root": str(tmp_path)})
    assert result["ok"] and result["applied"] is False
    assert not (tmp_path / "a.txt").exists()


def test_write_apply_requires_explicit_permission(tmp_path):
    denied = execute("file.write", {"path": "a.txt", "content": "new", "apply": True, "root": str(tmp_path)})
    assert denied["ok"] is False and "write" in denied["error"]
    assert not (tmp_path / "a.txt").exists()


def test_write_apply_and_read(tmp_path):
    execute("file.write", {"path": "a.txt", "content": "new", "apply": True, "root": str(tmp_path), "permissions": WRITE_POLICY})
    result = execute("file.read", {"path": "a.txt", "root": str(tmp_path), "permissions": READ_ONLY})
    assert result["ok"] and result["content"] == "new"


def test_shell_requires_execute_permission(tmp_path):
    denied = execute("shell.exec", {"command": "python -c 'print(1)'", "root": str(tmp_path)})
    assert denied["ok"] is False and "execute" in denied["error"]
    allowed = execute("shell.exec", {"command": "python -c 'print(1)'", "root": str(tmp_path), "permissions": EXEC_POLICY})
    assert allowed["ok"] and allowed["stdout"].strip() == "1"


def test_network_and_admin_commands_are_separate_capabilities(tmp_path):
    network = execute("shell.exec", {"command": "curl https://example.com", "root": str(tmp_path), "permissions": EXEC_POLICY})
    assert network["ok"] is False and "network" in network["error"]
    admin = execute("shell.exec", {"command": "sudo true", "root": str(tmp_path), "permissions": EXEC_POLICY})
    assert admin["ok"] is False and "admin" in admin["error"]


def test_git_requires_git_permission(tmp_path):
    denied = execute("git.exec", {"args": ["status"], "root": str(tmp_path)})
    assert denied["ok"] is False and "git" in denied["error"]


def test_unknown_tool_is_structured():
    result = execute("missing.tool")
    assert result == {"ok": False, "tool": "missing.tool", "error": "unknown tool"}
