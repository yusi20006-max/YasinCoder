"""Tool-driven coding-agent facade.

The facade keeps model reasoning separate from side effects: models request
named tools, tools return structured results, and file mutations are dry-run
until explicitly approved with ``apply=True``.
"""
from __future__ import annotations

from core.agent_tools import execute


class CodingAgent:
    def __init__(self, workspace=None):
        self.workspace = workspace
        self.history = []

    def tool(self, name, **payload):
        payload.setdefault("root", self.workspace)
        result = execute(name, payload)
        self.history.append({"tool": name, "result": result})
        return result

    def inspect(self):
        return self.tool("workspace.info")

    def read(self, path):
        return self.tool("file.read", path=path)

    def search(self, pattern):
        return self.tool("search", pattern=pattern)

    def propose_write(self, path, content):
        return self.tool("file.write", path=path, content=content, apply=False)

    def apply_write(self, path, content):
        return self.tool("file.write", path=path, content=content, apply=True)

    def run(self, command, timeout=60):
        return self.tool("shell.exec", command=command, timeout=timeout)

    def git_status(self):
        return self.tool("git.exec", args=["status", "--short"])

    def test(self, command="python -m pytest"):
        return self.tool("test.run", command=command)

    def transcript(self):
        return list(self.history)
