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
        from src.recordkit.by_email import dedup_emails

        rows = [
            {"email": " Straße ", "id": 1},
            {"email": "STRASSE", "id": 2},
            {"email": "Other", "id": 3},
            {"email": " other ", "id": 4},
            {"email": "", "id": 5},
            {"email": "  ", "id": 6},
        ]
        before = copy.deepcopy(rows)
        result = dedup_emails(rows)
        self.assertEqual(result, [rows[0], rows[2], rows[4]])
        self.assertTrue(
            all(a is b for a, b in zip(result, [rows[0], rows[2], rows[4]]))
        )
        self.assertEqual(rows, before)
        self.assertEqual(dedup_emails([]), [])
        self.assertEqual(dedup_emails([{"email": "NEW"}]), [{"email": "NEW"}])

    def test_arbitrary_distinct_values(self):
        from src.recordkit.by_email import dedup_emails

        rows = [{"email": f" key-{i} ", "id": i} for i in range(53)]
        duplicates = [{"email": f"KEY-{i}", "id": i + 100} for i in range(53)]
        self.assertEqual(dedup_emails(rows + duplicates), rows)


if __name__ == "__main__":
    run_checks(Behavior)
