"""Deterministic, source-only documentation and project reporting.

The generator intentionally avoids importing application modules or reading runtime
state. Only source files and selected git metadata are inspected.
"""
from __future__ import annotations

import ast
import json
import os
import re
import subprocess
from pathlib import Path

GENERATED_DIR = Path("docs/generated")
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "build", "dist", ".pytest_cache", ".mypy_cache"}
SKIP_FILES = {".env", ".env.local", ".env.production", "models.json", "index.json"}
SECRET_RE = re.compile(r"(?i)(api[_-]?key|token|secret|password|authorization)\s*[:=]\s*[^\s,}]+")


def _safe_path(path: Path) -> bool:
    return not any(part in SKIP_DIRS for part in path.parts) and path.name not in SKIP_FILES


def source_files(root: str | os.PathLike[str] = ".") -> list[Path]:
    base = Path(root).resolve()
    files = [p for p in base.rglob("*.py") if _safe_path(p.relative_to(base))]
    return sorted(files, key=lambda p: p.relative_to(base).as_posix())


def _parse(path: Path) -> ast.Module | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, UnicodeDecodeError, SyntaxError):
        return None


def _doc(node: ast.AST) -> str:
    text = ast.get_docstring(node) or ""
    return " ".join(text.split())


def analyze(root: str | os.PathLike[str] = ".") -> list[dict]:
    base = Path(root).resolve()
    records: list[dict] = []
    for path in source_files(base):
        tree = _parse(path)
        if tree is None:
            continue
        rel = path.relative_to(base).as_posix()
        classes = []
        functions = []
        imports = []
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                classes.append({"name": node.name, "doc": _doc(node)})
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append({"name": node.name, "async": isinstance(node, ast.AsyncFunctionDef), "doc": _doc(node)})
            elif isinstance(node, ast.Import):
                imports.extend(sorted(alias.name for alias in node.names))
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or ".")
        records.append({
            "path": rel,
            "lines": len(path.read_text(encoding="utf-8").splitlines()),
            "classes": classes,
            "functions": functions,
            "imports": sorted(set(imports)),
            "module_doc": _doc(tree),
        })
    return records


def api_markdown(records: list[dict]) -> str:
    lines = ["# API Reference", "", "Generated deterministically from Python source. No application modules are imported.", ""]
    for item in records:
        lines += [f"## `{item['path']}`", ""]
        if item["module_doc"]:
            lines += [item["module_doc"], ""]
        if item["classes"]:
            lines += ["### Classes", ""]
            for cls in item["classes"]:
                suffix = f" — {cls['doc']}" if cls["doc"] else ""
                lines.append(f"- `{cls['name']}`{suffix}")
            lines.append("")
        if item["functions"]:
            lines += ["### Functions", ""]
            for fn in item["functions"]:
                prefix = "async " if fn["async"] else ""
                suffix = f" — {fn['doc']}" if fn["doc"] else ""
                lines.append(f"- `{prefix}{fn['name']}`{suffix}")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def architecture_markdown(records: list[dict]) -> str:
    lines = ["# Architecture", "", "Source-derived module map. Imports are reported as declared, without executing code.", "", "```mermaid", "flowchart TD"]
    nodes: list[str] = []
    edges: list[str] = []
    for i, item in enumerate(records):
        node = f"N{i}"
        label = item["path"].replace('"', "'")
        nodes.append(f'    {node}["{label}"]')
        for imported in item["imports"]:
            target = next((j for j, r in enumerate(records) if r["path"] == imported or r["path"].startswith(imported.replace('.', '/') + "/")), None)
            if target is not None and target != i:
                edges.append(f"    N{i} --> N{target}")
    lines += nodes + edges + ["```", "", "## Module inventory", "", "| Module | Lines | Classes | Functions | Imports |", "|---|---:|---:|---:|---:|"]
    for item in records:
        lines.append(f"| `{item['path']}` | {item['lines']} | {len(item['classes'])} | {len(item['functions'])} | {len(item['imports'])} |")
    return "\n".join(lines) + "\n"


def _git(args: list[str], root: Path) -> str:
    try:
        result = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, timeout=10, check=False)
        return result.stdout.strip() if result.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def changed_files(root: str | os.PathLike[str] = ".", base_ref: str = "HEAD^", head_ref: str = "HEAD") -> list[dict]:
    base = Path(root).resolve()
    output = _git(["diff", "--name-status", base_ref, head_ref, "--", "."], base)
    result = []
    for line in output.splitlines():
        parts = line.split("\t", 1)
        if len(parts) != 2 or not _safe_path(Path(parts[1])):
            continue
        result.append({"status": parts[0], "path": parts[1]})
    return sorted(result, key=lambda x: (x["path"], x["status"]))


def report(records: list[dict], changes: list[dict] | None = None) -> dict:
    return {
        "version": 1,
        "files": len(records),
        "lines": sum(x["lines"] for x in records),
        "classes": sum(len(x["classes"]) for x in records),
        "functions": sum(len(x["functions"]) for x in records),
        "imports": sum(len(x["imports"]) for x in records),
        "changed": changes or [],
    }


def _redact(text: str) -> str:
    return SECRET_RE.sub(lambda m: m.group(1) + "=<redacted>", text)


def render(kind: str, root: str = ".", base_ref: str = "HEAD^") -> str:
    records = analyze(root)
    if kind == "api":
        return _redact(api_markdown(records))
    if kind == "architecture":
        return _redact(architecture_markdown(records))
    if kind == "changes":
        return _redact(json.dumps(changed_files(root, base_ref), indent=2, sort_keys=True) + "\n")
    if kind == "report":
        return _redact(json.dumps(report(records, changed_files(root, base_ref)), indent=2, sort_keys=True) + "\n")
    raise ValueError(f"unsupported documentation kind: {kind}")


def write_generated(root: str = ".", base_ref: str = "HEAD^") -> list[Path]:
    base = Path(root).resolve()
    out = base / GENERATED_DIR
    out.mkdir(parents=True, exist_ok=True)
    outputs = {
        "api": "api.md",
        "architecture": "architecture.md",
        "report": "report.json",
        "changes": "changes.json",
    }
    written = []
    for kind, filename in outputs.items():
        path = out / filename
        content = render(kind, str(base), base_ref)
        path.write_text(content, encoding="utf-8")
        written.append(path)
    return written
