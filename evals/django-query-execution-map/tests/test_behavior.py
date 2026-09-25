"""Grade concrete execution facts against the unmodified, pinned runtime."""

import ast
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import runpy
import sqlite3
import sqlite3.dbapi2
import _sqlite3
import sys
import unittest

WORKSPACE = Path(os.environ.get("TASK_WORKSPACE", "/app")).resolve()
LOGS = Path(os.environ.get("VERIFIER_LOGS", "/logs/verifier")).resolve()
HERE = Path(__file__).resolve().parent
DRIVER_TARGETS = {
    "sqlite3.Cursor.execute": sqlite3.Cursor.execute,
    "sqlite3.dbapi2.Cursor.execute": sqlite3.dbapi2.Cursor.execute,
    "_sqlite3.Cursor.execute": _sqlite3.Cursor.execute,
}


def source_digest():
    digest = hashlib.sha256()
    files = [WORKSPACE / "src/scenario.py", WORKSPACE / "src/LICENSE-Django"]
    for directory in (WORKSPACE / "src/django", WORKSPACE / "vendor"):
        if directory.is_symlink():
            return "symlink"
        for path in directory.rglob("*"):
            if path.is_symlink():
                return "symlink"
            if path.is_file() and "__pycache__" not in path.parts:
                files.append(path)
                if len(files) > 1200:
                    return "excess-files"
    total_bytes = 0
    for path in sorted(files):
        if path.is_symlink():
            return "symlink"
        digest.update(path.relative_to(WORKSPACE).as_posix().encode() + b"\0")
        try:
            with path.open("rb") as stream:
                body = stream.read(1024 * 1024)
            total_bytes += len(body)
            if len(body) == 1024 * 1024 or total_bytes > 12 * 1024 * 1024:
                return "excess-source"
            digest.update(hashlib.sha256(body).digest())
        except OSError:
            return "missing-source"
    return digest.hexdigest()


def observed_scenarios():
    # Only import agent-visible code after checking it against the frozen digest.
    # Keep the standard library and verified vendor packages ahead of scratch
    # modules an agent might create beside the output artifact.
    sys.path.extend([str(WORKSPACE / "vendor"), str(WORKSPACE / "src")])
    scenario = runpy.run_path(str(WORKSPACE / "src/scenario.py"))
    source = WORKSPACE / "src"
    terminal = source / "django/db/backends/sqlite3/base.py"
    observed = {}

    def observe(name, action, queryset):
        stacks = []

        def profile(frame, event, arg):
            if (
                event != "call"
                or frame.f_code.co_qualname != "SQLiteCursorWrapper.execute"
                or Path(frame.f_code.co_filename) != terminal
                or not frame.f_locals["query"].lstrip().upper().startswith("SELECT")
            ):
                return
            stack = []
            current = frame
            while current is not None:
                path = Path(current.f_code.co_filename)
                if path.is_relative_to(source / "django"):
                    stack.append(
                        {
                            "file": path.relative_to(source).as_posix(),
                            "symbol": current.f_code.co_qualname,
                            "call_line": None if current is frame else current.f_lineno,
                        }
                    )
                current = current.f_back
            stacks.append(list(reversed(stack)))

        sys.setprofile(profile)
        try:
            action()
        finally:
            sys.setprofile(None)
        observed[name] = {
            "sql_count": len(stacks),
            "cache_populated": queryset._result_cache is not None,
            "path": stacks[0] if stacks else [],
        }

    scenario["run_cases"](observe)
    return observed


# These off-stack call sites are independently read from the pinned source.
# Dynamic SELECT paths above are observed, not matched to an agent/reference answer.
BINDINGS = {
    "compiler_selector": {
        "file": "django/db/models/sql/query.py",
        "symbol": "Query.get_compiler",
        "call_line": 296,
        "target": "django.db.backends.base.operations.BaseDatabaseOperations.compiler",
    },
    "compiler_class": {
        "file": "django/db/backends/base/operations.py",
        "symbol": "BaseDatabaseOperations.compiler",
        "call_line": 369,
        "target": "django.db.models.sql.compiler.SQLCompiler",
    },
    "cursor_factory": {
        "file": "django/db/backends/base/base.py",
        "symbol": "BaseDatabaseWrapper._cursor",
        "call_line": 301,
        "target": "django.db.backends.sqlite3.base.DatabaseWrapper.create_cursor",
    },
    "driver_execute": {
        "file": "django/db/backends/sqlite3/base.py",
        "symbol": "SQLiteCursorWrapper.execute",
        "call_line": 357,
        "target": "sqlite3.Cursor.execute",
    },
}


