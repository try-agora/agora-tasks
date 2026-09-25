"""A tool-only setup layer over Harbor's unchanged task Docker environment."""

from datetime import datetime, timezone
import json
from pathlib import Path
import time
import tomllib
from weakref import WeakValueDictionary

from harbor.environments.docker.docker import DockerEnvironment
from overlays.readiness import check_index

ARMS = {"baseline", "codegraph", "gitnexus", "graphify", "codebase-memory-mcp"}
# Harbor hooks carry trial identity, not the live environment. Keep only weak,
# trial-scoped references; no sandbox data or state is shared between trials.
_environments = WeakValueDictionary()
_hooked_jobs = set()


class OverlayEnvironment(DockerEnvironment):
    def __init__(self, *args, arm="baseline", **kwargs):
        if arm not in ARMS:
            raise ValueError(f"Unknown overlay: {arm}")
        super().__init__(*args, **kwargs)
        self.arm = arm
        task = tomllib.loads((self.environment_dir.parent / "task.toml").read_text())
        self.step_names = [step["name"] for step in task.get("steps", [])]
        self.indexed_steps = []
        key = self.trial_paths.trial_dir.resolve()
        if self.step_names and key.parent not in _hooked_jobs:
            raise ValueError(
                "Multi-step overlays require --plugin overlays.environment:StepIndexPlugin"
            )
        _environments[key] = self

    async def _phase(self, phase, user, step=None):
        logs = self.trial_paths.trial_dir / "environment"
        output_dir = logs / "steps" / step if step else logs
        output_dir.mkdir(parents=True, exist_ok=True)
        started = datetime.now(timezone.utc).isoformat()
        clock = time.monotonic()
        record = {"arm": self.arm, "phase": phase, "started_at": started}
        if step:
            record["step"] = step
        try:
            result = await self.exec(
                f"bash /opt/benchmark-overlay/setup.sh {phase} {self.arm}",
                cwd="/app",
                user=user,
                timeout_sec=900,
            )
            (output_dir / f"{phase}.stdout.log").write_text(result.stdout or "")
            (output_dir / f"{phase}.stderr.log").write_text(result.stderr or "")
            record["return_code"] = result.return_code
            if result.return_code != 0:
                raise RuntimeError(f"Overlay {self.arm} {phase} failed; see {logs}")
            if phase == "index":
                record["index_readiness"] = check_index(self.arm, result.stdout or "")
        except BaseException as exc:
            record["error"] = type(exc).__name__
            raise
        finally:
            record["finished_at"] = datetime.now(timezone.utc).isoformat()
            record["seconds"] = time.monotonic() - clock
            with (logs / "setup.jsonl").open("a") as output:
                output.write(json.dumps(record) + "\n")

    async def start(self, force_build):
        await super().start(force_build)
        result = await self.exec("mkdir -p /opt/benchmark-overlay", user="root")
        if result.return_code:
            raise RuntimeError("Cannot create overlay setup directory")
        await self.upload_file(
            Path(__file__).with_name("setup.sh"), "/opt/benchmark-overlay/setup.sh"
        )
        await self.upload_dir(
            Path(__file__).with_name("locks"), "/opt/benchmark-overlay/locks"
        )
        await self._phase("common", "root")
        await self._phase("install", "root")
        if not self.step_names:
            await self._phase("index", "agent")

    async def prepare_step(self, name):
        expected = self.step_names[
            len(self.indexed_steps) : len(self.indexed_steps) + 1
        ]
        if expected != [name]:
            raise ValueError(f"Unexpected or repeated index step: {name}")
        await self._phase("index", "agent", step=name)
        self.indexed_steps.append(name)


class StepIndexPlugin:
    """Native Harbor pre-agent hook; never wraps or changes agent behavior."""

    async def on_job_start(self, job):
        self.job_dir = job.job_dir.resolve()
        _hooked_jobs.add(self.job_dir)
        job.on_agent_started(self.before_agent)

    async def before_agent(self, event):
        steps = event.result.step_results or []
        if not steps:
            return
        if event.config.agent.resume_trajectory:
            raise ValueError("Relay measurements require fresh conversations")
        key = (event.config.trials_dir / event.trial_name).resolve()
        environment = _environments.get(key)
        if environment is None:
            raise RuntimeError("No live overlay environment for this trial")
        await environment.prepare_step(steps[-1].step_name)

    async def on_job_end(self, job_result):
        _hooked_jobs.discard(self.job_dir)
