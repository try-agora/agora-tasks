"""Hidden behavioral checks. No model calls or tool-specific scoring."""

import json
import os
from pathlib import Path
import sys
import unittest

WORKSPACE = Path(os.environ.get("TASK_WORKSPACE", "/app")).resolve()
LOGS = Path(os.environ.get("VERIFIER_LOGS", "/logs/verifier")).resolve()
sys.path.insert(0, str(WORKSPACE))


class Behavior(unittest.TestCase):
    def setUp(self):
        import tempfile
        from src.buffer import Buffer

        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "queue.db"
        self.queue = Buffer(self.path)
        self.ids = [self.queue.append(value) for value in ("first", "second", "third")]

    def tearDown(self):
        self.queue.close()
        self.temp.cleanup()

    def test_subset_durability_idempotence(self):
        from src.buffer import Buffer

        first, second, third = self.ids
        self.queue.acknowledge(iter([second, second, 9999]))
        self.queue.acknowledge([])
        self.queue.close()
        self.queue = Buffer(self.path)
        self.assertEqual(self.queue.pending(), [(first, "first"), (third, "third")])
        self.queue.acknowledge([second])
        self.assertGreater(self.queue.append("fourth"), third)

    def test_invalid_and_broken_iterables_are_atomic(self):
        before = self.queue.pending()
        for value in (True, "1", 0, -1, 1.0, None):
            with self.assertRaises(ValueError):
                self.queue.acknowledge([self.ids[0], value])
            self.assertEqual(self.queue.pending(), before)

        def broken():
            yield self.ids[0]
            raise RuntimeError("interrupted producer")

        with self.assertRaises(RuntimeError):
            self.queue.acknowledge(broken())
        self.assertEqual(self.queue.pending(), before)

    def test_database_failure_rolls_back(self):
        import sqlite3

        before = self.queue.pending()
        self.queue.db.execute(
            "CREATE TRIGGER reject_second BEFORE DELETE ON entries WHEN OLD.payload = 'second' BEGIN SELECT RAISE(ABORT, 'reject'); END"
        )
        self.queue.db.commit()
        with self.assertRaises(sqlite3.DatabaseError):
            self.queue.acknowledge(self.ids[:2])
        self.assertEqual(self.queue.pending(), before)


if __name__ == "__main__":
    LOGS.mkdir(parents=True, exist_ok=True)
    # Remove stale scores before any work; a verifier crash must not reuse one.
    (LOGS / "reward.txt").unlink(missing_ok=True)
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(Behavior)
    )
    if result.testsRun == 0:
        raise RuntimeError("no behavioral checks executed")
    evidence = {
        "tests_run": result.testsRun,
        "failures": [
            {"test": str(test), "traceback": trace} for test, trace in result.failures
        ],
        "errors": [
            {"test": str(test), "traceback": trace} for test, trace in result.errors
        ],
        "passed": result.wasSuccessful(),
    }
    (LOGS / "checks.json").write_text(json.dumps(evidence, indent=2) + "\n")
    (LOGS / "reward.txt").write_text("1\n" if result.wasSuccessful() else "0\n")
