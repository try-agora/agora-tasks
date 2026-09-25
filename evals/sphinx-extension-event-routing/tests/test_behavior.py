"""Witness the real pinned registry in a clean source copy after initialization."""

import hashlib
import inspect
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

WORKSPACE = Path(os.environ.get("TASK_WORKSPACE", "/app")).resolve()
LOGS = Path(os.environ.get("VERIFIER_LOGS", "/logs/verifier")).resolve()
HERE = Path(__file__).resolve().parent


def source_digest():
    digest = hashlib.sha256()
    files = [WORKSPACE / "src/profile.json", WORKSPACE / "src/LICENSE-Sphinx"]
    for directory in (
        WORKSPACE / "src/sphinx",
        WORKSPACE / "src/project",
        WORKSPACE / "vendor",
    ):
        if directory.is_symlink():
            return "symlink"
        for path in directory.rglob("*"):
            if path.is_symlink():
                return "symlink"
            if path.is_file() and "__pycache__" not in path.parts:
                files.append(path)
                if len(files) > 4000:
                    return "excess-files"
    total = 0
    for path in sorted(files):
        if path.is_symlink():
            return "symlink"
        digest.update(path.relative_to(WORKSPACE).as_posix().encode() + b"\0")
        try:
            with path.open("rb") as stream:
                body = stream.read(16 * 1024 * 1024)
            total += len(body)
            if len(body) == 16 * 1024 * 1024 or total > 100 * 1024 * 1024:
                return "excess-source"
            digest.update(hashlib.sha256(body).digest())
        except OSError:
            return "missing-source"
    return digest.hexdigest()


def event_inventory():
    profile = json.loads((WORKSPACE / "src/profile.json").read_text())
    with tempfile.TemporaryDirectory(prefix="event-evidence-") as directory:
        root = Path(directory)
        ignore = shutil.ignore_patterns("__pycache__", "*.pyc")
        # Only previously integrity-checked source is executable. Agent-created
        # shadow modules and bytecode outside these trees cannot supply truth.
        shutil.copytree(WORKSPACE / "src/sphinx", root / "src/sphinx", ignore=ignore)
        shutil.copytree(WORKSPACE / "vendor", root / "vendor", ignore=ignore)
        shutil.copytree(WORKSPACE / "src/project", root / "project")
        sys.path[:0] = [str(root / "src"), str(root / "vendor")]
        from sphinx.application import Sphinx

        warnings = io.StringIO()
        app = Sphinx(
            str(root / "project"),
            None,
            str(root / "html"),
            str(root / "doctrees"),
            profile["builder"],
            confoverrides=profile["config_overrides"],
            freshenv=True,
            status=io.StringIO(),
            warning=warnings,
        )
        answer = {}
        for event in profile["events"]:
            listeners = []
            for listener in sorted(
                app.events.listeners[event], key=lambda entry: entry.priority
            ):
                function = inspect.unwrap(listener.handler)
                file = (
                    Path(inspect.getfile(function)).relative_to(root / "src").as_posix()
                )
                symbol = function.__qualname__.replace(".<locals>.", ".")
                listeners.append(
                    {"handler": file + ":" + symbol, "priority": listener.priority}
                )
            answer[event] = listeners
        if sum(map(len, answer.values())) != 39:
            raise RuntimeError("Pinned registry evidence changed")
        return {"events": answer}


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


class Behavior(unittest.TestCase):
    def test_event_registry(self):
        self.assertTrue(
            SOURCE_OK, "Protected source, configuration, or documents changed"
        )
        artifact = WORKSPACE / "src/event-routing.json"
        self.assertTrue(
            artifact.is_file() and not artifact.is_symlink(),
            "Missing regular routing artifact",
        )
        with artifact.open("rb") as stream:
            body = stream.read(65536)
        self.assertLess(len(body), 65536, "Artifact exceeds 64 KiB")
        try:
            report = json.loads(body, object_pairs_hook=unique_keys)
        except (ValueError, UnicodeError, RecursionError) as error:
            self.fail(f"Invalid JSON: {error}")
        self.assertIsInstance(report, dict)
        self.assertEqual(set(report), {"events"})
        self.assertIsInstance(report["events"], dict)
        self.assertEqual(set(report["events"]), set(EXPECTED["events"]))
        for event, expected in EXPECTED["events"].items():
            with self.subTest(event=event):
                rows = report["events"][event]
                self.assertIsInstance(rows, list)
                self.assertEqual(len(rows), len(expected), "Missing or extra listeners")
                for row, wanted in zip(rows, expected):
                    self.assertIsInstance(row, dict)
                    self.assertEqual(set(row), {"handler", "priority"})
                    self.assertIsInstance(row["handler"], str)
                    self.assertIs(type(row["priority"]), int)
                    normalized = {
                        **row,
                        "handler": row["handler"].replace(".<locals>.", "."),
                    }
                    self.assertEqual(normalized, wanted)


if __name__ == "__main__":
    LOGS.mkdir(parents=True, exist_ok=True)
    (LOGS / "reward.txt").unlink(missing_ok=True)
    SOURCE_OK = source_digest() == (HERE / "source.sha256").read_text().strip()
    EXPECTED = event_inventory() if SOURCE_OK else {}
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(Behavior)
    )
    evidence = {
        "tests_run": result.testsRun,
        "failures": [{"test": str(t), "traceback": s} for t, s in result.failures],
        "errors": [{"test": str(t), "traceback": s} for t, s in result.errors],
        "passed": result.wasSuccessful(),
        "source_unchanged": SOURCE_OK,
        "listener_registrations": sum(map(len, EXPECTED.get("events", {}).values())),
        "verifier_version": "1.0.0",
    }
    (LOGS / "checks.json").write_text(json.dumps(evidence, indent=2) + "\n")
    if result.errors:
        raise RuntimeError("Verifier error; no agent score emitted")
    (LOGS / "reward.txt").write_text("1\n" if result.wasSuccessful() else "0\n")
