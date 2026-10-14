"""The capture-reuse scorecard keeps raw paired dimensions and refuses gaps."""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from score_job import score_job
from score_reuse import score_campaign
from test_check_reuse_job import STEPS, make_job, task_checksum, write_json


def setup_phases(trial, arm, steps=STEPS):
    phases = []
    for phase, step, seconds in (
        ("common", None, 1),
        ("install", None, 1),
        ("index", steps[0], 1),
        ("capture", steps[0], 2),
        ("accept", steps[1], 3),
        ("index", steps[1], 1),
    ):
        phases.append({"phase": phase, "step": step, "arm": arm, "seconds": seconds})
    write_json(trial / "environment/setup.jsonl", phases, lines=True)


def scored_job(root, name, arm, tokens, *, product_tokens=(4, 2), source="agent"):
    job, trial = make_job(
        root,
        name,
        executor="fixture-v1" if source == "fixture" else "ported",
        accept="scripted-console-v1",
    )
    record = json.loads((trial / "result.json").read_text())
    record["trial_name"] = name
    for stage, count in zip(record["step_results"], tokens, strict=True):
        stage["agent_result"] = {
            "n_input_tokens": count,
            "n_cache_tokens": 0,
            "n_output_tokens": 10,
        }
    write_json(trial / "result.json", record)
    setup_phases(trial, arm)
    if arm == "baseline":
        product = trial / "environment/product"
        for path in sorted(product.rglob("*"), reverse=True):
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                path.rmdir()
        product.rmdir()
        for step in STEPS:
            (trial / f"steps/{step}/agent/codex.txt").write_text("")
    else:
        write_json(
            trial / "environment/product/product-usage.json",
            {
                "source": source,
                "input_tokens": product_tokens[0],
                "output_tokens": product_tokens[1],
            },
        )
    return job, trial


def retask_as_deduplication(trial, arm):
    old_steps = STEPS
    new_steps = ("accounts", "emails")
    record = json.loads((trial / "result.json").read_text())
    record["task_name"] = "agora/cross-session-deduplication-reuse"
    record["task_checksum"] = task_checksum("cross-session-deduplication-reuse")
    for stage, name in zip(record["step_results"], new_steps, strict=True):
        stage["step_name"] = name
    write_json(trial / "result.json", record)
    for old, new in zip(old_steps, new_steps, strict=True):
        (trial / f"steps/{old}").rename(trial / f"steps/{new}")
        atif = trial / f"steps/{new}/agent/trajectory.json"
        value = json.loads(atif.read_text())
        value["steps"][0]["message"] = (
            Path(__file__).resolve().parents[1]
            / f"evals/cross-session-deduplication-reuse/steps/{new}/instruction.md"
        ).read_text()
        if new == new_steps[1]:
            value["steps"][-1]["file_edits"] = [
                {
                    "path": "/app/src/recordkit/canonical.py",
                    "principal": {"id": "agent-b"},
                }
            ]
        write_json(atif, value)
    if arm == "agora":
        product = trial / "environment/product"
        pins = json.loads((product / "pins.json").read_text())
        pins["task_checksum"] = record["task_checksum"]
        write_json(product / "pins.json", pins)
        principals = json.loads((product / "principals.json").read_text())
        principals["steps"] = dict(zip(new_steps, principals["steps"].values(), strict=True))
        write_json(product / "principals.json", principals)
        proposal = json.loads((product / "proposals.json").read_text())[0]
        proposal["evidence_refs"] = ["repo://src/recordkit/canonical.py"]
        write_json(product / "proposals.json", [proposal])
        stream = trial / f"steps/{new_steps[1]}/agent/codex.txt"
        events = [json.loads(line) for line in stream.read_text().splitlines()]
        events[-1]["item"]["changes"][0]["path"] = "/app/src/recordkit/canonical.py"
        write_json(stream, events, lines=True)
    setup_phases(trial, arm, new_steps)


