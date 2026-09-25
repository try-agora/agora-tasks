"""Check native config compatibility without containers, tools, or model calls."""

from pathlib import Path
import asyncio
from copy import deepcopy
import json
import shutil
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock, patch

from harbor.cli.utils import load_mcp_servers
from harbor.models.job.config import JobConfig
from harbor.trial.trial import Trial
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from overlays.environment import (  # noqa: E402
    OverlayEnvironment,
    StepIndexPlugin,
    _environments,
    _hooked_jobs,
)
from check_overlay_job import inspect, inspect_oracle  # noqa: E402
from overlays.readiness import check_index  # noqa: E402


class OverlayConfig(unittest.TestCase):
    def test_reference_coverage_rejects_duplicates(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch("check_overlay_job.check_job") as check,
            patch(
                "check_overlay_job.check_setup",
                return_value={
                    "arm": "baseline",
                    "index_readiness": {"single": {"graph_required": False}},
                },
            ),
        ):
            job = Path(directory)
            for name in ("trial-1", "trial-2"):
                (job / name).mkdir()
                (job / name / "result.json").write_text(
                    json.dumps({"task_name": "agora/checkout-discount-once"})
                )
            with self.assertRaisesRegex(ValueError, "Duplicate task"):
                inspect_oracle(job, 2)
            check.assert_called_once_with(job, expected=1, count=2)
            (job / "trial-2/result.json").write_text(
                json.dumps({"task_name": "agora/middleware-authentication"})
            )
            self.assertEqual(inspect_oracle(job, 2)["stages_checked"], 2)

    def test_installation_locks(self):
        locks = ROOT / "overlays/locks"
        for arm in ("common", "codegraph", "gitnexus"):
            manifest = json.loads((locks / arm / "package.json").read_text())
            lock = json.loads((locks / arm / "package-lock.json").read_text())
            self.assertEqual(lock["lockfileVersion"], 3)
            self.assertEqual(
                manifest["dependencies"], lock["packages"][""]["dependencies"]
            )
            for name, package in lock["packages"].items():
                if name:
                    self.assertTrue(
                        package["resolved"].startswith("https://registry.npmjs.org/")
                    )
                    self.assertTrue(package["integrity"].startswith("sha512-"))
            for name, version in manifest["dependencies"].items():
                self.assertEqual(
                    lock["packages"][f"node_modules/{name}"]["version"], version
                )
        requirements = (locks / "graphify.txt").read_text().splitlines()
        self.assertIn("--python-version 3.12", requirements[1])
        pinned = [
            i for i, line in enumerate(requirements) if line and line[0].isalnum()
        ]
        self.assertGreater(len(pinned), 1)
        for i in pinned:
            self.assertIn("==", requirements[i])
            self.assertTrue(requirements[i + 1].strip().startswith("--hash=sha256:"))

    def test_step_hook_order_isolation_and_failure(self):
        async def scenario(directory):
            env = object.__new__(OverlayEnvironment)
            env.step_names = ["first", "second"]
            env.indexed_steps = []
            env._phase = AsyncMock()
            job = SimpleNamespace(job_dir=Path(directory), on_agent_started=Mock())
            plugin = StepIndexPlugin()
            await plugin.on_job_start(job)
            self.assertIn(job.job_dir.resolve(), _hooked_jobs)
            job.on_agent_started.assert_called_once_with(plugin.before_agent)
            key = job.job_dir / "trial"
            _environments[key.resolve()] = env
            event = SimpleNamespace(
                trial_name="trial",
                config=SimpleNamespace(
                    trials_dir=job.job_dir,
                    agent=SimpleNamespace(resume_trajectory=False),
                ),
                result=SimpleNamespace(
                    step_results=[SimpleNamespace(step_name="first")]
                ),
            )
            await plugin.before_agent(event)
            env._phase.assert_awaited_once_with("index", "agent", step="first")
            self.assertEqual(env.indexed_steps, ["first"])
            with self.assertRaisesRegex(ValueError, "repeated"):
                await plugin.before_agent(event)
            event.result.step_results.append(SimpleNamespace(step_name="second"))
            env._phase.side_effect = RuntimeError("index failed")
            with self.assertRaisesRegex(RuntimeError, "index failed"):
                await plugin.before_agent(event)
            # Exercise Harbor's real phase entrypoint: hook failure must stop
            # execution before it starts either the agent context or its timer.
            trial = SimpleNamespace(_emit=lambda _: plugin.before_agent(event))
            target = SimpleNamespace(agent_result=None, agent_execution=None)
            with self.assertRaisesRegex(RuntimeError, "index failed"):
                await Trial._run_agent_phase(
                    trial,
                    target=target,
                    instruction="unused",
                    timeout_sec=1,
                    user="agent",
                )
            self.assertIsNone(target.agent_result)
            self.assertIsNone(target.agent_execution)
            self.assertEqual(env.indexed_steps, ["first"])
            env._phase.side_effect = None
            await plugin.before_agent(event)
            self.assertEqual(env.indexed_steps, ["first", "second"])
            event.trial_name = "other-trial"
            with self.assertRaisesRegex(RuntimeError, "No live"):
                await plugin.before_agent(event)
            event.config.agent.resume_trajectory = True
            with self.assertRaisesRegex(ValueError, "fresh conversations"):
                await plugin.before_agent(event)
            await plugin.on_job_end(None)
            self.assertNotIn(job.job_dir.resolve(), _hooked_jobs)

        with tempfile.TemporaryDirectory() as directory:
            asyncio.run(scenario(directory))

    def test_native_configs(self):
        baseline = JobConfig.model_validate(
            yaml.safe_load((ROOT / "overlays/baseline.yaml").read_text())
        )
        self.assertEqual(len(baseline.agents), 1)
        agent = baseline.agents[0]
        self.assertEqual(agent.name, "codex")
        self.assertEqual(agent.model_name, "openai/gpt-5.6-luna")
        self.assertEqual(agent.kwargs["version"], "0.144.3")
        self.assertFalse(agent.mcp_servers)
        smoke = JobConfig.model_validate(
            yaml.safe_load((ROOT / "overlays/smoke.yaml").read_text())
        )
        self.assertEqual(smoke.agents, baseline.agents)
        self.assertEqual(
            smoke.environment.import_path, "overlays.environment:OverlayEnvironment"
        )
        self.assertEqual(smoke.environment.override_memory_mb, 4096)
        for name, (command, args) in {
            "codegraph": ("codegraph", ["serve", "--mcp", "--path", "/app"]),
            "gitnexus": ("gitnexus", ["mcp"]),
            "graphify": (
                "graphify-mcp",
                ["/app/graphify-out/graph.json", "--transport", "stdio"],
            ),
            "codebase-memory-mcp": ("codebase-memory-mcp", []),
        }.items():
            with self.subTest(arm=name):
                servers = load_mcp_servers(ROOT / "overlays" / f"{name}.mcp.json")
                self.assertEqual(len(servers), 1)
                server = servers[0]
                self.assertEqual(server.name, name)
                self.assertEqual(server.command, command)
                self.assertEqual(server.args, args)
                self.assertEqual(server.transport, "stdio")

    def test_setup_evidence_and_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            env = object.__new__(OverlayEnvironment)
            env.arm = "graphify"
            env.trial_paths = SimpleNamespace(trial_dir=Path(directory))
            env.exec = AsyncMock(
                return_value=SimpleNamespace(
                    return_code=0, stdout="Rebuilt: 4 nodes, 6 edges", stderr=""
                )
            )
            asyncio.run(env._phase("index", "agent"))
            env.exec.assert_awaited_once_with(
                "bash /opt/benchmark-overlay/setup.sh index graphify",
                cwd="/app",
                user="agent",
                timeout_sec=900,
            )
            record = json.loads(
                (Path(directory) / "environment/setup.jsonl").read_text()
            )
            self.assertEqual(record["return_code"], 0)
            self.assertGreaterEqual(record["seconds"], 0)
            self.assertEqual(record["index_readiness"]["nodes"], 4)
            env.exec.return_value.stdout = "Rebuilt: 0 nodes, 0 edges"
            with self.assertRaisesRegex(ValueError, "Empty or invalid"):
                asyncio.run(env._phase("index", "agent"))
            env.exec.return_value.return_code = 1
            with self.assertRaises(RuntimeError):
                asyncio.run(env._phase("index", "agent"))
            records = (
                (Path(directory) / "environment/setup.jsonl").read_text().splitlines()
            )
            self.assertEqual(json.loads(records[-1])["error"], "RuntimeError")

    def test_usage_and_initialization_audit(self):
        native = {
            "input_tokens": 100,
            "cached_input_tokens": 50,
            "output_tokens": 10,
            "total_tokens": 110,
        }
        atif = {
            "final_metrics": {
                "total_prompt_tokens": 100,
                "total_cached_tokens": 50,
                "total_completion_tokens": 10,
            }
        }

        def timestamp(second):
            return f"2026-09-24T00:00:{second:02d}+00:00"

        result = {
            "started_at": timestamp(0),
            "finished_at": timestamp(8),
            "environment_setup": {
                "started_at": timestamp(0),
                "finished_at": timestamp(4),
            },
            "agent_execution": {
                "started_at": timestamp(5),
                "finished_at": timestamp(7),
            },
            "agent_result": {
                "n_input_tokens": 100,
                "n_cache_tokens": 50,
                "n_output_tokens": 10,
            },
        }
        phases = [
            {
                "phase": phase,
                "arm": "baseline",
                "return_code": 0,
                "started_at": timestamp(i),
                "finished_at": timestamp(i + 1),
                "seconds": 1,
            }
            for i, phase in enumerate(["common", "install", "index"])
        ]
        score = {
            "errors": [],
            "trials": [
                {
                    "completed": True,
                    "reward": 0.9,
                    "total_tokens": 110,
                    "agent_seconds": 2,
                }
            ],
        }
        with (
            tempfile.TemporaryDirectory() as directory,
            patch("check_overlay_job.score_job", return_value=score),
        ):
            job = Path(directory)
            trial = job / "trial"

            def write(relative, data):
                path = trial / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(data if isinstance(data, str) else json.dumps(data))

            write("result.json", result)
            write("agent/trajectory.json", atif)
            write(
                "agent/sessions/session.jsonl",
                {
                    "payload": {
                        "type": "token_count",
                        "info": {"total_token_usage": native},
                    }
                },
            )
            write("agent/codex.txt", {"type": "turn.completed", "usage": native})
            write("environment/setup.jsonl", "\n".join(map(json.dumps, phases)))
            write(
                "environment/index.stdout.log", "No graph; baseline uses shell search."
            )
            self.assertTrue(inspect(job)["usage_reconciled"])
            atif["final_metrics"]["total_cached_tokens"] += 1
            write("agent/trajectory.json", atif)
            with self.assertRaisesRegex(ValueError, "accounting mismatch"):
                inspect(job)
            atif["final_metrics"]["total_cached_tokens"] -= 1
            write("agent/trajectory.json", atif)
            for phase in phases:
                phase["arm"] = "graphify"
            write("environment/setup.jsonl", "\n".join(map(json.dumps, phases)))
            write("environment/index.stdout.log", "Rebuilt: 4 nodes, 6 edges")
            with self.assertRaisesRegex(ValueError, "No completed MCP call"):
                inspect(job)

            # Exercise the same reconciliation through every stage and trial.
            phases = phases[:2]
            for phase in phases:
                phase["arm"] = "baseline"
            stages = []
            for name, start in (("first", 4), ("second", 8)):
                stage = deepcopy(result)
                stage["step_name"] = name
                stage["agent_execution"] = {
                    "started_at": timestamp(start + 1),
                    "finished_at": timestamp(start + 3),
                }
                stage["verifier"] = {"finished_at": timestamp(start + 4)}
                stages.append(stage)
                prefix = f"steps/{name}/agent"
                write(f"{prefix}/trajectory.json", atif)
                event = {
                    "payload": {
                        "type": "token_count",
                        "info": {"total_token_usage": native},
                    }
                }
                # Repeated cumulative snapshots are not additive usage.
                write(
                    f"{prefix}/sessions/session.jsonl",
                    "\n".join([json.dumps(event)] * 2),
                )
                write(
                    f"{prefix}/codex.txt", {"type": "turn.completed", "usage": native}
                )
                phases.append(
                    {
                        "phase": "index",
                        "step": name,
                        "arm": "baseline",
                        "return_code": 0,
                        "started_at": timestamp(start),
                        "finished_at": timestamp(start + 1),
                        "seconds": 1,
                    }
                )
                write(
                    f"environment/steps/{name}/index.stdout.log",
                    "No graph; baseline uses shell search.",
                )
            result["step_results"] = stages
            result["finished_at"] = timestamp(13)
            score["trials"][0].update(total_tokens=220, agent_seconds=4)
            write("result.json", result)
            write("environment/setup.jsonl", "\n".join(map(json.dumps, phases)))
            self.assertEqual(len(inspect(job)["trials"][0]["stages"]), 2)
            for invalid in (phases[:-1], [*phases[:2], phases[3], phases[2]]):
                write("environment/setup.jsonl", "\n".join(map(json.dumps, invalid)))
                with self.assertRaisesRegex(ValueError, "setup phases"):
                    inspect(job)
            phases[-1]["finished_at"] = timestamp(10)
            phases[-1]["seconds"] = 2
            write("environment/setup.jsonl", "\n".join(map(json.dumps, phases)))
            with self.assertRaisesRegex(ValueError, "overlaps agent"):
                inspect(job)
            phases[-1]["finished_at"] = timestamp(9)
            phases[-1]["seconds"] = 1
            write("environment/setup.jsonl", "\n".join(map(json.dumps, phases)))
            shutil.copytree(trial, job / "trial-2")
            score["trials"].append(deepcopy(score["trials"][0]))
            self.assertEqual(inspect(job)["completed_tasks"], 2)
            second_atif = job / "trial-2/steps/second/agent/trajectory.json"
            atif["final_metrics"]["total_completion_tokens"] += 1
            second_atif.write_text(json.dumps(atif))
            with self.assertRaisesRegex(ValueError, "accounting mismatch"):
                inspect(job)

    def test_index_readiness_requires_backend_evidence(self):
        for arm in ("codegraph", "graphify"):
            self.assertEqual(check_index(arm, "22 nodes, 41 edges")["nodes"], 22)
            for text in ("success", "0 nodes, 0 edges", "2 nodes, 0 edges"):
                with self.subTest(arm=arm, text=text), self.assertRaises(ValueError):
                    check_index(arm, text)
        summary = "22 nodes | 46 edges\n"
        capabilities = {
            "graph": {"status": "available"},
            "fts": {"status": "available"},
        }
        self.assertEqual(
            check_index("gitnexus", summary + json.dumps(capabilities))["edges"], 46
        )
        with self.assertRaisesRegex(ValueError, "FTS readiness"):
            check_index("gitnexus", summary + "FTS indexes missing")
        capabilities["fts"]["status"] = "unavailable"
        with self.assertRaisesRegex(ValueError, "FTS readiness"):
            check_index("gitnexus", summary + json.dumps(capabilities))
        cbm = {
            "status": "indexed",
            "nodes": 34,
            "edges": 105,
            "expected_nodes": 34,
            "expected_edges": 105,
            "not_indexed_files_count": 0,
            "skipped_count": 0,
            "parse_partial_count": 0,
        }
        self.assertEqual(
            check_index("codebase-memory-mcp", json.dumps(cbm))["nodes"], 34
        )
        cbm["parse_partial_count"] = 1
        with self.assertRaisesRegex(ValueError, "Incomplete codebase-memory-mcp"):
            check_index("codebase-memory-mcp", json.dumps(cbm))
        cbm["parse_partial_count"] = 0
        cbm["not_indexed_files_count"] = 1
        cbm["not_indexed_files"] = {
            "files": [{"path": "eshop/LICENSE", "reason": "skip-list"}],
            "count": 1,
            "truncated": False,
        }
        self.assertEqual(
            check_index("codebase-memory-mcp", json.dumps(cbm))["nodes"], 34
        )
        cbm["not_indexed_files"]["files"] = [
            {"path": "theme/logo.svg", "reason": "ignored-suffix"}
        ]
        self.assertEqual(
            check_index("codebase-memory-mcp", json.dumps(cbm))["nodes"], 34
        )
        for file in (
            {"path": "src/main.py", "reason": "skip-list"},
            {"path": "global.d.ts", "reason": "fast-pattern"},
            {"path": "LICENSE", "reason": "parse-error"},
        ):
            cbm["not_indexed_files"]["files"] = [file]
            with (
                self.subTest(file=file),
                self.assertRaisesRegex(ValueError, "Unapproved"),
            ):
                check_index("codebase-memory-mcp", json.dumps(cbm))
        cbm["not_indexed_files"]["files"] = [{"path": "LICENSE", "reason": "skip-list"}]
        for key, value in (("truncated", True), ("count", 2), ("files", [])):
            invalid = deepcopy(cbm)
            invalid["not_indexed_files"][key] = value
            with (
                self.subTest(key=key),
                self.assertRaisesRegex(ValueError, "exclusion evidence"),
            ):
                check_index("codebase-memory-mcp", json.dumps(invalid))


if __name__ == "__main__":
    unittest.main()
