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
    def test_threshold_clients_and_instances(self):
        from src.microapp import App
        from src.microapp.config import DEFAULTS

        for limit in (0, 1, 4):
            DEFAULTS["rate_limit"] = limit
            app = App()
            for _ in range(limit):
                self.assertEqual(app.handle(client="hot")[0], 200)
            self.assertEqual(app.handle(client="hot")[0], 429)
            if limit:
                self.assertEqual(app.handle(client="cold")[0], 200)
                self.assertEqual(App().handle(client="hot")[0], 200)
            self.assertEqual(app.last_context.state["events"], ["request", "response"])

    def test_routes_and_input(self):
        from src.microapp import App
        from src.microapp.config import DEFAULTS

        DEFAULTS["rate_limit"] = 5
        headers = {"X-Trace": "a"}
        app = App()
        self.assertEqual(app.handle("/missing", headers=headers)[0], 404)
        self.assertEqual(headers, {"X-Trace": "a"})

    def test_registered_middleware(self):
        from src.microapp.middleware import REGISTRY

        self.assertGreaterEqual(
            len(REGISTRY), 2, "feature must participate in the middleware pipeline"
        )


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