class ReuseScoring(unittest.TestCase):
    def test_methodology_only_claims_scores_from_supplied_jobs(self):
        methodology = (
            Path(__file__).resolve().parents[1] / "docs/methodology.md"
        ).read_text()
        self.assertIn(
            "`completion-efficiency-v1` mean recomputed from the supplied jobs",
            methodology,
        )

    def test_raw_dimensions_pair_costs_and_existing_composite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline, _ = scored_job(root, "baseline-1", "baseline", (100, 200))
            product, _ = scored_job(root, "product-1", "agora", (80, 100))
            report = score_campaign([baseline, product])
            self.assertFalse(report["errors"])
            cells = {cell["arm"]: cell for cell in report["cells"]}
            self.assertEqual(cells["baseline"]["tokens"]["pair_mean"], 320)
            self.assertEqual(cells["agora"]["tokens"]["pair_mean"], 200)
            self.assertEqual(cells["agora"]["tokens"]["product_mean"], 6)
            self.assertEqual(report["tokens_saved"][0]["mean"], 114)
            self.assertEqual(
                cells["baseline"]["completion_composite"]["mean"],
                score_job(baseline)["mean_reward"],
            )
            self.assertEqual(
                report["arms"]["baseline"]["completion_composite"]["mean"],
                score_job(baseline)["mean_reward"],
            )
            self.assertEqual(cells["agora"]["time"]["capture_mean"], 2)
            self.assertEqual(cells["agora"]["time"]["accept_mean"], 3)

    def test_pre_overlay_baseline_keeps_the_legacy_composite(self):
        with tempfile.TemporaryDirectory() as directory:
            baseline, trial = scored_job(
                Path(directory), "baseline-1", "baseline", (100, 200)
            )
            (trial / "environment/setup.jsonl").unlink()
            report = score_campaign([baseline])
            self.assertFalse(report["errors"])
            self.assertEqual(
                report["cells"][0]["completion_composite"]["mean"],
                score_job(baseline)["mean_reward"],
            )

    def test_missing_usage_baseline_cell_and_retries_are_not_imputed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline, _ = scored_job(root, "baseline-1", "baseline", (100, 200))
            product, trial = scored_job(root, "product-1", "agora", (80, 100))
            usage = trial / "environment/product/product-usage.json"
            usage.unlink()
            report = score_campaign([baseline, product])
            product_cell = next(c for c in report["cells"] if c["arm"] == "agora")
            self.assertIsNone(product_cell["completion_composite"]["mean"])
            self.assertTrue(report["errors"])
            write_json(
                usage,
                {"source": "agent", "input_tokens": 4, "output_tokens": 2},
            )
            self.assertIsNone(score_campaign([product])["tokens_saved"])
            summary = json.loads((product / "result.json").read_text())
            summary["stats"]["n_retries"] = 1
            write_json(product / "result.json", summary)
            self.assertTrue(score_campaign([baseline, product])["errors"])

    def test_fixture_usage_is_zero_and_labeled(self):
        with tempfile.TemporaryDirectory() as directory:
            product, _ = scored_job(
                Path(directory),
                "product-1",
                "agora",
                (80, 100),
                product_tokens=(99, 99),
                source="fixture",
            )
            cell = score_campaign([product])["cells"][0]
            self.assertEqual(cell["tokens"]["product_mean"], 0)
            self.assertEqual(cell["tokens"]["product_source"], {"fixture": 1})

    def test_protocol_requires_declared_complete_unique_jobs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            jobs = []
            for arm in ("baseline", "agora"):
                for attempt in range(3):
                    job, _ = scored_job(
                        root,
                        f"{arm}-{attempt}",
                        arm,
                        (100, 200),
                    )
                    jobs.append(job)
            with self.assertRaisesRegex(ValueError, "declared count"):
                score_campaign(jobs, protocol=True)
            with self.assertRaisesRegex(ValueError, "12 jobs"):
                score_campaign(jobs, protocol=True, count=6)
            duplicate = deepcopy(jobs * 2)
            with self.assertRaisesRegex(ValueError, "unique"):
                score_campaign(duplicate, protocol=True, count=12)

    def test_complete_protocol_has_three_attempts_per_cell(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            jobs = []
            for task in ("framework", "deduplication"):
                for arm in ("baseline", "agora"):
                    for attempt in range(3):
                        job, trial = scored_job(
                            root,
                            f"{task}-{arm}-{attempt}",
                            arm,
                            (100, 200),
                        )
                        if task == "deduplication":
                            retask_as_deduplication(trial, arm)
                        jobs.append(job)
            report = score_campaign(jobs, protocol=True, count=12)
            self.assertFalse(report["errors"])
            self.assertEqual({cell["n"] for cell in report["cells"]}, {3})


if __name__ == "__main__":
    unittest.main()
