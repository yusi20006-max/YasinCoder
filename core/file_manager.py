from pathlib import Path

from core.edit_engine import SafeFileEditor


class FileManager:
    """Compatibility facade over the production-safe file editor."""

    def __init__(self, workspace=None):
        self.workspace = Path(workspace or Path.cwd()).resolve()
        self.editor = SafeFileEditor(self.workspace)

    def exists(self, path):
        try:
            return self.editor.resolve(path, allow_missing=True).exists()
        except Exception:
            return False

    def read(self, path):
        return self.editor.read_text(path)

    def write(self, path, data, *, expected_sha256=None, dry_run=False, backup=True):
        return self.editor.write_text(
            path,
            data,
            expected_sha256=expected_sha256,
            dry_run=dry_run,
            backup=backup,
        )

    def backup(self, path):
        target = self.editor.resolve(path)
        return self.editor._backup(target)
