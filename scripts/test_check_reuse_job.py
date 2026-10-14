"""Synthetic capture-to-reuse evidence trees exercise every checker rule."""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from dirhash import dirhash

from check_reuse_job import audit_campaign
from check_overlay_job import check_setup


ROOT = Path(__file__).resolve().parents[1]
TASK = "cross-session-framework-reuse"
STEPS = ("rate-limit", "authenticate")
READ_ONLY_TOOLS = {
    "affected_graph",
    "explain_graph",
    "explore_graph",
    "graph_status",
    "list_calls",
    "list_documents",
    "list_knowledge",
    "list_repository_tree",
    "path_graph",
    "query_graph",
    "read_document",
    "read_implementation",
    "read_implementation_graph",
    "read_plan",
    "read_reference",
    "read_repository_file",
    "recall_memory",
    "trace_graph",
    "traverse_knowledge",
}
MUTATING_TOOLS = {
    "anchor_plan",
    "archive_document",
    "ask_plan",
    "attach_artifact",
    "block_task",
    "build_graph",
    "capture_knowledge",
    "claim_job",
    "complete_job",
    "complete_task",
    "create_document",
    "edit_implementation_graph",
    "edit_plan",
    "fail_job",
    "heartbeat_job",
    "ingest",
    "propose",
    "refresh_graph",
    "rename_document",
    "report_pr",
    "report_progress",
    "report_verification",
    "request_revision",
    "restore_document",
    "start_implementation",
    "start_task",
}
TIMES = {
    "rate-limit": ("2026-10-14T00:00:10+00:00", "2026-10-14T00:00:20+00:00"),
    "authenticate": ("2026-10-14T00:00:30+00:00", "2026-10-14T00:00:40+00:00"),
}


