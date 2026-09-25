"""Independent AST census over the integrity-checked source, not an MCP index."""

import ast
from collections import defaultdict
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import unittest

WORKSPACE = Path(os.environ.get("TASK_WORKSPACE", "/app")).resolve()
LOGS = Path(os.environ.get("VERIFIER_LOGS", "/logs/verifier")).resolve()
HERE = Path(__file__).resolve().parent


def source_digest():
    digest = hashlib.sha256()
    files = [WORKSPACE / "src/helpers.json", WORKSPACE / "src/LICENSE-Django"]
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


def dotted(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = dotted(node.value)
        return prefix + "." + node.attr if prefix else ""
    return ""


def source_census():
    targets = set(json.loads((WORKSPACE / "src/helpers.json").read_text()))
    callers = {target: set() for target in targets}
    witnesses = []
    definitions = set()
    for file in sorted((WORKSPACE / "src/django").rglob("*.py")):
        relative = file.relative_to(WORKSPACE / "src").as_posix()
        module = relative[:-3].replace("/", ".").removesuffix(".__init__")
        package = module if file.name == "__init__.py" else module.rpartition(".")[0]
        tree = ast.parse(file.read_text())
        bindings = defaultdict(set)
        parents = {
            child: parent
            for parent in ast.walk(tree)
            for child in ast.iter_child_nodes(parent)
        }
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = module + "." + node.name
                bindings[node.name].add(name)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    definitions.add(name)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    bindings[alias.asname or alias.name.split(".")[0]].add(
                        alias.name if alias.asname else alias.name.split(".")[0]
                    )
            elif isinstance(node, ast.ImportFrom):
                base = (
                    importlib.util.resolve_name(
                        "." * node.level + (node.module or ""), package
                    )
                    if node.level
                    else node.module
                )
                for alias in node.names:
                    bindings[alias.asname or alias.name].add(base + "." + alias.name)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            expression = dotted(node.func)
            head, dot, tail = expression.partition(".")
            matches = {value + dot + tail for value in bindings.get(head, ())} & targets
            if not matches:
                continue
            # This is a pinned-corpus census, not a general Python resolver.
            # Fail closed if its simple imported-root assumptions cease to hold.
            if len(bindings[head]) != 1:
                raise RuntimeError(
                    f"Ambiguous import binding: {relative}:{node.lineno}"
                )
            parent = parents.get(node)
            while parent is not None:
                if isinstance(
                    parent, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)
                ):
                    args = parent.args
                    parameters = [*args.posonlyargs, *args.args, *args.kwonlyargs]
                    parameters += [arg for arg in (args.vararg, args.kwarg) if arg]
                    if head in {arg.arg for arg in parameters}:
                        raise RuntimeError(
                            f"Shadowed target binding: {relative}:{node.lineno}"
                        )
                parent = parents.get(parent)
            for target in matches:
                callers[target].add(relative)
                witnesses.append(
                    {
                        "helper": target,
                        "file": relative,
                        "line": node.lineno,
                        "expression": expression,
                    }
                )
    if not targets <= definitions:
        raise RuntimeError("Catalog contains a helper without a defining function")
    answer = {
        "ranking": sorted(
            [
                {"helper": helper, "caller_file_count": len(files)}
                for helper, files in callers.items()
            ],
            key=lambda row: (-row["caller_file_count"], row["helper"]),
        )
    }
    return answer, witnesses


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


class Behavior(unittest.TestCase):
    def test_ranking(self):
        self.assertTrue(SOURCE_OK, "Protected source or catalog changed")
        artifact = WORKSPACE / "src/helper-fan-in.json"
        self.assertTrue(
            artifact.is_file() and not artifact.is_symlink(),
            "Missing regular ranking artifact",
        )
        with artifact.open("rb") as stream:
            body = stream.read(32768)
        self.assertLess(len(body), 32768, "Artifact exceeds 32 KiB")
        try:
            answer = json.loads(body, object_pairs_hook=unique_keys)
        except (ValueError, UnicodeError, RecursionError) as error:
            self.fail(f"Invalid JSON: {error}")
        self.assertIsInstance(answer, dict)
        self.assertEqual(set(answer), {"ranking"})
        self.assertIsInstance(answer["ranking"], list)
        self.assertEqual(len(answer["ranking"]), len(EXPECTED["ranking"]))
        for row, expected in zip(answer["ranking"], EXPECTED["ranking"]):
            with self.subTest(helper=expected["helper"]):
                self.assertIsInstance(row, dict)
                self.assertIs(type(row.get("caller_file_count")), int)
                self.assertEqual(row, expected)


if __name__ == "__main__":
    LOGS.mkdir(parents=True, exist_ok=True)
    (LOGS / "reward.txt").unlink(missing_ok=True)
    SOURCE_OK = source_digest() == (HERE / "source.sha256").read_text().strip()
    EXPECTED, witnesses = source_census() if SOURCE_OK else ({}, [])
    (LOGS / "source-call-witnesses.json").write_text(
        json.dumps(witnesses, indent=2) + "\n"
    )
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(Behavior)
    )
    evidence = {
        "tests_run": result.testsRun,
        "failures": [{"test": str(t), "traceback": s} for t, s in result.failures],
        "errors": [{"test": str(t), "traceback": s} for t, s in result.errors],
        "passed": result.wasSuccessful(),
        "source_unchanged": SOURCE_OK,
        "verified_call_expressions": len(witnesses),
        "verifier_version": "1.0.0",
    }
    (LOGS / "checks.json").write_text(json.dumps(evidence, indent=2) + "\n")
    if result.errors:
        raise RuntimeError("Verifier error; no agent score emitted")
    (LOGS / "reward.txt").write_text("1\n" if result.wasSuccessful() else "0\n")
