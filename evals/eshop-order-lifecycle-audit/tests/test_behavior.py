"""Check a source-grounded order audit, independently of any provider graph."""

import hashlib
import json
import os
from pathlib import Path
import unittest

WORKSPACE = Path(os.environ.get("TASK_WORKSPACE", "/app")).resolve()
SOURCE = WORKSPACE / "src"
LOGS = Path(os.environ.get("VERIFIER_LOGS", "/logs/verifier")).resolve()
HERE = Path(__file__).resolve().parent


def source_digest():
    files = []
    directory = SOURCE / "eshop"
    if directory.is_symlink():
        return "symlink"
    for path in directory.rglob("*"):
        if path.is_symlink():
            return "symlink"
        if path.is_file():
            files.append(path)
            if len(files) > 1000:
                return "excess-files"
    digest = hashlib.sha256()
    total = 0
    for path in sorted(files, key=lambda p: p.relative_to(SOURCE).as_posix()):
        if path.is_symlink():
            return "symlink"
        try:
            with path.open("rb") as stream:
                body = stream.read(1024 * 1024)
        except OSError:
            return "missing-source"
        total += len(body)
        if len(body) == 1024 * 1024 or total > 4 * 1024 * 1024:
            return "excess-source"
        digest.update(path.relative_to(SOURCE).as_posix().encode() + b"\0")
        digest.update(hashlib.sha256(body).digest())
    return digest.hexdigest()


def expected_audit():
    # Manually traced, pinned-source witnesses; never load the oracle artifact.
    # This is a bounded source audit, not a general C# execution model.
    evidence = json.loads((HERE / "expected.json").read_text())
    locations = {}
    for key, (file, symbol, needle, *occurrence) in evidence["locations"].items():
        lines = (SOURCE / file).read_text().splitlines()
        matches = [i for i, line in enumerate(lines, 1) if line.strip() == needle]
        if len(matches) != (2 if occurrence else 1):
            raise RuntimeError(f"Source witness is ambiguous or missing: {key}")
        locations[key] = {
            "file": file,
            "symbol": symbol,
        }
    for key, (file, *needles) in evidence["decision_evidence"].items():
        body = (SOURCE / file).read_text()
        if not all(needle in body for needle in needles):
            raise RuntimeError(f"Decision evidence changed: {key}")
    return {"locations": locations, "decisions": evidence["decisions"]}


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


class Behavior(unittest.TestCase):
    def test_order_audit(self):
        self.assertTrue(SOURCE_OK, "Protected source was changed")
        artifact = SOURCE / "order-lifecycle.json"
        self.assertTrue(
            artifact.is_file() and not artifact.is_symlink(),
            "Missing regular audit artifact",
        )
        with artifact.open("rb") as stream:
            body = stream.read(64 * 1024)
        self.assertLess(len(body), 64 * 1024, "Audit exceeds 64 KiB")
        try:
            actual = json.loads(body, object_pairs_hook=unique_keys)
        except (ValueError, UnicodeError, RecursionError) as error:
            self.fail(f"Invalid JSON: {error}")
        self.assertIsInstance(actual, dict)
        self.assertEqual(set(actual), set(EXPECTED))
        for section in EXPECTED:
            self.assertIsInstance(actual[section], dict)
            self.assertEqual(set(actual[section]), set(EXPECTED[section]))
            for key, value in EXPECTED[section].items():
                with self.subTest(section=section, key=key):
                    self.assertIs(type(actual[section][key]), type(value))
                    self.assertEqual(actual[section][key], value)


if __name__ == "__main__":
    LOGS.mkdir(parents=True, exist_ok=True)
    (LOGS / "reward.txt").unlink(missing_ok=True)
    SOURCE_OK = source_digest() == (HERE / "source.sha256").read_text().strip()
    EXPECTED = expected_audit() if SOURCE_OK else {}
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(Behavior)
    )
    evidence = {
        "tests_run": result.testsRun,
        "failures": [{"test": str(t), "traceback": s} for t, s in result.failures],
        "errors": [{"test": str(t), "traceback": s} for t, s in result.errors],
        "passed": result.wasSuccessful(),
        "source_unchanged": SOURCE_OK,
        "locations": len(EXPECTED.get("locations", {})),
        "verifier_version": "1.1.0",
    }
    (LOGS / "source-witnesses.json").write_text(json.dumps(EXPECTED, indent=2) + "\n")
    (LOGS / "checks.json").write_text(json.dumps(evidence, indent=2) + "\n")
    if result.errors:
        raise RuntimeError("Verifier error; no agent score emitted")
    (LOGS / "reward.txt").write_text("1\n" if result.wasSuccessful() else "0\n")
