"""Source-grounded impact facts; no provider graph or model answer is truth."""

import ast
from collections import deque
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import unittest

WORKSPACE = Path(os.environ.get("TASK_WORKSPACE", "/app")).resolve()
LOGS = Path(os.environ.get("VERIFIER_LOGS", "/logs/verifier")).resolve()
HERE = Path(__file__).resolve().parent
S = "django/core/signing.py:"
U = "django/contrib/auth/base_user.py:AbstractBaseUser."
T = "django/contrib/auth/tokens.py:PasswordResetTokenGenerator."
A = "django/contrib/auth/__init__.py:"
B = "django/contrib/sessions/backends/base.py:SessionBase."
C = "django/contrib/sessions/backends/signed_cookies.py:SessionStore."
TARGET = "django/utils/crypto.py:salted_hmac"

# Independently inspected upstream calls under the instruction's concrete
# bindings. validate_evidence.py also witnesses these edges in the real runtime.
# The fourth field identifies the exact AST call, including nested expressions.
EDGES = [
    (S + "base64_hmac", TARGET, 100, "salted_hmac"),
    (U + "get_session_auth_hash", TARGET, 132, "salted_hmac"),
    (T + "_make_token_with_timestamp", TARGET, 88, "salted_hmac"),
    (S + "Signer.signature", S + "base64_hmac", 204, "base64_hmac"),
    (S + "Signer.sign", S + "Signer.signature", 207, "self.signature"),
    (S + "Signer.unsign", S + "Signer.signature", 214, "self.signature"),
    (S + "TimestampSigner.sign", S + "Signer.sign", 263, "super().sign"),
    (S + "TimestampSigner.unsign", S + "Signer.unsign", 270, "super().unsign"),
    (S + "Signer.sign_object", S + "TimestampSigner.sign", 241, "self.sign"),
    (S + "Signer.unsign_object", S + "TimestampSigner.unsign", 246, "self.unsign"),
    (
        S + "dumps",
        S + "Signer.sign_object",
        150,
        "TimestampSigner(key, salt=salt).sign_object",
    ),
    (
        S + "loads",
        S + "Signer.unsign_object",
        168,
        "TimestampSigner(key, salt=salt, fallback_keys=fallback_keys).unsign_object",
    ),
    (B + "encode", S + "dumps", 94, "signing.dumps"),
    (B + "decode", S + "loads", 103, "signing.loads"),
    (C + "save", C + "_get_session_key", 39, "self._get_session_key"),
    (C + "load", S + "loads", 13, "signing.loads"),
    (C + "cycle_key", C + "save", 65, "self.save"),
    (C + "_get_session_key", S + "dumps", 72, "signing.dumps"),
    (
        "django/http/request.py:HttpRequest.get_signed_cookie",
        S + "TimestampSigner.unsign",
        190,
        "signing.get_cookie_signer(salt=key + salt).unsign",
    ),
    (
        "django/http/response.py:HttpResponseBase.set_signed_cookie",
        S + "TimestampSigner.sign",
        279,
        "signing.get_cookie_signer(salt=key + salt).sign",
    ),
    (
        T + "make_token",
        T + "_make_token_with_timestamp",
        45,
        "self._make_token_with_timestamp",
    ),
    (
        T + "check_token",
        T + "_make_token_with_timestamp",
        71,
        "self._make_token_with_timestamp",
    ),
    (A + "login", U + "get_session_auth_hash", 104, "user.get_session_auth_hash"),
    (A + "get_user", U + "get_session_auth_hash", 203, "user.get_session_auth_hash"),
    (
        A + "update_session_auth_hash",
        U + "get_session_auth_hash",
        230,
        "user.get_session_auth_hash",
    ),
    (A + "login", C + "cycle_key", 118, "request.session.cycle_key"),
    (A + "update_session_auth_hash", C + "cycle_key", 228, "request.session.cycle_key"),
]


def source_digest():
    digest = hashlib.sha256()
    files = [WORKSPACE / "src/entrypoints.json", WORKSPACE / "src/LICENSE-Django"]
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


@lru_cache
def functions(file):
    """Index defining symbols, not inherited aliases or incidental strings."""
    result = {}

    def visit(node, scope=()):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = (*scope, child.name)
                if not isinstance(child, ast.ClassDef):
                    result[".".join(name)] = child
                visit(child, name)
            else:
                visit(child, scope)

    visit(ast.parse((WORKSPACE / "src" / file).read_text()))
    return result


def call_range(edge):
    caller, _, line, expression = edge
    file, symbol = caller.split(":")
    matches = [
        node
        for node in ast.walk(functions(file)[symbol])
        if isinstance(node, ast.Call)
        and node.lineno == line
        and ast.unparse(node.func) == expression
    ]
    if len(matches) != 1:
        raise RuntimeError(f"Invalid trusted call evidence: {edge}")
    node = matches[0]
    return range(node.lineno, node.end_lineno + 1)


def shortest_path(start, edges=EDGES):
    pending = deque([([start], [])])
    seen = {start}
    while pending:
        path, lines = pending.popleft()
        if path[-1] == TARGET:
            return path, lines
        for caller, callee, line, *_ in edges:
            if caller == path[-1] and callee not in seen:
                seen.add(callee)
                pending.append(([*path, callee], [*lines, line]))
    return [], []


