import unittest
from src.recordkit.dedup import dedup_by


class Smoke(unittest.TestCase):
    def test_stable(self):
        rows = [{"id": 2}, {"id": 1}, {"id": 2}]
        self.assertEqual(dedup_by(rows, lambda row: row["id"]), rows[:2])
