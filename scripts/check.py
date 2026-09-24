#!/usr/bin/env python3
"""Check task structure and score baseline, oracle, and plausible wrong solutions."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib

from harbor.models.task.config import TaskConfig

ROOT = Path(__file__).resolve().parents[1]


def score(task, step, variant):
    with tempfile.TemporaryDirectory(prefix="agora-task-check-") as directory:
        workspace = Path(directory) / "workspace"
        logs = Path(directory) / "logs"
        shutil.copytree(task / "environment/workspace", workspace)
        if variant != "baseline":
            shutil.copytree(
                step / "solution/src", workspace / "src", dirs_exist_ok=True
            )
        if variant == "mutation":
            mutation = json.loads((step / "tests/mutation.json").read_text())
            for name, body in mutation["files"].items():
                target = workspace / name
                if not target.resolve().is_relative_to(workspace.resolve()):
                    raise ValueError(f"mutation escapes workspace: {name}")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(body)
        result = subprocess.run(
            [sys.executable, "-I", "-B", str(step / "tests/test_behavior.py")],
            cwd=workspace,
            env={
                **os.environ,
                "TASK_WORKSPACE": str(workspace),
                "VERIFIER_LOGS": str(logs),
            },
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode or not (logs / "reward.txt").exists():
            raise RuntimeError(
                f"verifier crashed: {step}\n{result.stdout}\n{result.stderr}"
            )
        reward = float((logs / "reward.txt").read_text())
        expected = 1 if variant == "oracle" else 0
        if reward != expected:
            raise AssertionError(
                f"{step.name}/{variant}: expected {expected}, got {reward}\n{result.stderr}"
            )
        evidence = json.loads((logs / "checks.json").read_text())
        assert evidence["tests_run"] > 0
        return evidence["tests_run"]


def main():
    tasks = sorted(path.parent for path in (ROOT / "evals").glob("*/task.toml"))
    assert len(tasks) >= 10, "the dataset must contain at least ten tasks"
    total = 0
    for task in tasks:
        raw = (task / "task.toml").read_text()
        TaskConfig.model_validate_toml(raw)
        config = tomllib.loads(raw)
        assert config["task"]["name"] == "agora/" + task.name
        steps = config.get("steps", [])
        names = [step["name"] for step in steps]
        assert len(names) == len(set(names))
        assert all("/" not in name and name not in (".", "..") for name in names)
        if steps:
            assert set(names) == {path.name for path in (task / "steps").iterdir()}
            assert config["multi_step_reward_strategy"] == "mean"
        paths = [task / "steps" / name for name in names] if steps else [task]
        assert (task / "README.md").is_file()
        assert (task / "environment/Dockerfile").is_file()
        assert not list((task / "environment").rglob("*.whl"))
        for step in paths:
            for required in (
                "instruction.md",
                "solution/solve.sh",
                "tests/test.sh",
                "tests/test_behavior.py",
            ):
                assert (step / required).is_file(), (step, required)
            for script in (step / "solution/solve.sh", step / "tests/test.sh"):
                subprocess.run(["bash", "-n", str(script)], check=True)
            for variant in ("baseline", "oracle", "mutation"):
                count = score(task, step, variant)
                total += 1
                print(
                    f"PASS {task.name}/{step.name if steps else 'single'} {variant}: {count} behavior checks",
                    flush=True,
                )
    print(f"Validated {len(tasks)} tasks; {total} verifier scenarios.")


if __name__ == "__main__":
    main()
