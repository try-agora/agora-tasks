"""Hidden behavioral checks. No model calls or tool-specific scoring."""

from pathlib import Path
import sys
import unittest

# Python -I excludes the script directory; load only the bundled verifier helper.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import run_checks  # noqa: E402


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
    run_checks(Behavior)
