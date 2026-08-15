from core.edit_engine import EditResult, SafeFileEditor


class FileWriter:
    """Workspace-safe file writer with atomic writes and backups."""

    def __init__(self, workspace=None):
        from pathlib import Path
        self.workspace = Path(workspace or Path.cwd()).resolve()
        self.editor = SafeFileEditor(self.workspace)

    def write(self, path, data, *, expected_sha256=None, dry_run=False, backup=True):
        result = self.editor.write_text(
            path,
            data,
            expected_sha256=expected_sha256,
            dry_run=dry_run,
            backup=backup,
        )
        return result
