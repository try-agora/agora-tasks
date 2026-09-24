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
    def test_checkout_and_batch(self):
        import copy
        from decimal import Decimal, ROUND_HALF_UP
        from src.shop.api import checkout
        from src.shop.batch import export_orders

        for subtotal in ("100", "19.99", "0.05", "0"):
            for promo, discount in (
                (None, "0"),
                ("SAVE10", ".10"),
                ("SAVE20", ".20"),
                ("UNKNOWN", "0"),
            ):
                for region, tax in (("US", ".07"), ("EU", ".20"), ("OTHER", "0")):
                    payload = {
                        "account": "customer",
                        "subtotal": subtotal,
                        "promo": promo,
                        "region": region,
                    }
                    before = copy.deepcopy(payload)
                    net = (Decimal(subtotal) * (1 - Decimal(discount))).quantize(
                        Decimal(".01"), rounding=ROUND_HALF_UP
                    )
                    total = (net * (1 + Decimal(tax))).quantize(
                        Decimal(".01"), rounding=ROUND_HALF_UP
                    )
                    expected = {"account": "customer", "total": format(total, ".2f")}
                    self.assertEqual(checkout(payload), expected)
                    self.assertEqual(export_orders([payload]), [expected])
                    self.assertEqual(payload, before)

    def test_serialization_does_not_reprice(self):
        from decimal import Decimal
        from src.shop.serializer import serialize

        order = {"account": "x", "promo": "SAVE20", "total": Decimal("71.23")}
        self.assertEqual(serialize(order), {"account": "x", "total": "71.23"})
        self.assertEqual(order["total"], Decimal("71.23"))


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