@lru_cache
def call_lines(file, line):
    tree = ast.parse((WORKSPACE / "src" / file).read_text())
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and node.lineno <= line <= node.end_lineno
    ]
    if not calls:
        raise RuntimeError(f"Verifier call-site evidence is invalid: {file}:{line}")
    call = min(calls, key=lambda node: node.end_lineno - node.lineno)
    return range(call.lineno, call.end_lineno + 1)


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


class Behavior(unittest.TestCase):
    def assert_site(self, actual, expected):
        self.assertIsInstance(actual, dict)
        self.assertEqual(set(actual), set(expected))
        for key in expected:
            if key == "target" and expected[key] == "sqlite3.Cursor.execute":
                self.assertIsInstance(actual[key], str)
                self.assertIs(DRIVER_TARGETS.get(actual[key]), sqlite3.Cursor.execute)
            elif key != "call_line":
                self.assertEqual(actual[key], expected[key], key)
        if expected["call_line"] is None:
            self.assertIsNone(actual["call_line"])
        else:
            self.assertIs(type(actual["call_line"]), int)
            self.assertIn(
                actual["call_line"], call_lines(expected["file"], expected["call_line"])
            )

    def test_execution_map(self):
        self.assertTrue(
            SOURCE_OK, "Provided source, dependencies, or scenario were changed"
        )
        artifact = WORKSPACE / "src/execution-path.json"
        self.assertTrue(
            artifact.is_file() and not artifact.is_symlink(),
            "Missing regular execution-path.json",
        )
        with artifact.open("rb") as stream:
            body = stream.read(32768)
        self.assertLess(len(body), 32768, "Artifact exceeds 32 KiB")
        try:
            report = json.loads(body, object_pairs_hook=unique_keys)
        except (ValueError, UnicodeError, RecursionError) as error:
            self.fail(f"Invalid JSON artifact: {error}")
        self.assertIsInstance(report, dict)
        self.assertEqual(set(report), {"scenarios", "bindings"})
        self.assertIsInstance(report["scenarios"], dict)
        self.assertEqual(set(report["scenarios"]), set(OBSERVED))
        for name, expected in OBSERVED.items():
            with self.subTest(scenario=name):
                actual = report["scenarios"][name]
                self.assertIsInstance(actual, dict)
                self.assertEqual(set(actual), {"sql_count", "cache_populated", "path"})
                self.assertIs(type(actual["sql_count"]), int)
                self.assertEqual(actual["sql_count"], expected["sql_count"])
                self.assertIs(actual["cache_populated"], expected["cache_populated"])
                self.assertIsInstance(actual["path"], list)
                self.assertEqual(len(actual["path"]), len(expected["path"]))
                for site, wanted in zip(actual["path"], expected["path"], strict=True):
                    self.assert_site(site, wanted)
        self.assertIsInstance(report["bindings"], dict)
        self.assertEqual(set(report["bindings"]), set(BINDINGS))
        for name, expected in BINDINGS.items():
            with self.subTest(binding=name):
                self.assert_site(report["bindings"][name], expected)


if __name__ == "__main__":
    LOGS.mkdir(parents=True, exist_ok=True)
    (LOGS / "reward.txt").unlink(missing_ok=True)
    SOURCE_OK = source_digest() == (HERE / "source.sha256").read_text().strip()
    # A failure of the trusted scenario/evidence is an infrastructure error:
    # propagate it before unittest, leaving no reward file.
    OBSERVED = observed_scenarios() if SOURCE_OK else {}
    sites = [s for case in OBSERVED.values() for s in case["path"]]
    for site in sites + (list(BINDINGS.values()) if SOURCE_OK else []):
        if site["call_line"] is not None:
            call_lines(site["file"], site["call_line"])
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(Behavior)
    )
    evidence = {
        "tests_run": result.testsRun,
        "failures": [
            {"test": str(test), "traceback": trace} for test, trace in result.failures
        ],
        "errors": [
            {"test": str(test), "traceback": trace} for test, trace in result.errors
        ],
        "passed": result.wasSuccessful(),
        "source_unchanged": SOURCE_OK,
        "verifier_version": "1.1.1",
        "observed_scenarios": OBSERVED,
    }
    (LOGS / "checks.json").write_text(json.dumps(evidence, indent=2) + "\n")
    (LOGS / "reward.txt").write_text("1\n" if result.wasSuccessful() else "0\n")
