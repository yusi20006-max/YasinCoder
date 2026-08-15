import subprocess
import tempfile
import unittest
from pathlib import Path

from backup import BackupManager
from core.file_writer import FileWriter
from git_manager import GitError, GitManager


def git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True)
    return result.stdout.strip()


class GitBackupTests(unittest.TestCase):
    def test_backup_checkpoint_and_restore(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "example.txt"
            source.write_text("before", encoding="utf-8")
            backups = BackupManager(root, root / "backups")
            checkpoint = backups.checkpoint(source)
            self.assertTrue(checkpoint)
            source.write_text("after", encoding="utf-8")
            restored = backups.restore(checkpoint)
            self.assertEqual(Path(restored).read_text(encoding="utf-8"), "before")

    def test_file_writer_creates_pre_edit_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "example.txt"
            source.write_text("before", encoding="utf-8")
            backups = BackupManager(root, root / "backups")
            checkpoint = FileWriter(root, backups).write(source, "after")
            self.assertTrue(checkpoint)
            self.assertEqual(source.read_text(encoding="utf-8"), "after")
            backups.restore(checkpoint)
            self.assertEqual(source.read_text(encoding="utf-8"), "before")

    def test_git_manager_status_and_explicit_commit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            git(root, "init")
            git(root, "config", "user.email", "test@example.invalid")
            git(root, "config", "user.name", "YasinCoder Test")
            file = root / "note.txt"
            file.write_text("one", encoding="utf-8")
            manager = GitManager(root)
            manager.stage("note.txt")
            commit = manager.commit("test: initial checkpoint")
            self.assertEqual(len(commit), 40)
            self.assertFalse(manager.is_dirty())
            file.write_text("two", encoding="utf-8")
            self.assertTrue(manager.is_dirty())
            self.assertIn("note.txt", manager.status())

    def test_git_manager_refuses_empty_commit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            git(root, "init")
            manager = GitManager(root)
            with self.assertRaisesRegex(GitError, "nothing staged"):
                manager.commit("should fail")

    def test_git_restore_does_not_remove_untracked_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            git(root, "init")
            tracked = root / "tracked.txt"
            tracked.write_text("one", encoding="utf-8")
            git(root, "add", "tracked.txt")
            git(root, "config", "user.email", "test@example.invalid")
            git(root, "config", "user.name", "YasinCoder Test")
            git(root, "commit", "-m", "initial")
            tracked.write_text("two", encoding="utf-8")
            untracked = root / "untracked.txt"
            untracked.write_text("keep", encoding="utf-8")
            GitManager(root).restore()
            self.assertEqual(tracked.read_text(encoding="utf-8"), "one")
            self.assertTrue(untracked.exists())


if __name__ == "__main__":
    unittest.main()
