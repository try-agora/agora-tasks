"""Derive inheritance truth from the pinned runtime, never a provider graph."""

import ast
import hashlib
import importlib
import inspect
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
HOOKS = ("as_sql", "process_rhs")


def source_digest():
    digest = hashlib.sha256()
    files = [WORKSPACE / "src/LICENSE-Django"]
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
    total = 0
    for path in sorted(files):
        if path.is_symlink():
            return "symlink"
        digest.update(path.relative_to(WORKSPACE).as_posix().encode() + b"\0")
        try:
            with path.open("rb") as stream:
                body = stream.read(1024 * 1024)
            total += len(body)
            if len(body) == 1024 * 1024 or total > 12 * 1024 * 1024:
                return "excess-source"
            digest.update(hashlib.sha256(body).digest())
        except OSError:
            return "missing-source"
    return digest.hexdigest()


def expected_inventory():
    # Copy only integrity-checked source. Never import an agent-created pyc,
    # analysis script, or shadow module from the mutable workspace root.
    with tempfile.TemporaryDirectory(prefix="lookup-evidence-") as directory:
        root = Path(directory)
        ignore = shutil.ignore_patterns("__pycache__", "*.pyc")
        shutil.copytree(WORKSPACE / "src/django", root / "django", ignore=ignore)
        shutil.copytree(WORKSPACE / "vendor", root / "vendor", ignore=ignore)
        sys.path[:0] = [str(root), str(root / "vendor")]
        from django.db.models.lookups import Lookup

        def identity(cls):
            file = Path(inspect.getfile(cls)).relative_to(root).as_posix()
            return file + ":" + cls.__qualname__

        answer = {}
        # Inspect every module in the declared scope, not a hand-picked list
        # inferred from graph output or the reference artifact.
        for file in sorted((root / "django/db/models").rglob("*.py")):
            definitions = [
                n
                for n in ast.parse(file.read_text()).body
                if isinstance(n, ast.ClassDef)
            ]
            if not definitions:
                continue
            module_name = (
                file.relative_to(root).with_suffix("").as_posix().replace("/", ".")
            )
            module_name = module_name.removesuffix(".__init__")
            module = importlib.import_module(module_name)
            for node in definitions:
                cls = getattr(module, node.name)
                if cls is Lookup or not issubclass(cls, Lookup):
                    continue
                owners = {}
                for hook in HOOKS:
                    owner = next(base for base in cls.__mro__ if hook in base.__dict__)
                    owners[hook] = identity(owner) + "." + hook
                    # Check runtime ownership against the defining source AST.
                    owner_file = Path(inspect.getfile(owner))
                    declaration = next(
                        n
                        for n in ast.parse(owner_file.read_text()).body
                        if isinstance(n, ast.ClassDef) and n.name == owner.__name__
                    )
                    if not any(
                        isinstance(n, ast.FunctionDef) and n.name == hook
                        for n in declaration.body
                    ):
                        raise RuntimeError(
                            f"Missing source declaration: {owners[hook]}"
                        )
                answer[identity(cls)] = {
                    "bases": [identity(base) for base in cls.__bases__],
                    "owners": owners,
                }
        if len(answer) != 66:
            raise RuntimeError(
                f"Pinned runtime evidence changed: {len(answer)} classes"
            )
        return {"classes": answer}


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


class Behavior(unittest.TestCase):
    def test_inventory(self):
        self.assertTrue(SOURCE_OK, "Protected source was changed")
        artifact = WORKSPACE / "src/lookup-hierarchy.json"
        self.assertTrue(
            artifact.is_file() and not artifact.is_symlink(),
            "Missing regular inventory",
        )
        with artifact.open("rb") as stream:
            body = stream.read(128 * 1024)
        self.assertLess(len(body), 128 * 1024, "Inventory exceeds 128 KiB")
        try:
            answer = json.loads(body, object_pairs_hook=unique_keys)
        except (ValueError, UnicodeError, RecursionError) as error:
            self.fail(f"Invalid JSON: {error}")
        self.assertIsInstance(answer, dict)
        self.assertEqual(set(answer), {"classes"})
        self.assertIsInstance(answer["classes"], dict)
        self.assertEqual(
            set(answer["classes"]),
            set(EXPECTED["classes"]),
            "Missing or extra descendants",
        )
        for name, expected in EXPECTED["classes"].items():
            with self.subTest(lookup=name):
                self.assertEqual(answer["classes"][name], expected)


if __name__ == "__main__":
    LOGS.mkdir(parents=True, exist_ok=True)
    (LOGS / "reward.txt").unlink(missing_ok=True)
    SOURCE_OK = source_digest() == (HERE / "source.sha256").read_text().strip()
    # Evidence failures are verifier errors; they must not become agent failures.
    EXPECTED = expected_inventory() if SOURCE_OK else {}
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(Behavior)
    )
    evidence = {
        "tests_run": result.testsRun,
        "failures": [{"test": str(t), "traceback": s} for t, s in result.failures],
        "errors": [{"test": str(t), "traceback": s} for t, s in result.errors],
        "passed": result.wasSuccessful(),
        "source_unchanged": SOURCE_OK,
        "classes": len(EXPECTED.get("classes", {})),
        "verifier_version": "1.0.0",
    }
    (LOGS / "checks.json").write_text(json.dumps(evidence, indent=2) + "\n")
    if result.errors:
        raise RuntimeError("Verifier error; no agent score emitted")
    (LOGS / "reward.txt").write_text("1\n" if result.wasSuccessful() else "0\n")
