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
    def test_legacy_callers(self):
        from src.notify.core import build_payload
        from src.notify.alerts import alert
        from src.notify.digest import digest
        from src.notify.scheduler import scheduled

        self.assertEqual(build_payload("x"), {"msg": "x"})
        self.assertEqual(alert("a"), {"msg": "a"})
        self.assertEqual(digest(["x", "y"]), {"msg": "x; y"})
        self.assertEqual(scheduled("s"), {"msg": "s"})

    def test_independent_optional_metadata(self):
        from src.notify.core import build_payload

        for sender in (None, "", "system"):
            for category in (None, "", "ops"):
                expected = {"msg": "m"}
                if sender is not None:
                    expected["sender"] = sender
                if category is not None:
                    expected["category"] = category
                self.assertEqual(
                    build_payload("m", sender=sender, category=category), expected
                )
        first = build_payload("first", sender="s")
        first["msg"] = "changed"
        self.assertEqual(build_payload("second"), {"msg": "second"})
        with self.assertRaises(TypeError):
            build_payload("m", "s")


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
