"""Scoped, persistent AI memory stored outside the repository workspace."""
from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MAX_ITEMS = 200
MAX_ITEM_CHARS = 8_000
MAX_TOTAL_CHARS = 80_000
_SECRET_PATTERNS = (
    re.compile(r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*[^\s,;]+"),
    re.compile(r"\b(?:sk|ghp|github_pat)-[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/=-]{12,}"),
)


def _data_dir() -> Path:
    root = os.environ.get("XDG_DATA_HOME")
    if root:
        return Path(root) / "YasinCoder"
    if os.name == "nt":
        root = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        return Path(root or Path.home() / "AppData" / "Local") / "YasinCoder"
    import platform
    if platform.system().lower() == "darwin":
        return Path.home() / "Library" / "Application Support" / "YasinCoder"
    return Path.home() / ".local" / "share" / "YasinCoder"


def _redact(value: str) -> str:
    value = str(value)
    for pattern in _SECRET_PATTERNS:
        value = pattern.sub(lambda m: f"{m.group(1)}=[REDACTED]" if m.lastindex else "[REDACTED]", value)
    return value


def _scope(scope: str | None) -> str:
    value = (scope or "global").strip()
    if not value or not re.fullmatch(r"[A-Za-z0-9_.:/-]{1,128}", value):
        raise ValueError("invalid memory scope")
    return value


class Memory:
    """Small bounded memory store with explicit scopes and safe persistence."""

    def __init__(self, directory: str | Path | None = None, *, max_items: int = MAX_ITEMS):
        self.directory = Path(directory) if directory else _data_dir() / "memory"
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path = self.directory / "memory.json"
        self.max_items = max(1, min(int(max_items), MAX_ITEMS))
        self.data = self._load()

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"version": 1, "items": []}
        try:
            with self.path.open(encoding="utf-8") as handle:
                data = json.load(handle)
            items = data.get("items", []) if isinstance(data, dict) else []
            return {"version": 1, "items": [self._normalize(x) for x in items if isinstance(x, dict)]}
        except (OSError, json.JSONDecodeError, ValueError):
            return {"version": 1, "items": []}

    def _normalize(self, item: dict[str, Any]) -> dict[str, Any]:
        text = _redact(str(item.get("text", ""))).strip()[:MAX_ITEM_CHARS]
        return {
            "id": str(item.get("id") or os.urandom(8).hex()),
            "scope": _scope(str(item.get("scope") or "global")),
            "text": text,
            "tags": [str(x)[:64] for x in item.get("tags", []) if str(x).strip()][:12],
            "created_at": str(item.get("created_at") or _now()),
            "updated_at": str(item.get("updated_at") or _now()),
        }

    def save(self) -> None:
        self._prune()
        payload = json.dumps(self.data, ensure_ascii=False, indent=2)
        fd, tmp = tempfile.mkstemp(prefix=".memory.", suffix=".tmp", dir=self.directory)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp, self.path)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def add(self, text: str, *, scope: str | None = None, tags: list[str] | None = None) -> dict[str, Any]:
        clean = _redact(text).strip()
        if not clean:
            raise ValueError("memory text must not be empty")
        item = self._normalize({"scope": _scope(scope), "text": clean, "tags": tags or []})
        self.data["items"].append(item)
        self.save()
        return dict(item)

    def update(self, item_id: str, text: str | None = None, *, tags: list[str] | None = None) -> dict[str, Any] | None:
        for item in self.data["items"]:
            if item["id"] == item_id:
                if text is not None:
                    clean = _redact(text).strip()
                    if not clean:
                        raise ValueError("memory text must not be empty")
                    item["text"] = clean[:MAX_ITEM_CHARS]
                if tags is not None:
                    item["tags"] = [str(x)[:64] for x in tags if str(x).strip()][:12]
                item["updated_at"] = _now()
                self.save()
                return dict(item)
        return None

    def forget(self, item_id: str | None = None, *, scope: str | None = None) -> int:
        target_scope = _scope(scope) if scope is not None else None
        before = len(self.data["items"])
        self.data["items"] = [
            x for x in self.data["items"]
            if not ((item_id is None or x["id"] == item_id) and (target_scope is None or x["scope"] == target_scope))
        ]
        removed = before - len(self.data["items"])
        if removed:
            self.save()
        return removed

    def list(self, *, scope: str | None = None) -> list[dict[str, Any]]:
        target = _scope(scope) if scope is not None else None
        return [dict(x) for x in self.data["items"] if target is None or x["scope"] == target]

    def retrieve(self, query: str, *, scope: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
        terms = {t.lower() for t in re.findall(r"\w+", query) if len(t) > 1}
        items = self.list(scope=scope)
        scored: list[tuple[int, dict[str, Any]]] = []
        for item in items:
            haystack = f"{item['text']} {' '.join(item['tags'])}".lower()
            score = sum(1 for term in terms if term in haystack)
            if score:
                scored.append((score, item))
        scored.sort(key=lambda pair: (pair[0], pair[1]["updated_at"]), reverse=True)
        return [item for _, item in scored[: max(1, min(int(limit), 50))]]

    def clear(self, *, scope: str | None = None) -> int:
        return self.forget(scope=scope)

    def _prune(self) -> None:
        items = self.data["items"][-self.max_items:]
        total = 0
        kept: list[dict[str, Any]] = []
        for item in reversed(items):
            size = len(item.get("text", ""))
            if total + size > MAX_TOTAL_CHARS and kept:
                continue
            kept.append(item)
            total += size
        self.data["items"] = list(reversed(kept))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
