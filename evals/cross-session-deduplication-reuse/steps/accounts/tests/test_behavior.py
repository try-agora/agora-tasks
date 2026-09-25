"""Hidden behavioral checks. No model calls or tool-specific scoring."""

from pathlib import Path
import sys
import unittest

# Python -I excludes the script directory; load only the bundled verifier helper.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import run_checks  # noqa: E402


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
    run_checks(Behavior)