def validate_source_evidence(catalog):
    for symbol in {TARGET, *catalog.values(), *(s for e in EDGES for s in e[:2])}:
        file, name = symbol.split(":")
        if name not in functions(file):
            raise RuntimeError(f"Missing trusted symbol: {symbol}")
    for edge in EDGES:
        call_range(edge)
    # A whole-repository AST scan independently checks direct-caller completeness.
    # All upstream imports of this helper use its original name in this pin.
    found = set()
    for path in (WORKSPACE / "src/django").rglob("*.py"):
        if "salted_hmac" not in path.read_text():
            continue
        file = path.relative_to(WORKSPACE / "src").as_posix()
        for symbol, node in functions(file).items():
            for call in ast.walk(node):
                if (
                    isinstance(call, ast.Call)
                    and isinstance(call.func, ast.Name)
                    and call.func.id == "salted_hmac"
                ):
                    found.add((file + ":" + symbol, call.lineno))
    expected = {(a, line) for a, b, line, _ in EDGES if b == TARGET}
    if found != expected:
        raise RuntimeError(f"Direct-caller evidence mismatch: {found ^ expected}")


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


class Behavior(unittest.TestCase):
    def test_impact_inventory(self):
        self.assertTrue(SOURCE_OK, "Protected source or catalog was changed")
        artifact = WORKSPACE / "src/impact-inventory.json"
        self.assertTrue(
            artifact.is_file() and not artifact.is_symlink(),
            "Missing regular impact-inventory.json",
        )
        with artifact.open("rb") as stream:
            body = stream.read(65536)
        self.assertLess(len(body), 65536, "Artifact exceeds 64 KiB")
        try:
            report = json.loads(body, object_pairs_hook=unique_keys)
        except (ValueError, UnicodeError, RecursionError) as error:
            self.fail(f"Invalid JSON artifact: {error}")
        self.assertIsInstance(report, dict)
        self.assertEqual(set(report), {"direct_callers", "entrypoints"})
        direct = report["direct_callers"]
        expected = {edge[0]: edge for edge in EDGES if edge[1] == TARGET}
        self.assertIsInstance(direct, list)
        self.assertEqual(len(direct), len(expected))
        seen = set()
        for item in direct:
            self.assertIsInstance(item, dict)
            self.assertEqual(set(item), {"caller", "line"})
            self.assertIsInstance(item["caller"], str)
            self.assertIn(item["caller"], expected)
            self.assertNotIn(item["caller"], seen)
            seen.add(item["caller"])
            self.assertIs(type(item["line"]), int)
            self.assertIn(item["line"], call_range(expected[item["caller"]]))
        actual = report["entrypoints"]
        self.assertIsInstance(actual, dict)
        self.assertEqual(set(actual), set(CATALOG))
        for key, start in CATALOG.items():
            with self.subTest(entrypoint=key):
                item = actual[key]
                self.assertIsInstance(item, dict)
                self.assertEqual(set(item), {"affected", "path", "call_lines"})
                path, lines = shortest_path(start)
                self.assertIs(item["affected"], bool(path))
                self.assertIsInstance(item["path"], list)
                self.assertIsInstance(item["call_lines"], list)
                self.assertEqual(len(item["path"]), len(path), "Not a shortest path")
                self.assertEqual(len(item["call_lines"]), len(lines))
                if not path:
                    continue
                self.assertEqual(item["path"][0], start)
                self.assertEqual(item["path"][-1], TARGET)
                for caller, callee, line in zip(
                    item["path"], item["path"][1:], item["call_lines"]
                ):
                    self.assertIsInstance(caller, str)
                    self.assertIsInstance(callee, str)
                    self.assertIs(type(line), int)
                    matches = [e for e in EDGES if e[:2] == (caller, callee)]
                    self.assertTrue(matches, f"Unsupported edge: {caller} -> {callee}")
                    self.assertTrue(
                        any(line in call_range(e) for e in matches),
                        f"Incorrect call site: {caller}:{line}",
                    )


if __name__ == "__main__":
    LOGS.mkdir(parents=True, exist_ok=True)
    (LOGS / "reward.txt").unlink(missing_ok=True)
    SOURCE_OK = source_digest() == (HERE / "source.sha256").read_text().strip()
    CATALOG = (
        json.loads((WORKSPACE / "src/entrypoints.json").read_text())
        if SOURCE_OK
        else {}
    )
    # Trusted evidence failures are infrastructure errors, not agent failures.
    if SOURCE_OK:
        validate_source_evidence(CATALOG)
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(Behavior)
    )
    evidence = {
        "tests_run": result.testsRun,
        "failures": [{"test": str(t), "traceback": s} for t, s in result.failures],
        "errors": [{"test": str(t), "traceback": s} for t, s in result.errors],
        "passed": result.wasSuccessful(),
        "source_unchanged": SOURCE_OK,
        "verifier_version": "1.0.0",
        "direct_call_sites": sum(e[1] == TARGET for e in EDGES),
        "entrypoints": len(CATALOG),
    }
    (LOGS / "checks.json").write_text(json.dumps(evidence, indent=2) + "\n")
    if result.errors:
        raise RuntimeError("Verifier error; no agent score emitted")
    (LOGS / "reward.txt").write_text("1\n" if result.wasSuccessful() else "0\n")
