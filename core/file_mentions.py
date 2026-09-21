"""Safe project file mentions and bounded context expansion for YasinCoder."""

from __future__ import annotations

import re
from pathlib import Path

MENTION_RE = re.compile(r"(?<!\w)@([^\s@]+)")
MAX_FILES = 8
MAX_FILE_BYTES = 64_000
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", ".yasin"}


def _root(root: Path) -> Path:
    return root.resolve()


def resolve_mention(value: str, root: Path) -> Path | None:
    candidate = value.strip().strip("'\"").replace("\\", "/")
    if not candidate or candidate.startswith("/") or candidate.startswith("~"):
        return None
    base = _root(root)
    path = (base / candidate).resolve()
    try:
        path.relative_to(base)
    except ValueError:
        return None
    if not path.is_file():
        return None
    return path


def mentions(text: str, root: Path) -> list[Path]:
    found: list[Path] = []
    seen: set[Path] = set()
    for raw in MENTION_RE.findall(text):
        path = resolve_mention(raw.rstrip(",.;:!?)]}"), root)
        if path and path not in seen:
            found.append(path)
            seen.add(path)
        if len(found) >= MAX_FILES:
            break
    return found


def complete(prefix: str, root: Path) -> list[str]:
    """Complete a relative file path for an @mention prefix."""
    if not prefix.startswith("@"):
        return []
    partial = prefix[1:]
    base = _root(root)
    parent = (base / partial).parent if "/" in partial else base
    fragment = (base / partial).name if "/" in partial else partial
    try:
        parent = parent.resolve()
        parent.relative_to(base)
    except ValueError:
        return []
    if not parent.is_dir():
        return []
    results = []
    for path in sorted(parent.iterdir(), key=lambda p: p.name.lower()):
        if path.name.startswith(fragment) and path.name not in SKIP_DIRS:
            rel = path.relative_to(base).as_posix()
            results.append("@" + rel + ("/" if path.is_dir() else ""))
        if len(results) >= 8:
            break
    return results


def context_preview(paths: list[Path], root: Path) -> list[str]:
    base = _root(root)
    lines = []
    for path in paths:
        try:
            size = path.stat().st_size
            rel = path.relative_to(base).as_posix()
            if size > MAX_FILE_BYTES:
                lines.append(f"@{rel} — skipped (file exceeds {MAX_FILE_BYTES} bytes)")
            else:
                lines.append(f"@{rel} — {size} bytes")
        except OSError:
            lines.append(f"@{path} — unavailable")
    return lines


def enrich_prompt(prompt: str, root: Path) -> tuple[str, list[Path]]:
    paths = mentions(prompt, root)
    if not paths:
        return prompt, []
    chunks = [prompt, "", "Referenced project files:"]
    base = _root(root)
    for path in paths:
        try:
            rel = path.relative_to(base).as_posix()
            data = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if len(data.encode("utf-8")) > MAX_FILE_BYTES:
            continue
        chunks.extend([f"\n--- {rel} ---", data])
    return "\n".join(chunks), paths
