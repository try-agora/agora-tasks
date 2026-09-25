"""Scoring must reward correct efficiency, never missing evidence or partial work."""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from score_job import score_job, score_trial


def stage(name="single", correct=1, tokens=100, seconds=10):
    return {
        "step_name": name,
        "verifier_result": {"rewards": {"reward": correct}},
        "agent_result": {
            "n_input_tokens": tokens,
            "n_cache_tokens": tokens // 2,
            "n_output_tokens": 10,
        },
        "agent_execution": {
            "started_at": "2026-09-24T12:00:00+00:00",
            "finished_at": f"2026-09-24T12:00:{seconds:02d}+00:00",
        },
    }


def trial():
    return {
        **stage(),
        "task_name": "agora/notification-api-compatibility",
        "trial_name": "trial",
        "finished_at": "2026-09-24T12:01:00+00:00",
    }


class EfficiencyScoring(unittest.TestCase):
    def test_correctness_gate_and_efficiency(self):
        fast = trial()
        score = score_trial(fast, [])
        self.assertTrue(score["completed"])
        self.assertEqual(score["total_tokens"], 110)  # Cache is already in input.
        slow = {**fast, **stage(tokens=1000, seconds=50)}
        self.assertGreater(score["reward"], score_trial(slow, [])["reward"])
        failed = {**fast, **stage(correct=0, tokens=0, seconds=0)}
        self.assertEqual(score_trial(failed, [])["reward"], 0)
        self.assertFalse(score_trial(failed, [])["completed"])

    def test_all_steps_required_and_partial_completion_is_zero(self):
        full = trial()
        full["step_results"] = [stage("first"), stage("second")]
        result = score_trial(full, ["first", "second"])
        # Do not count trial totals twice.
        self.assertEqual(result["total_tokens"], 220)
        self.assertEqual(result["agent_seconds"], 20)
        self.assertGreater(result["reward"], 0.8)
        full["step_results"][1] = stage("second", correct=0)
        self.assertEqual(score_trial(full, ["first", "second"])["reward"], 0)
        full["step_results"].pop()
        self.assertIsNone(score_trial(full, ["first", "second"])["reward"])

    def test_infrastructure_or_missing_usage_is_not_a_cheap_success(self):
        broken = trial()
        broken["agent_result"] = None
        self.assertIsNone(score_trial(broken, [])["reward"])
        self.assertTrue(score_trial(broken, [])["completed"])
        for field, value in (
            ("exception_info", {"exception_type": "TimeoutError"}),
            ("finished_at", None),
            ("agent_execution", None),
            ("verifier_result", {"rewards": {"reward": float("nan")}}),
        ):
            with self.subTest(field=field):
                broken = {**trial(), field: value}
                self.assertIsNone(score_trial(broken, [])["reward"])
        broken = trial()
        broken["agent_result"]["n_cache_tokens"] = 1000
        self.assertIsNone(score_trial(broken, [])["reward"])
        broken["agent_result"]["n_input_tokens"] = float("nan")
        json.dumps(score_trial(broken, []), allow_nan=False)
        broken = trial()
        broken["step_results"] = [stage("first"), stage("second")]
        broken["step_results"][1]["exception_info"] = {"exception_type": "ResetError"}
        self.assertIsNone(score_trial(broken, ["first", "second"])["reward"])
        for scale in (0, -1, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                score_trial(trial(), [], token_scale=scale)

    def test_job_report_is_read_only_and_rejects_incomplete_jobs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "trial").mkdir()
            record = trial()
            saved = json.dumps(record)
            (root / "trial/result.json").write_text(saved)
            job = {
                "finished_at": record["finished_at"],
                "n_total_trials": 1,
                "stats": {"n_completed_trials": 1, "n_errored_trials": 0},
            }
            (root / "result.json").write_text(json.dumps(job))
            report = score_job(root)
            self.assertEqual(report["completed_tasks"], 1)
            self.assertGreater(report["mean_reward"], 0.8)
            self.assertEqual((root / "trial/result.json").read_text(), saved)
            missing = deepcopy(job)
            missing["n_total_trials"] = 2
            (root / "result.json").write_text(json.dumps(missing))
            self.assertIsNone(score_job(root)["mean_reward"])
            retried = deepcopy(job)
            retried["stats"]["n_retries"] = 1
            (root / "result.json").write_text(json.dumps(retried))
            self.assertIsNone(score_job(root)["mean_reward"])


if __name__ == "__main__":
    unittest.main()
