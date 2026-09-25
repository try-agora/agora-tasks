"""Hidden behavioral checks. No model calls or tool-specific scoring."""

from pathlib import Path
import sys
import unittest

# Python -I excludes the script directory; load only the bundled verifier helper.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import run_checks  # noqa: E402


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
    run_checks(Behavior)
