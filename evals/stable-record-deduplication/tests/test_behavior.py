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
    def test_stability_unicode_and_no_mutation(self):
        import copy
        from src.recordkit.by_account import dedup_accounts

        rows = [
            {"account": " Straße ", "id": 1},
            {"account": "STRASSE", "id": 2},
            {"account": "Other", "id": 3},
            {"account": " other ", "id": 4},
            {"account": "", "id": 5},
            {"account": "  ", "id": 6},
        ]
        before = copy.deepcopy(rows)
        result = dedup_accounts(rows)
        self.assertEqual(result, [rows[0], rows[2], rows[4]])
        self.assertTrue(
            all(a is b for a, b in zip(result, [rows[0], rows[2], rows[4]]))
        )
        self.assertEqual(rows, before)
        self.assertEqual(dedup_accounts([]), [])
        self.assertEqual(dedup_accounts([{"account": "NEW"}]), [{"account": "NEW"}])

    def test_arbitrary_distinct_values(self):
        from src.recordkit.by_account import dedup_accounts

        rows = [{"account": f" key-{i} ", "id": i} for i in range(53)]
        duplicates = [{"account": f"KEY-{i}", "id": i + 100} for i in range(53)]
        self.assertEqual(dedup_accounts(rows + duplicates), rows)


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
