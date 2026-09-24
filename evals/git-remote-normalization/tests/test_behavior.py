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
    def test_supported_remotes(self):
        from src.remotes import parse_remote

        cases = [
            (
                "git@Example.COM:team/repo.git",
                ("ssh", "example.com", 22, "git", "team/repo"),
            ),
            ("example.com:team/repo", ("ssh", "example.com", 22, None, "team/repo")),
            (
                "ssh://git@example.com:2222/team/repo.git",
                ("ssh", "example.com", 2222, "git", "team/repo"),
            ),
            (
                "https://EXAMPLE.com/group/sub/repo.git",
                ("https", "example.com", 443, None, "group/sub/repo"),
            ),
            (
                "https://user@example.com:8443/a.git/",
                ("https", "example.com", 8443, "user", "a"),
            ),
            (
                "ssh://git@[2001:db8::1]:2222/team/repo",
                ("ssh", "2001:db8::1", 2222, "git", "team/repo"),
            ),
            (
                "git@example.com:2222/repo.git",
                ("ssh", "example.com", 22, "git", "2222/repo"),
            ),
        ]
        for value, expected in cases:
            self.assertEqual(
                parse_remote(value),
                dict(zip(("transport", "host", "port", "user", "path"), expected)),
            )

    def test_invalid_inputs(self):
        from src.remotes import parse_remote

        for value in (
            "",
            None,
            "/tmp/repo",
            "../repo",
            "ftp://host/repo",
            "ssh://host:bad/repo",
            "ssh://host:65536/repo",
            "ssh://user:secret@host/repo",
            "ssh://host/",
            "https://host/a//b",
            "https://host/a/../b",
            "https://host/repo?token=x",
            "ssh://host/repo#ref",
            "git@host:my repo",
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_remote(value)


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
