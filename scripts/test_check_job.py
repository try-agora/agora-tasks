"""Regression: Harbor can report reward=1 while a later step has no score."""

import json
from pathlib import Path
import tempfile
import unittest

from check_job import check


class JobEvidence(unittest.TestCase):
    def test_rejects_false_green_multistep_summary(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "trial").mkdir()
            (root / "result.json").write_text(
                json.dumps(
                    {
                        "n_total_trials": 1,
                        "stats": {"n_completed_trials": 1, "n_errored_trials": 0},
                    }
                )
            )
            score = {"rewards": {"reward": 1}}
            trial = {
                "task_name": "agora/cross-session-framework-reuse",
                "verifier_result": score,
                "step_results": [
                    {"step_name": "rate-limit", "verifier_result": score},
                    {"step_name": "authenticate", "verifier_result": score},
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


if __name__ == "__main__":
    unittest.main()
