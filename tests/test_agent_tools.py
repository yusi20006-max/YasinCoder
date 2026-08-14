from pathlib import Path

from core.agent_tools import execute, safe_path


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


def test_write_apply_and_read(tmp_path):
    execute("file.write", {"path": "a.txt", "content": "new", "apply": True, "root": str(tmp_path)})
    result = execute("file.read", {"path": "a.txt", "root": str(tmp_path)})
    assert result["ok"] and result["content"] == "new"


def test_unknown_tool_is_structured():
    result = execute("missing.tool")
    assert result == {"ok": False, "tool": "missing.tool", "error": "unknown tool"}
