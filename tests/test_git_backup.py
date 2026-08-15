import subprocess
from pathlib import Path

import pytest

from backup import BackupManager
from core.file_writer import FileWriter
from git_manager import GitManager, GitError


def git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def test_backup_checkpoint_and_restore(tmp_path):
    source = tmp_path / "example.txt"
    source.write_text("before", encoding="utf-8")
    backups = BackupManager(tmp_path, tmp_path / "backups")
    checkpoint = backups.checkpoint(source)
    assert checkpoint
    source.write_text("after", encoding="utf-8")
    restored = backups.restore(checkpoint)
    assert Path(restored).read_text(encoding="utf-8") == "before"


def test_file_writer_creates_pre_edit_checkpoint(tmp_path):
    source = tmp_path / "example.txt"
    source.write_text("before", encoding="utf-8")
    backups = BackupManager(tmp_path, tmp_path / "backups")
    checkpoint = FileWriter(tmp_path, backups).write(source, "after")
    assert checkpoint
    assert source.read_text(encoding="utf-8") == "after"
    backups.restore(checkpoint)
    assert source.read_text(encoding="utf-8") == "before"


def test_git_manager_status_and_explicit_commit(tmp_path):
    git(tmp_path, "init")
    git(tmp_path, "config", "user.email", "test@example.invalid")
    git(tmp_path, "config", "user.name", "YasinCoder Test")
    file = tmp_path / "note.txt"
    file.write_text("one", encoding="utf-8")
    manager = GitManager(tmp_path)
    manager.stage("note.txt")
    commit = manager.commit("test: initial checkpoint")
    assert len(commit) == 40
    assert manager.is_dirty() is False
    file.write_text("two", encoding="utf-8")
    assert manager.is_dirty() is True
    assert "note.txt" in manager.status()


def test_git_manager_refuses_empty_commit(tmp_path):
    git(tmp_path, "init")
    manager = GitManager(tmp_path)
    with pytest.raises(GitError, match="nothing staged"):
        manager.commit("should fail")


def test_git_restore_does_not_remove_untracked_file(tmp_path):
    git(tmp_path, "init")
    tracked = tmp_path / "tracked.txt"
    tracked.write_text("one", encoding="utf-8")
    git(tmp_path, "add", "tracked.txt")
    git(tmp_path, "commit", "-m", "initial")
    tracked.write_text("two", encoding="utf-8")
    untracked = tmp_path / "untracked.txt"
    untracked.write_text("keep", encoding="utf-8")
    GitManager(tmp_path).restore()
    assert tracked.read_text(encoding="utf-8") == "one"
    assert untracked.exists()
