"""Workspace file writes with automatic pre-edit checkpoints."""
from __future__ import annotations

from pathlib import Path

from backup import BackupManager


class FileWriter:
    def __init__(self, root: str | Path | None = None, backup_manager: BackupManager | None = None):
        self.root = Path(root or Path.cwd()).expanduser().resolve()
        self.backups = backup_manager or BackupManager(self.root)

    def write(self, path: str | Path, data: str) -> str | None:
        target = Path(path).expanduser()
        if not target.is_absolute():
            target = self.root / target
        target = target.resolve()
        try:
            target.relative_to(self.root)
        except ValueError as exc:
            raise ValueError("write path is outside project root") from exc
        checkpoint = self.backups.checkpoint(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(data, encoding="utf-8")
        return checkpoint