def write_json(path, value, lines=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    if lines:
        path.write_text("\n".join(json.dumps(row) for row in value) + "\n")
    else:
        path.write_text(json.dumps(value))


def task_checksum(task=TASK):
    return dirhash(ROOT / "evals" / task, "sha256")


def pins(**changes):
    value = {
        "server_sha": "server-sha",
        "server_drop_sha256": "server-drop",
        "agent_sha": "agent-sha",
        "agent_drop_sha256": "agent-drop",
        "hook_sha256": "hook-sha",
        "hook_version": "1",
        "executor": "ported",
        "agora_tasks_sha": "tasks-sha",
        "task_checksum": task_checksum(),
        "harbor_version": "0.23.0",
        "codex_version": "0.144.3",
        "model": "model",
        "accept": "person",
    }
    value.update(changes)
    return value


def result(reward=1, checksum=None):
    stages = []
    for name in STEPS:
        start, end = TIMES[name]
        stages.append(
            {
                "step_name": name,
                "agent_execution": {"started_at": start, "finished_at": end},
                "agent_result": {
                    "n_input_tokens": 10,
                    "n_cache_tokens": 0,
                    "n_output_tokens": 5,
                },
                "verifier_result": {"rewards": {"reward": reward}},
            }
        )
    return {
        "task_name": f"agora/{TASK}",
        "trial_name": "trial-1",
        "task_checksum": checksum or task_checksum(),
        "finished_at": "2026-10-14T00:00:50+00:00",
        "step_results": stages,
    }


def make_job(root, name="job-1", *, executor="ported", accept="person"):
    job = root / name
    trial = job / "trial-1"
    write_json(
        job / "result.json",
        {
            "job_name": name,
            "started_at": "2026-10-14T00:00:00+00:00",
            "finished_at": "2026-10-14T00:01:00+00:00",
            "n_total_trials": 1,
            "stats": {
                "n_completed_trials": 1,
                "n_errored_trials": 0,
                "n_running_trials": 0,
                "n_pending_trials": 0,
                "n_cancelled_trials": 0,
                "n_retries": 0,
            },
        },
    )
    write_json(trial / "result.json", result())
    product = trial / "environment/product"
    write_json(product / "pins.json", pins(executor=executor, accept=accept))
    write_json(
        product / "principals.json",
        {
            "steps": {"rate-limit": "agent-a", "authenticate": "agent-b"},
            "human": "person-reviewer",
            "executor": "agent-executor",
        },
    )
    write_json(
        product / "capture/rate-limit.jsonl",
        [
            {
                "source_identity": "session-a",
                "cursor": "cursor-1",
                "status": "accepted",
                "job_id": "capture-job",
                "effect": True,
            }
        ],
        lines=True,
    )
    write_json(
        product / "jobs.jsonl",
        [
            {
                "id": "capture-job",
                "state": "settled",
                "claimant": "agent-executor",
                "settled_by": "agent-executor",
            }
        ],
        lines=True,
    )
    write_json(
        product / "proposals.json",
        [
            {
                "id": "proposal-1",
                "revision": 1,
                "claim_ids": ["claim-1"],
                "claim": "Use the registered extension point.",
                "evidence_refs": ["repo://src/microapp/middleware.py"],
                "state_history": [{"state": "accepted"}],
            }
        ],
    )
    write_json(
        product / "acceptance.jsonl",
        [
            {
                "actor_id": "person-reviewer",
                "actor_class": "human",
                "proposal_id": "proposal-1",
                "revision": 1,
                "decision": "accepted",
                "time": "2026-10-14T00:00:25+00:00",
                "policy": accept,
            }
        ],
        lines=True,
    )
    write_json(
        product / "calls.jsonl",
        [
            {
                "tool": "ingest",
                "call_id": "ingest-call",
                "principal": {"id": "agent-a", "source": "turn"},
                "recordedAt": "2026-10-14T00:00:15+00:00",
                "outcome": "succeeded",
            },
            {
                "tool": "settle_capture",
                "call_id": "settle-call",
                "principal": {"id": "agent-executor", "source": "turn"},
                "recordedAt": "2026-10-14T00:00:22+00:00",
                "outcome": "succeeded",
            },
            {
                "tool": "accept_proposal",
                "call_id": "accept-call",
                "principal": {"id": "person-reviewer", "source": "session"},
                "recordedAt": "2026-10-14T00:00:25+00:00",
                "outcome": "succeeded",
            },
            {
                "tool": "recall_memory",
                "call_id": "retrieval-call",
                "principal": {"id": "agent-b", "source": "turn"},
                "recordedAt": "2026-10-14T00:00:35+00:00",
                "outcome": "succeeded",
                "result": {"content": [{"type": "text", "text": "claim-1"}]},
            },
        ],
        lines=True,
    )
    write_json(
        product / "product-usage.json",
        {"source": "agent", "input_tokens": 4, "output_tokens": 2},
    )
    first_instruction = (ROOT / f"evals/{TASK}/steps/{STEPS[0]}/instruction.md").read_text()
    second_instruction = (ROOT / f"evals/{TASK}/steps/{STEPS[1]}/instruction.md").read_text()
    for step, instruction in zip(STEPS, (first_instruction, second_instruction), strict=True):
        trajectory = {
            "session_id": "session-a" if step == STEPS[0] else "session-b",
            "steps": [
                {"source": "user", "message": instruction},
                {
                    "source": "agent",
                    "message": "Applied the retrieved convention.",
                    "file_edits": (
                        [
                            {
                                "path": "/app/src/microapp/middleware.py",
                                "principal": {"id": "agent-b"},
                            }
                        ]
                        if step == STEPS[1]
                        else []
                    ),
                },
            ]
        }
        write_json(trial / f"steps/{step}/agent/trajectory.json", trajectory)
        stream = []
        if step == STEPS[1]:
            stream.append(
                {
                    "type": "item.completed",
                    "item": {
                        "type": "mcp_tool_call",
                        "id": "retrieval-call",
                        "principal": {"id": "agent-b"},
                        "server": "agora",
                        "tool": "recall_memory",
                        "status": "completed",
                        "error": None,
                        "result": {"content": [{"type": "text", "text": "claim-1"}]},
                    },
                }
            )
            stream.append(
                {
                    "type": "item.completed",
                    "item": {
                        "type": "file_change",
                        "status": "completed",
                        "changes": [
                            {
                                "path": "/app/src/microapp/middleware.py",
                                "kind": "update",
                                "principal": {"id": "agent-b"},
                            }
                        ],
                    },
                }
            )
        write_json(trial / f"steps/{step}/agent/codex.txt", stream, lines=True)
    return job, trial


class ReuseEvidence(unittest.TestCase):
    def test_happy_path_is_pending_then_verified(self):
        with tempfile.TemporaryDirectory() as directory:
            job, trial = make_job(Path(directory))
            report = audit_campaign([job], receipt=True)
            self.assertEqual(report["trials"][0]["reuse"], "pending-review")
            self.assertFalse(report["trials"][0]["cited"])
            review = trial / "environment/product/review.md"
            self.assertFalse(review.exists())
            self.assertEqual(report["written_files"], [])
            self.assertEqual(report["trials"][0]["review"]["suggested_path"], str(review))
            self.assertIn("claim-1", report["trials"][0]["review"]["template"])
            output = Path(directory) / "review.md"
            report = audit_campaign([job], receipt=True, review_output=output)
            self.assertEqual(report["written_files"], [str(output)])
            self.assertIn("claim-1", output.read_text())
            write_json(
                review.with_suffix(".json"),
                {
                    "reviewer": "reviewer",
                    "verdict": "applies",
                    "time": "2026-10-14T00:02:00+00:00",
                },
            )
            self.assertEqual(
                audit_campaign([job], receipt=True)["trials"][0]["reuse"],
                "verified",
            )

    def test_job_summary_validity_flags_are_required(self):
        cases = (
            ("finished_at", None, "finished"),
            ("n_completed_trials", 0, "completed"),
            ("n_errored_trials", 1, "infrastructure"),
            ("n_running_trials", 1, "partial"),
            ("n_pending_trials", 1, "partial"),
            ("n_cancelled_trials", 1, "partial"),
            ("n_retries", 1, "retried"),
        )
        for field, value, message in cases:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                job, _ = make_job(Path(directory))
                summary = json.loads((job / "result.json").read_text())
                target = summary if field == "finished_at" else summary["stats"]
                target[field] = value
                write_json(job / "result.json", summary)
                with self.assertRaisesRegex(ValueError, message):
                    audit_campaign([job], receipt=True)

    def test_only_catalog_reads_can_retrieve_claims(self):
        self.assertEqual(len(READ_ONLY_TOOLS), 19)
        self.assertEqual(len(MUTATING_TOOLS), 26)
        self.assertFalse(READ_ONLY_TOOLS & MUTATING_TOOLS)
        cases = [(name, True) for name in sorted(READ_ONLY_TOOLS)]
        cases += [(name, False) for name in sorted(MUTATING_TOOLS)]
        cases += [("accept_proposal", False), ("unknown_tool", False)]
        for tool, allowed in cases:
            with self.subTest(tool=tool), tempfile.TemporaryDirectory() as directory:
                job, trial = make_job(Path(directory))
                stream = trial / f"steps/{STEPS[1]}/agent/codex.txt"
                events = [json.loads(line) for line in stream.read_text().splitlines()]
                events[0]["item"]["tool"] = tool
                write_json(stream, events, lines=True)
                calls = trial / "environment/product/calls.jsonl"
                rows = [json.loads(line) for line in calls.read_text().splitlines()]
                rows[-1]["tool"] = tool
                write_json(calls, rows, lines=True)
                if allowed:
                    self.assertEqual(
                        audit_campaign([job], receipt=True)["trials"][0]["reuse"],
                        "pending-review",
                    )
                else:
                    with self.assertRaisesRegex(ValueError, "read-only retrieval"):
                        audit_campaign([job], receipt=True)

    def test_pins_are_complete_consistent_and_match_the_trial(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            job, trial = make_job(root)
            path = trial / "environment/product/pins.json"
            original = json.loads(path.read_text())
            for change, message in (
                ({key: value for key, value in original.items() if key != "hook_sha256"}, "pins"),
                ({**original, "task_checksum": "wrong"}, "task_checksum"),
            ):
                path.write_text(json.dumps(change))
                with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                    audit_campaign([job])
            path.write_text(json.dumps(original))
            second, second_trial = make_job(root, "job-2")
            mixed = json.loads((second_trial / "environment/product/pins.json").read_text())
            mixed["model"] = "different"
            write_json(second_trial / "environment/product/pins.json", mixed)
            with self.assertRaisesRegex(ValueError, "mixed pins"):
                audit_campaign([job, second])

    def test_receipt_refuses_fixture_but_plumbing_labels_it(self):
        with tempfile.TemporaryDirectory() as directory:
            job, _ = make_job(
                Path(directory), executor="fixture-v1", accept="scripted-console-v1"
            )
            with self.assertRaisesRegex(ValueError, "ported"):
                audit_campaign([job], receipt=True)
            report = audit_campaign([job])
            self.assertEqual(report["classification"], "plumbing")
            self.assertEqual(report["accept"], "scripted-console-v1")

    def test_principals_and_agent_windows_are_isolated(self):
        with tempfile.TemporaryDirectory() as directory:
            job, trial = make_job(Path(directory))
            path = trial / "environment/product/principals.json"
            principals = json.loads(path.read_text())
            principals["steps"][STEPS[1]] = principals["steps"][STEPS[0]]
            write_json(path, principals)
            with self.assertRaisesRegex(ValueError, "distinct"):
                audit_campaign([job])
            principals["steps"][STEPS[1]] = "agent-b"
            write_json(path, principals)
            acceptance = trial / "environment/product/acceptance.jsonl"
            row = json.loads(acceptance.read_text())
            write_json(acceptance, [{**row, "actor_class": "agent"}], lines=True)
            audit_campaign([job])
            write_json(acceptance, [row], lines=True)
            calls = trial / "environment/product/calls.jsonl"
            records = [json.loads(line) for line in calls.read_text().splitlines()]
            records[0]["principal"]["id"] = "agent-b"
            write_json(calls, records, lines=True)
            with self.assertRaisesRegex(ValueError, "window"):
                audit_campaign([job])

    def test_acceptance_class_comes_from_the_call_credential(self):
        with tempfile.TemporaryDirectory() as directory:
            job, trial = make_job(Path(directory))
            calls = trial / "environment/product/calls.jsonl"
            records = [json.loads(line) for line in calls.read_text().splitlines()]
            records[2]["principal"]["source"] = "bearer"
            write_json(calls, records, lines=True)
            with self.assertRaisesRegex(ValueError, "human credential"):
                audit_campaign([job], receipt=True)

            principals = trial / "environment/product/principals.json"
            declared = json.loads(principals.read_text())
            declared["human"] = declared["executor"]
            write_json(principals, declared)
            acceptance = trial / "environment/product/acceptance.jsonl"
            accepted = json.loads(acceptance.read_text())
            accepted["actor_id"] = declared["executor"]
            accepted["actor_class"] = "human"
            write_json(acceptance, [accepted], lines=True)
            with self.assertRaisesRegex(ValueError, "human credential"):
                audit_campaign([job], receipt=True)

    def test_only_an_accepted_claim_is_a_reuse_event(self):
        with tempfile.TemporaryDirectory() as directory:
            job, trial = make_job(Path(directory))
            path = trial / "environment/product/proposals.json"
            proposal = json.loads(path.read_text())[0]
            acceptance = trial / "environment/product/acceptance.jsonl"
            accepted = json.loads(acceptance.read_text())
            for state in ("pending", "rejected", "superseded"):
                write_json(path, [{**proposal, "state_history": [{"state": state}]}])
                write_json(acceptance, [{**accepted, "decision": state}], lines=True)
                with self.subTest(state=state):
                    self.assertEqual(audit_campaign([job])["trials"][0]["reuse"], "absent")

    def test_explicit_citation_is_reported_but_not_required(self):
        with tempfile.TemporaryDirectory() as directory:
            job, trial = make_job(Path(directory))
            report = audit_campaign([job])
            self.assertFalse(report["trials"][0]["cited"])
            trajectory = trial / f"steps/{STEPS[1]}/agent/trajectory.json"
            atif = json.loads(trajectory.read_text())
            atif["steps"][-1]["message"] += " Claim: claim-1."
            write_json(trajectory, atif)
            self.assertTrue(audit_campaign([job])["trials"][0]["cited"])

    def test_edit_must_follow_the_retrieval(self):
        with tempfile.TemporaryDirectory() as directory:
            job, trial = make_job(Path(directory))
            stream = trial / f"steps/{STEPS[1]}/agent/codex.txt"
            events = [json.loads(line) for line in stream.read_text().splitlines()]
            write_json(stream, list(reversed(events)), lines=True)
            self.assertEqual(
                audit_campaign([job])["trials"][0]["reuse"],
                "retrieved-unapplied",
            )

    def test_edit_must_belong_to_the_retrieving_principal(self):
        with tempfile.TemporaryDirectory() as directory:
            job, trial = make_job(Path(directory))
            trajectory = trial / f"steps/{STEPS[1]}/agent/trajectory.json"
            atif = json.loads(trajectory.read_text())
            atif["steps"][-1]["file_edits"][0]["principal"]["id"] = "agent-c"
            write_json(trajectory, atif)
            stream = trial / f"steps/{STEPS[1]}/agent/codex.txt"
            events = [json.loads(line) for line in stream.read_text().splitlines()]
            events[-1]["item"]["changes"][0]["principal"]["id"] = "agent-c"
            write_json(stream, events, lines=True)
            self.assertEqual(
                audit_campaign([job])["trials"][0]["reuse"],
                "retrieved-unapplied",
            )

    def test_edit_must_touch_the_claims_cited_file(self):
        with tempfile.TemporaryDirectory() as directory:
            job, trial = make_job(Path(directory))
            trajectory = trial / f"steps/{STEPS[1]}/agent/trajectory.json"
            atif = json.loads(trajectory.read_text())
            atif["steps"][-1]["file_edits"][0]["path"] = "/app/src/unrelated.py"
            write_json(trajectory, atif)
            stream = trial / f"steps/{STEPS[1]}/agent/codex.txt"
            events = [json.loads(line) for line in stream.read_text().splitlines()]
            events[-1]["item"]["changes"][0]["path"] = "/app/src/unrelated.py"
            write_json(stream, events, lines=True)
            self.assertEqual(
                audit_campaign([job])["trials"][0]["reuse"],
                "retrieved-unapplied",
            )

    def test_retrieval_call_log_row_must_have_the_same_call_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            job, trial = make_job(Path(directory))
            stream = trial / f"steps/{STEPS[1]}/agent/codex.txt"
            events = [json.loads(line) for line in stream.read_text().splitlines()]
            events[0]["item"]["id"] = "retrieval-with-claim"
            write_json(stream, events, lines=True)
            calls = trial / "environment/product/calls.jsonl"
            records = [json.loads(line) for line in calls.read_text().splitlines()]
            records[-1]["call_id"] = "different-call"
            records[-1]["result"] = {
                "content": [{"type": "text", "text": "unrelated"}]
            }
            write_json(calls, records, lines=True)
            with self.assertRaisesRegex(ValueError, "call log"):
                audit_campaign([job], receipt=True)

    def test_retrieval_call_log_row_binds_principal_and_claim(self):
        for field, value in (
            ("principal", {"id": "agent-c", "source": "turn"}),
            ("result", {"content": [{"type": "text", "text": "unrelated"}]}),
        ):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                job, trial = make_job(Path(directory))
                calls = trial / "environment/product/calls.jsonl"
                records = [json.loads(line) for line in calls.read_text().splitlines()]
                records[-1][field] = value
                write_json(calls, records, lines=True)
                with self.assertRaisesRegex(ValueError, "call log"):
                    audit_campaign([job], receipt=True)

    def test_failed_verifier_is_not_verified(self):
        with tempfile.TemporaryDirectory() as directory:
            job, trial = make_job(Path(directory))
            write_json(trial / "result.json", result(reward=0))
            self.assertEqual(
                audit_campaign([job])["trials"][0]["reuse"], "failed-verifier"
            )

    def test_task_checksum_is_computed_and_verifier_edits_are_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            job, trial = make_job(Path(directory))
            pin_path = trial / "environment/product/pins.json"
            pinned = json.loads(pin_path.read_text())
            pinned["task_checksum"] = "archive-controlled"
            write_json(pin_path, pinned)
            record_path = trial / "result.json"
            record = json.loads(record_path.read_text())
            record["task_checksum"] = "archive-controlled"
            write_json(record_path, record)
            with self.assertRaisesRegex(ValueError, "suite task checksum"):
                audit_campaign([job], receipt=True)

            pinned["task_checksum"] = task_checksum()
            write_json(pin_path, pinned)
            record["task_checksum"] = task_checksum()
            write_json(record_path, record)
            target = "/app/steps/authenticate/tests/test_behavior.py"
            trajectory = trial / f"steps/{STEPS[1]}/agent/trajectory.json"
            atif = json.loads(trajectory.read_text())
            atif["steps"][-1]["file_edits"].append(
                {"path": target, "principal": {"id": "agent-b"}}
            )
            write_json(trajectory, atif)
            stream = trial / f"steps/{STEPS[1]}/agent/codex.txt"
            events = [json.loads(line) for line in stream.read_text().splitlines()]
            events[-1]["item"]["changes"].append(
                {"path": target, "kind": "update", "principal": {"id": "agent-b"}}
            )
            write_json(stream, events, lines=True)
            with self.assertRaisesRegex(ValueError, "verifier"):
                audit_campaign([job], receipt=True)

    def test_instruction_must_match_and_must_not_contain_the_proposal(self):
        with tempfile.TemporaryDirectory() as directory:
            job, trial = make_job(Path(directory))
            trajectory = trial / f"steps/{STEPS[1]}/agent/trajectory.json"
            atif = json.loads(trajectory.read_text())
            atif["steps"][0]["message"] += " injected"
            write_json(trajectory, atif)
            with self.assertRaisesRegex(ValueError, "instruction"):
                audit_campaign([job])
            atif["steps"][0]["message"] = (
                ROOT / f"evals/{TASK}/steps/{STEPS[1]}/instruction.md"
            ).read_text()
            proposal = json.loads(
                (trial / "environment/product/proposals.json").read_text()
            )[0]
            proposal["claim"] = atif["steps"][0]["message"]
            write_json(trial / "environment/product/proposals.json", [proposal])
            write_json(trajectory, atif)
            with self.assertRaisesRegex(ValueError, "overlap"):
                audit_campaign([job], overlap_threshold=0.2)
            proposal["claim"] = atif["steps"][0]["message"] + " " + " ".join(
                f"padding{index}" for index in range(300)
            )
            write_json(trial / "environment/product/proposals.json", [proposal])
            with self.assertRaisesRegex(ValueError, "overlap"):
                audit_campaign([job])

    def test_duplicate_capture_is_one_effect_only(self):
        with tempfile.TemporaryDirectory() as directory:
            job, trial = make_job(Path(directory))
            capture = trial / "environment/product/capture/rate-limit.jsonl"
            row = json.loads(capture.read_text())
            write_json(capture, [row, {**row, "effect": False}], lines=True)
            audit_campaign([job])
            write_json(capture, [row, row], lines=True)
            with self.assertRaisesRegex(ValueError, "one effect"):
                audit_campaign([job])

    def test_product_phase_order_is_additive(self):
        def timing(start, end):
            return {
                "started_at": f"2026-10-14T00:00:{start:02d}+00:00",
                "finished_at": f"2026-10-14T00:00:{end:02d}+00:00",
            }

        with tempfile.TemporaryDirectory() as directory:
            trial = Path(directory)
            stages = [
                {
                    "step_name": STEPS[0],
                    "agent_execution": timing(5, 6),
                    "verifier": timing(8, 9),
                },
                {
                    "step_name": STEPS[1],
                    "agent_execution": timing(13, 14),
                    "verifier": timing(15, 16),
                },
            ]
            record = {
                "environment_setup": timing(0, 2),
                "step_results": stages,
            }
            phases = []
            for phase, step, start, end in (
                ("common", None, 0, 1),
                ("install", None, 1, 2),
                ("index", STEPS[0], 3, 4),
                ("capture", STEPS[0], 6, 7),
                ("accept", STEPS[1], 10, 11),
                ("index", STEPS[1], 11, 12),
            ):
                phases.append(
                    {
                        "phase": phase,
                        "step": step,
                        "arm": "agora",
                        "return_code": 0,
                        **timing(start, end),
                        "seconds": end - start,
                    }
                )
            write_json(trial / "environment/setup.jsonl", phases, lines=True)
            for step in STEPS:
                (trial / f"environment/steps/{step}").mkdir(parents=True)
                (trial / f"environment/steps/{step}/index.stdout.log").write_text("ready")
            with patch("check_overlay_job.check_index", return_value={"nodes": 1}):
                self.assertEqual(len(check_setup(trial, record)["phases"]), 6)
            for row in phases:
                row["arm"] = "baseline"
            write_json(trial / "environment/setup.jsonl", phases, lines=True)
            with self.assertRaisesRegex(ValueError, "setup phases"):
                check_setup(trial, record)


if __name__ == "__main__":
    unittest.main()
