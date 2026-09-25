"""Regression: Harbor can report reward=1 while a later step has no score."""

import json
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from check_job import check

TIMING = {"started_at": "2026-09-25T00:00:00Z", "finished_at": "2026-09-25T00:00:01Z"}


class JobEvidence(unittest.TestCase):
    def test_rejects_false_green_multistep_summary(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "trial").mkdir()
            (root / "result.json").write_text(
                json.dumps(
                    {
                        **TIMING,
                        "n_total_trials": 1,
                        "stats": {"n_completed_trials": 1, "n_errored_trials": 0},
                    }
                )
            )
            score = {"rewards": {"reward": 1}}
            trial = {
                **TIMING,
                "task_name": "agora/cross-session-framework-reuse",
                "verifier_result": score,
                "step_results": [
                    {
                        "step_name": "rate-limit",
                        "verifier_result": score,
                        "verifier": TIMING,
                    },
                    {
                        "step_name": "authenticate",
                        "verifier_result": score,
                        "verifier": TIMING,
                    },
                ],
            }
            path = root / "trial/result.json"
            path.write_text(json.dumps(trial))
            check(root, 1, 1)
            trial["step_results"][1]["verifier_result"] = None
            trial["step_results"][1]["exception_info"] = {
                "exception_type": "RuntimeError"
            }
            path.write_text(json.dumps(trial))
            with self.assertRaisesRegex(AssertionError, "failed step authenticate"):
                check(root, 1, 1)

    def test_rejects_duplicate_unknown_unfinished_and_missing_tasks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            job = {
                **TIMING,
                "n_total_trials": 2,
                "stats": {"n_completed_trials": 2, "n_errored_trials": 0},
            }
            trials = [
                {
                    **TIMING,
                    "task_name": f"agora/{name}",
                    "verifier_result": {"rewards": {"reward": 1}},
                }
                for name in ("checkout-discount-once", "git-remote-normalization")
            ]

            def write(records, summary=job):
                (root / "result.json").write_text(json.dumps(summary))
                for i, record in enumerate(records):
                    (root / str(i)).mkdir(exist_ok=True)
                    (root / str(i) / "result.json").write_text(json.dumps(record))

            write(trials)
            check(root, 1, 2)
            with self.assertRaisesRegex(AssertionError, "incomplete trials"):
                check(root, 1)  # A subset cannot masquerade as the full dataset.
            for key, value in (
                ("task_name", trials[0]["task_name"]),
                ("task_name", "agora/../unknown"),
                ("finished_at", None),
                ("finished_at", "invalid"),
                ("finished_at", "2020-01-01T00:00:00Z"),
                ("verifier_result", None),
                ("verifier_result", {"rewards": {"reward": True}}),
            ):
                changed = deepcopy(trials)
                changed[1][key] = value
                write(changed)
                with (
                    self.subTest(key=key, value=value),
                    self.assertRaises(AssertionError),
                ):
                    check(root, 1, 2)
            write(trials, {**job, "finished_at": None})
            with self.assertRaisesRegex(AssertionError, "job is unfinished"):
                check(root, 1, 2)


if __name__ == "__main__":
    unittest.main()
