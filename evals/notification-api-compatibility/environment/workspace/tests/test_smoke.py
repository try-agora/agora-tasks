import unittest
from src.notify.alerts import alert


class Smoke(unittest.TestCase):
    def test_legacy(self):
        self.assertEqual(alert("hello"), {"msg": "hello"})
