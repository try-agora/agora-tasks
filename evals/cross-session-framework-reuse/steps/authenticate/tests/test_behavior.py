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
    def test_opt_in_and_headers(self):
        from src.microapp import App
        from src.microapp.config import DEFAULTS

        DEFAULTS["auth_required"] = False
        self.assertEqual(App().handle()[0], 200)
        DEFAULTS["auth_required"] = True
        app = App()
        for headers in (
            {},
            {"Authorization": ""},
            {"authorization": "   "},
            {"X-Token": "x"},
        ):
            self.assertEqual(app.handle(headers=headers)[0], 401)
        for key in ("Authorization", "authorization", "AUTHORIZATION"):
            headers = {key: "Bearer token"}
            self.assertEqual(app.handle(headers=headers)[0], 200)
            self.assertEqual(headers, {key: "Bearer token"})
        self.assertEqual(app.last_context.state["events"], ["request", "response"])
        self.assertEqual(app.handle("/missing", headers={"Authorization": "x"})[0], 404)

    def test_registered_middleware(self):
        from src.microapp import App  # noqa: F401 -- load application registrations
        from src.microapp.middleware import REGISTRY

        self.assertGreaterEqual(len(REGISTRY), 2)


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
