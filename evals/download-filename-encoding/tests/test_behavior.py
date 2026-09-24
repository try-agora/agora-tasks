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
    def test_ascii_roundtrip(self):
        from email.message import Message
        from src.downloads import attachment_header

        for name in ("report.csv", 'a"b.txt', "a\\\\b.txt", "a;b.txt", "two words.txt"):
            value = attachment_header(name)
            self.assertTrue(value.isascii())
            message = Message()
            message["Content-Disposition"] = value
            self.assertEqual(message.get_content_disposition(), "attachment")
            self.assertEqual(message.get_filename(), name)

    def test_unicode_extended_name_and_fallback(self):
        from email.message import Message
        from urllib.parse import unquote
        from src.downloads import attachment_header

        for name in ("café.csv", "東京.txt", "🧪"):
            value = attachment_header(name)
            self.assertTrue(value.isascii())
            base, extended = value.rsplit("; filename*=", 1)
            self.assertTrue(extended.lower().startswith("utf-8''"))
            self.assertEqual(unquote(extended.split("''", 1)[1]), name)
            message = Message()
            message["Content-Disposition"] = base
            self.assertTrue(message.get_filename())

    def test_reject_controls(self):
        from src.downloads import attachment_header

        for name in (None, "", *("x" + chr(code) + "y" for code in (*range(32), 127))):
            with self.subTest(name=name), self.assertRaises(ValueError):
                attachment_header(name)


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
