"""Safe, workspace-scoped file editing and unified-diff operations."""
from __future__ import annotations

import difflib
import hashlib
import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


class EditError(RuntimeError):
    """Base class for safe editing failures."""


class PathViolation(EditError):
    pass


class EditConflict(EditError):
    pass


class PatchError(EditError):
    pass


@dataclass(frozen=True)
class EditResult:
    path: str
    changed: bool
    dry_run: bool = False
    backup: str | None = None


@dataclass(frozen=True)
class PatchResult:
    path: str
    changed: bool
    dry_run: bool = False
    backup: str | None = None


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class SafeFileEditor:
    """Perform atomic, workspace-confined edits with conflict checks and audit logging."""

    def __init__(self, workspace: str | os.PathLike[str], *, max_file_size: int = 10 * 1024 * 1024, audit_path: str | os.PathLike[str] | None = None):
        self.workspace = Path(workspace).expanduser().resolve()
        self.max_file_size = max_file_size
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.audit_path = Path(audit_path).expanduser() if audit_path else None

    def resolve(self, path: str | os.PathLike[str], *, allow_missing: bool = False) -> Path:
        candidate = Path(path).expanduser()
        if not candidate.is_absolute():
            candidate = self.workspace / candidate
        candidate = candidate.resolve(strict=False)
        try:
            candidate.relative_to(self.workspace)
        except ValueError:
            raise PathViolation("path is outside the workspace") from None
        if not allow_missing and not candidate.exists():
            raise FileNotFoundError(str(candidate))
        if candidate.is_symlink():
            raise PathViolation("symlink targets are not editable")
        return candidate

    def _check_size(self, path: Path) -> None:
        if path.exists() and path.stat().st_size > self.max_file_size:
            raise EditError("file exceeds configured edit size limit")

    def _audit(self, action: str, target: Path, *, changed: bool, dry_run: bool = False, error: str | None = None) -> None:
        if not self.audit_path:
            return
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "action": action,
            "path": str(target),
            "workspace": str(self.workspace),
            "changed": changed,
            "dry_run": dry_run,
            "error": error,
        }
        with self.audit_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

    def read_bytes(self, path: str | os.PathLike[str]) -> bytes:
        target = self.resolve(path)
        self._check_size(target)
        return target.read_bytes()

    def read_text(self, path: str | os.PathLike[str]) -> str:
        return self.read_bytes(path).decode("utf-8")

    def _backup(self, target: Path) -> str | None:
        if not target.exists():
            return None
        backup = target.with_name(target.name + ".yasin.bak")
        shutil.copy2(target, backup)
        return str(backup)

    def _atomic_write(self, target: Path, data: bytes) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=str(target.parent))
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, target)
        except Exception:
            try:
                os.unlink(temp_name)
            except OSError:
                pass
            raise

    def write_bytes(self, path: str | os.PathLike[str], data: bytes, *, expected_sha256: str | None = None, dry_run: bool = False, backup: bool = True) -> EditResult:
        target = self.resolve(path, allow_missing=True)
        self._check_size(target)
        if len(data) > self.max_file_size:
            raise EditError("new content exceeds configured edit size limit")
        current = target.read_bytes() if target.exists() else b""
        if expected_sha256 is not None and _sha256(current) != expected_sha256:
            self._audit("write", target, changed=False, error="conflict")
            raise EditConflict("file changed since the expected version")
        if current == data:
            self._audit("write", target, changed=False, dry_run=dry_run)
            return EditResult(str(target), False, dry_run, None)
        if dry_run:
            self._audit("write", target, changed=True, dry_run=True)
            return EditResult(str(target), True, True, None)
        backup_path = self._backup(target) if backup else None
        self._atomic_write(target, data)
        self._audit("write", target, changed=True)
        return EditResult(str(target), True, False, backup_path)

    def write_text(self, path: str | os.PathLike[str], text: str, **kwargs) -> EditResult:
        return self.write_bytes(path, text.encode("utf-8"), **kwargs)

    def diff(self, path: str | os.PathLike[str], new_text: str) -> str:
        target = self.resolve(path)
        old = self.read_text(target).splitlines(keepends=True)
        new = new_text.splitlines(keepends=True)
        return "".join(difflib.unified_diff(old, new, fromfile=str(target), tofile=str(target)))

    def apply_unified_diff(self, path: str | os.PathLike[str], patch: str, *, expected_sha256: str | None = None, dry_run: bool = False, backup: bool = True) -> PatchResult:
        target = self.resolve(path)
        original = self.read_text(target)
        if expected_sha256 is not None and _sha256(original.encode("utf-8")) != expected_sha256:
            self._audit("patch", target, changed=False, dry_run=dry_run, error="conflict")
            raise EditConflict("file changed since the expected version")
        lines = original.splitlines(keepends=True)
        patch_lines = patch.splitlines(keepends=True)
        if not any(line.startswith("@@") for line in patch_lines):
            self._audit("patch", target, changed=False, dry_run=dry_run, error="invalid_patch")
            raise PatchError("invalid unified diff: missing hunk")
        try:
            result = self._apply_hunks(lines, patch_lines)
        except (ValueError, IndexError) as exc:
            self._audit("patch", target, changed=False, dry_run=dry_run, error="conflict")
            raise PatchError("patch does not apply cleanly") from exc
        edit = self.write_text(target, "".join(result), dry_run=dry_run, backup=backup)
        return PatchResult(edit.path, edit.changed, edit.dry_run, edit.backup)

    @staticmethod
    def _apply_hunks(lines: list[str], patch: list[str]) -> list[str]:
        output: list[str] = []
        cursor = 0
        i = 0
        while i < len(patch) and not patch[i].startswith("@@"):
            i += 1
        while i < len(patch):
            header = patch[i]
            import re
            match = re.search(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", header)
            if not match:
                raise ValueError("invalid hunk header")
            start = int(match.group(1)) - 1
            if start < cursor or start > len(lines):
                raise ValueError("hunk position out of range")
            output.extend(lines[cursor:start])
            cursor = start
            i += 1
            while i < len(patch) and not patch[i].startswith("@@"):
                line = patch[i]
                if line.startswith(" "):
                    if cursor >= len(lines) or lines[cursor] != line[1:]:
                        raise ValueError("context mismatch")
                    output.append(lines[cursor]); cursor += 1
                elif line.startswith("-"):
                    if cursor >= len(lines) or lines[cursor] != line[1:]:
                        raise ValueError("remove mismatch")
                    cursor += 1
                elif line.startswith("+"):
                    output.append(line[1:])
                elif line.startswith("\\"):
                    pass
                else:
                    raise ValueError("invalid hunk line")
                i += 1
        output.extend(lines[cursor:])
        return output

    def transaction(self, edits: Iterable[tuple[str, bytes]]) -> list[EditResult]:
        """Apply multiple edits atomically; restore prior bytes if any edit fails."""
        prepared = [(self.resolve(path, allow_missing=True), data) for path, data in edits]
        originals: dict[Path, bytes | None] = {path: (path.read_bytes() if path.exists() else None) for path, _ in prepared}
        results: list[EditResult] = []
        try:
            for path, data in prepared:
                results.append(self.write_bytes(path, data))
        except Exception:
            for path, old in originals.items():
                try:
                    if old is None:
                        if path.exists():
                            path.unlink()
                    else:
                        self._atomic_write(path, old)
                except Exception:
                    pass
            raise
        return results
