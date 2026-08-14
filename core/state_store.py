"""Durable, repository-independent state for YasinCoder.

State lives under a user data directory (override with YASIN_CODER_DATA_DIR)
and is never written into the checked-out project. SQLite is used so projects,
sessions, tasks and memories survive process restarts without extra dependencies.
"""
from __future__ import annotations

import json
import os
import shutil
import sqlite3
import tempfile
import time
from pathlib import Path
from typing import Any, Iterable


APP_DIR = "yasin-coder"


def default_data_dir() -> Path:
    override = os.environ.get("YASIN_CODER_DATA_DIR")
    if override:
        return Path(override).expanduser()
    if os.name == "nt":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    elif os.environ.get("XDG_DATA_HOME"):
        base = os.environ["XDG_DATA_HOME"]
    else:
        base = os.path.expanduser("~/.local/share")
    return Path(base) / APP_DIR


class StateStore:
    """Persistent state with atomic backups before mutating operations."""

    def __init__(self, data_dir: str | os.PathLike[str] | None = None):
        self.data_dir = Path(data_dir).expanduser() if data_dir else default_data_dir()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir = self.data_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        self.db_path = self.data_dir / "state.sqlite3"
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._init_schema()

    def close(self) -> None:
        self._conn.close()

    def _init_schema(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                root TEXT NOT NULL,
                metadata TEXT NOT NULL DEFAULT '{}',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                title TEXT NOT NULL DEFAULT '',
                state TEXT NOT NULL DEFAULT '{}',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                metadata TEXT NOT NULL DEFAULT '{}',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                content TEXT NOT NULL,
                metadata TEXT NOT NULL DEFAULT '{}',
                created_at REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_sessions_project ON sessions(project_id);
            CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project_id);
            CREATE INDEX IF NOT EXISTS idx_memory_project ON memories(project_id);
            """
        )
        self._conn.commit()

    def backup(self) -> Path:
        """Create a consistent SQLite backup and return its path."""
        stamp = time.strftime("%Y%m%d-%H%M%S")
        target = self.backup_dir / f"state-{stamp}-{time.time_ns() % 1000000:06d}.sqlite3"
        dst = sqlite3.connect(target)
        try:
            self._conn.backup(dst)
            dst.commit()
        finally:
            dst.close()
        return target

    @staticmethod
    def _json(value: dict[str, Any] | None) -> str:
        return json.dumps(value or {}, ensure_ascii=False, sort_keys=True)

    @staticmethod
    def _row(row: sqlite3.Row | None) -> dict[str, Any] | None:
        if row is None:
            return None
        result = dict(row)
        for key in ("metadata", "state"):
            if key in result:
                result[key] = json.loads(result[key])
        return result

    def _mutate(self) -> None:
        self.backup()

    def create_project(self, project_id: str, name: str, root: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        self._mutate()
        now = time.time()
        root_path = str(Path(root).expanduser().resolve())
        self._conn.execute("INSERT INTO projects VALUES (?, ?, ?, ?, ?, ?)", (project_id, name, root_path, self._json(metadata), now, now))
        self._conn.commit()
        return self.get_project(project_id)  # type: ignore[return-value]

    def get_project(self, project_id: str) -> dict[str, Any] | None:
        return self._row(self._conn.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone())

    def list_projects(self) -> list[dict[str, Any]]:
        return [self._row(r) for r in self._conn.execute("SELECT * FROM projects ORDER BY updated_at DESC")]

    def remove_project(self, project_id: str) -> None:
        self._mutate()
        self._conn.execute("DELETE FROM projects WHERE id=?", (project_id,))
        self._conn.commit()

    def create_session(self, session_id: str, project_id: str, title: str = "", state: dict[str, Any] | None = None) -> dict[str, Any]:
        self._mutate()
        now = time.time()
        self._conn.execute("INSERT INTO sessions VALUES (?, ?, ?, ?, ?, ?)", (session_id, project_id, title, self._json(state), now, now))
        self._conn.commit()
        return self.get_session(session_id)  # type: ignore[return-value]

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        return self._row(self._conn.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone())

    def list_sessions(self, project_id: str) -> list[dict[str, Any]]:
        return [self._row(r) for r in self._conn.execute("SELECT * FROM sessions WHERE project_id=? ORDER BY updated_at DESC", (project_id,))]

    def update_session(self, session_id: str, state: dict[str, Any]) -> None:
        self._mutate()
        self._conn.execute("UPDATE sessions SET state=?, updated_at=? WHERE id=?", (self._json(state), time.time(), session_id))
        self._conn.commit()

    def create_task(self, task_id: str, project_id: str, title: str, status: str = "pending", metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        self._mutate()
        now = time.time()
        self._conn.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?, ?, ?)", (task_id, project_id, title, status, self._json(metadata), now, now))
        self._conn.commit()
        return self.get_task(task_id)  # type: ignore[return-value]

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        return self._row(self._conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone())

    def list_tasks(self, project_id: str, status: str | None = None) -> list[dict[str, Any]]:
        if status is None:
            rows = self._conn.execute("SELECT * FROM tasks WHERE project_id=? ORDER BY updated_at DESC", (project_id,))
        else:
            rows = self._conn.execute("SELECT * FROM tasks WHERE project_id=? AND status=? ORDER BY updated_at DESC", (project_id, status))
        return [self._row(r) for r in rows]

    def update_task(self, task_id: str, status: str | None = None, metadata: dict[str, Any] | None = None) -> None:
        self._mutate()
        current = self.get_task(task_id)
        if not current:
            raise KeyError(task_id)
        self._conn.execute("UPDATE tasks SET status=?, metadata=?, updated_at=? WHERE id=?", (status or current["status"], self._json(metadata if metadata is not None else current["metadata"]), time.time(), task_id))
        self._conn.commit()

    def add_memory(self, project_id: str, content: str, metadata: dict[str, Any] | None = None) -> int:
        self._mutate()
        cur = self._conn.execute("INSERT INTO memories(project_id, content, metadata, created_at) VALUES (?, ?, ?, ?)", (project_id, content, self._json(metadata), time.time()))
        self._conn.commit()
        return int(cur.lastrowid)

    def search_memory(self, project_id: str, query: str = "", limit: int = 20) -> list[dict[str, Any]]:
        if query:
            rows = self._conn.execute("SELECT * FROM memories WHERE project_id=? AND content LIKE ? ORDER BY created_at DESC LIMIT ?", (project_id, f"%{query}%", limit))
        else:
            rows = self._conn.execute("SELECT * FROM memories WHERE project_id=? ORDER BY created_at DESC LIMIT ?", (project_id, limit))
        return [self._row(r) for r in rows]

    def export_project(self, project_id: str, path: str | os.PathLike[str]) -> Path:
        project = self.get_project(project_id)
        if not project:
            raise KeyError(project_id)
        payload = {
            "version": 1,
            "project": project,
            "sessions": self.list_sessions(project_id),
            "tasks": self.list_tasks(project_id),
            "memories": self.search_memory(project_id, limit=100000),
        }
        target = Path(path).expanduser()
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix="yasin-export-", suffix=".json", dir=target.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, ensure_ascii=False, indent=2)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, target)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
        return target

    def import_project(self, path: str | os.PathLike[str], project_id: str | None = None) -> str:
        payload = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
        source = payload["project"]
        new_id = project_id or source["id"]
        if self.get_project(new_id):
            raise ValueError(f"project already exists: {new_id}")
        self._mutate()
        self._conn.execute("INSERT INTO projects VALUES (?, ?, ?, ?, ?, ?)", (new_id, source["name"], source["root"], self._json(source.get("metadata")), source["created_at"], source["updated_at"]))
        for item in payload.get("sessions", []):
            self._conn.execute("INSERT INTO sessions VALUES (?, ?, ?, ?, ?, ?)", (item["id"], new_id, item.get("title", ""), self._json(item.get("state")), item["created_at"], item["updated_at"]))
        for item in payload.get("tasks", []):
            self._conn.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?, ?, ?)", (item["id"], new_id, item["title"], item.get("status", "pending"), self._json(item.get("metadata")), item["created_at"], item["updated_at"]))
        for item in payload.get("memories", []):
            self._conn.execute("INSERT INTO memories(id, project_id, content, metadata, created_at) VALUES (?, ?, ?, ?, ?)", (item["id"], new_id, item["content"], self._json(item.get("metadata")), item["created_at"]))
        self._conn.commit()
        return new_id
