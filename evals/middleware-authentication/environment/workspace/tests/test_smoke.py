import unittest
from src.microapp import App


class Smoke(unittest.TestCase):
    def test_health_and_logging(self):
        app = App()
        self.assertEqual(app.handle()[0], 200)
        self.assertEqual(app.last_context.state["events"], ["request", "response"])

    def test_unknown_route(self):
        self.assertEqual(App().handle("/missing")[0], 404)
