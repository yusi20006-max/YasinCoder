"""Recoverable pre-edit checkpoints stored outside the project tree."""
from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path


class BackupError(RuntimeError):
    """Raised when a checkpoint cannot be created or restored safely."""


class BackupManager:
    """Create and restore timestamped file checkpoints without polluting Git."""

    def __init__(self, root: str | Path | None = None, storage: str | Path | None = None):
        self.root = Path(root or Path.cwd()).expanduser().resolve()
        self.storage = Path(storage or (Path.home() / ".cache" / "yasin-coder" / "backups")).expanduser().resolve()
        self.storage.mkdir(parents=True, exist_ok=True)

    def _safe_path(self, path: str | Path) -> Path:
        candidate = Path(path).expanduser()
        if not candidate.is_absolute():
            candidate = self.root / candidate
        candidate = candidate.resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise BackupError("backup path is outside project root") from exc
        return candidate

    def checkpoint(self, path: str | Path) -> str | None:
        """Save an existing file before editing it and return its checkpoint id."""
        source = self._safe_path(path)
        if not source.is_file():
            return None
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        digest = hashlib.sha256(str(source.relative_to(self.root)).encode()).hexdigest()[:12]
        checkpoint_id = f"{stamp}-{digest}"
        target_dir = self.storage / checkpoint_id
        target_dir.mkdir(parents=True, exist_ok=False)
        relative = source.relative_to(self.root)
        target = target_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        metadata = {
            "id": checkpoint_id,
            "root": str(self.root),
            "path": str(relative),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        (target_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        return checkpoint_id

    def backup(self, path: str | Path) -> str | None:
        """Backward-compatible alias for checkpoint()."""
        return self.checkpoint(path)

    def restore(self, checkpoint_id: str) -> str:
        if not checkpoint_id or Path(checkpoint_id).name != checkpoint_id:
            raise BackupError("invalid checkpoint id")
        directory = self.storage / checkpoint_id
        metadata_path = directory / "metadata.json"
        if not metadata_path.is_file():
            raise BackupError("checkpoint not found")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        relative = Path(metadata["path"])
        destination = self._safe_path(relative)
        source = directory / relative
        if not source.is_file():
            raise BackupError("checkpoint payload missing")
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as tmp:
            temp_path = Path(tmp.name)
        try:
            shutil.copy2(source, temp_path)
            temp_path.replace(destination)
        finally:
            temp_path.unlink(missing_ok=True)
        return str(destination)

    def list(self) -> list[dict]:
        checkpoints = []
        for directory in sorted(self.storage.iterdir(), reverse=True):
            metadata = directory / "metadata.json"
            if not metadata.is_file():
                continue
            try:
                checkpoints.append(json.loads(metadata.read_text(encoding="utf-8")))
            except (OSError, json.JSONDecodeError):
                continue
        return checkpoints
