"""Preservation checks using only Python's standard library and temporary files."""

import hashlib
from contextlib import closing
import importlib.util
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


BACKEND = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("database_paths", BACKEND / "database_paths.py")
paths = importlib.util.module_from_spec(spec)
spec.loader.exec_module(paths)


class DatabaseSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_application_path_does_not_depend_on_startup_directory(self):
        original = Path.cwd()
        try:
            os.chdir(self.root)
            spec.loader.exec_module(paths)
            self.assertEqual(paths.DATABASE_PATH, BACKEND / "privacy_analyzer.db")
            self.assertFalse((self.root / "privacy_analyzer.db").exists())
        finally:
            os.chdir(original)

    def test_recovered_path_is_refused_even_when_missing(self):
        recovered = self.root / "recovered.db"
        with patch.object(paths, "DATABASE_PATH", recovered):
            with self.assertRaisesRegex(ValueError, "recovered"):
                paths.reserve_seed_destination(recovered)
        self.assertFalse(recovered.exists())

    def test_existing_database_keeps_rows_and_identical_bytes(self):
        target = self.root / "existing.db"
        with closing(sqlite3.connect(target)) as db:
            db.execute("CREATE TABLE evidence (id INTEGER PRIMARY KEY, observation TEXT)")
            db.execute("INSERT INTO evidence VALUES (1, 'permission declared')")
            db.commit()
        before = hashlib.sha256(target.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError, "already exists"):
            paths.reserve_seed_destination(target)
        self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(), before)
        with closing(sqlite3.connect(target)) as db:
            self.assertEqual(db.execute("SELECT * FROM evidence").fetchall(), [(1, "permission declared")])

    def test_existing_empty_file_is_also_refused(self):
        target = self.root / "empty.db"
        target.touch()
        with self.assertRaises(ValueError):
            paths.reserve_seed_destination(target)
        self.assertEqual(target.read_bytes(), b"")

    def test_sqlite_recovery_sidecars_are_preserved(self):
        for suffix in ("-wal", "-shm", "-journal"):
            with self.subTest(suffix=suffix):
                target = self.root / (suffix[1:] + ".db")
                sidecar = Path(str(target) + suffix)
                sidecar.write_bytes(b"recovery data")
                with self.assertRaisesRegex(ValueError, "recovery files"):
                    paths.reserve_seed_destination(target)
                self.assertFalse(target.exists())
                self.assertEqual(sidecar.read_bytes(), b"recovery data")

    def test_new_destination_is_reserved_once(self):
        target = self.root / "demo.db"
        self.assertEqual(paths.reserve_seed_destination(target), target.resolve())
        self.assertTrue(target.is_file())
        with self.assertRaises(ValueError):
            paths.reserve_seed_destination(target)

    def test_file_created_after_validation_is_not_truncated(self):
        target = self.root / "race.db"

        def competing_creation(destination):
            target.write_bytes(b"another process owns this")
            return target

        with patch.object(paths, "validate_seed_destination", side_effect=competing_creation):
            with self.assertRaises(FileExistsError):
                paths.reserve_seed_destination(target)
        self.assertEqual(target.read_bytes(), b"another process owns this")

    def test_missing_parent_is_not_created(self):
        target = self.root / "missing" / "demo.db"
        with self.assertRaisesRegex(ValueError, "parent directory"):
            paths.reserve_seed_destination(target)
        self.assertFalse(target.parent.exists())

    def run_seed(self, *arguments):
        return subprocess.run(
            [sys.executable, "-B", str(BACKEND / "seed_data.py"), *arguments],
            cwd=self.root, capture_output=True, text=True, timeout=15,
        )

    def test_cli_requires_explicit_destination_without_creating_database(self):
        result = self.run_seed()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--database", result.stderr)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_cli_refuses_existing_database_before_loading_dependencies(self):
        target = self.root / "existing.db"
        target.write_bytes(b"preserve this file")
        result = self.run_seed("--database", str(target))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("already exists", result.stderr)
        self.assertEqual(target.read_bytes(), b"preserve this file")
        self.assertNotIn("ModuleNotFoundError", result.stderr)

    def test_import_cannot_seed_or_load_database_dependencies(self):
        result = subprocess.run(
            [sys.executable, "-B", "-c",
             "import sys; sys.path.insert(0, sys.argv[1]); import seed_data", str(BACKEND)],
            cwd=self.root, capture_output=True, text=True, timeout=15,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must be run explicitly", result.stderr)
        self.assertNotIn("ModuleNotFoundError", result.stderr)
        self.assertEqual(list(self.root.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
