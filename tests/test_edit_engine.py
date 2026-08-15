import hashlib
import tempfile
import unittest
from pathlib import Path

from core.edit_engine import EditConflict, PathViolation, PatchError, SafeFileEditor


class SafeFileEditorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.editor = SafeFileEditor(self.root, max_file_size=1024)

    def tearDown(self):
        self.tmp.cleanup()

    def test_atomic_write_and_backup(self):
        self.editor.write_text("a.txt", "one")
        result = self.editor.write_text("a.txt", "two")
        self.assertTrue(result.changed)
        self.assertEqual((self.root / "a.txt").read_text(), "two")
        self.assertEqual((self.root / "a.txt.yasin.bak").read_text(), "one")

    def test_path_traversal_and_absolute_escape_are_rejected(self):
        with self.assertRaises(PathViolation):
            self.editor.write_text("../escape.txt", "x")
        with self.assertRaises(PathViolation):
            self.editor.write_text(self.root.parent / "escape.txt", "x")

    def test_symlink_is_rejected(self):
        target = self.root / "target.txt"
        target.write_text("safe")
        link = self.root / "link.txt"
        link.symlink_to(target)
        with self.assertRaises(PathViolation):
            self.editor.write_text(link, "unsafe")

    def test_conflict_detection(self):
        path = self.root / "a.txt"
        path.write_text("before")
        digest = hashlib.sha256(b"before").hexdigest()
        path.write_text("changed")
        with self.assertRaises(EditConflict):
            self.editor.write_text(path, "new", expected_sha256=digest)

    def test_dry_run_does_not_mutate(self):
        self.editor.write_text("a.txt", "before")
        result = self.editor.write_text("a.txt", "after", dry_run=True)
        self.assertTrue(result.changed)
        self.assertTrue(result.dry_run)
        self.assertEqual((self.root / "a.txt").read_text(), "before")

    def test_unified_diff_round_trip(self):
        path = self.root / "a.txt"
        path.write_text("one\ntwo\nthree\n")
        diff = self.editor.diff(path, "one\nchanged\nthree\n")
        result = self.editor.apply_unified_diff(path, diff)
        self.assertTrue(result.changed)
        self.assertEqual(path.read_text(), "one\nchanged\nthree\n")

    def test_invalid_patch_is_rejected(self):
        self.editor.write_text("a.txt", "one\n")
        with self.assertRaises(PatchError):
            self.editor.apply_unified_diff("a.txt", "@@ -1,1 +1,1 @@\n-two\n+three\n")

    def test_transaction_rolls_back(self):
        self.editor.write_text("a.txt", "one")
        with self.assertRaises(PathViolation):
            self.editor.transaction([("a.txt", b"two"), ("../bad.txt", b"x")])
        self.assertEqual((self.root / "a.txt").read_text(), "one")

    def test_empty_file_and_binary_are_supported_by_bytes(self):
        self.editor.write_bytes("empty", b"")
        self.assertEqual(self.editor.read_bytes("empty"), b"")
        self.editor.write_bytes("data", b"\x00\xff")
        self.assertEqual(self.editor.read_bytes("data"), b"\x00\xff")

    def test_large_file_rejected(self):
        with self.assertRaises(Exception):
            self.editor.write_bytes("large", b"x" * 1025)


if __name__ == "__main__":
    unittest.main()
