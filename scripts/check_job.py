#!/usr/bin/env python3
"""Fail CI on missing trials, infrastructure errors, or unexpected Harbor rewards."""

import argparse
from datetime import datetime
import json
from pathlib import Path
import tomllib


def check(directory, expected, count=None):
    contracts = {}
    for path in (Path(__file__).resolve().parents[1] / "evals").glob("*/task.toml"):
        config = tomllib.loads(path.read_text())
        contracts[config["task"]["name"]] = [s["name"] for s in config.get("steps", [])]
    count = len(contracts) if count is None else count
    if count < 1 or expected not in (0, 1):
        raise ValueError("positive task count and binary expected reward required")

    def finished(record):
        try:
            return datetime.fromisoformat(
                record["started_at"]
            ) <= datetime.fromisoformat(record["finished_at"])
        except (KeyError, TypeError, ValueError):
            return False

    result = json.loads((directory / "result.json").read_text())
    if not finished(result):
        raise AssertionError("job is unfinished or has invalid timestamps")
    stats = result["stats"]
    if result["n_total_trials"] != count or stats["n_completed_trials"] != count:
        raise AssertionError("missing or incomplete trials")
    if stats["n_errored_trials"]:
        raise AssertionError(f"infrastructure errors: {stats['n_errored_trials']}")
    trials = list(directory.glob("*/result.json"))
    if len(trials) != count:
        raise AssertionError(f"expected {count} trial results, found {len(trials)}")
    seen = set()
    for path in trials:
        trial = json.loads(path.read_text())
        if not finished(trial):
            raise AssertionError(f"{path}: unfinished trial or invalid timestamps")
        if trial.get("exception_info"):
            raise AssertionError(f"{path}: {trial['exception_info']}")
        rewards = (trial.get("verifier_result") or {}).get("rewards") or {}
        if (
            type(rewards.get("reward")) not in (int, float)
            or rewards.get("reward") != expected
        ):
            raise AssertionError(f"{path}: expected {expected}, got {rewards}")
        task_name = trial["task_name"]
        if task_name not in contracts or task_name in seen:
            raise AssertionError(f"{path}: unknown or duplicate task: {task_name}")
        seen.add(task_name)
        names = contracts[task_name]
        observed = trial.get("step_results") or []
        if [step["step_name"] for step in observed] != names:
            raise AssertionError(f"{path}: missing or reordered steps")
        for step in observed:
            if (
                step.get("exception_info")
                or not finished(step.get("verifier") or {})
                or (step.get("verifier_result") or {}).get("rewards", {}).get("reward")
                != expected
            ):
                raise AssertionError(f"{path}: failed step {step['step_name']}")
    if count == len(contracts) and seen != set(contracts):
        raise AssertionError("reference coverage differs from the dataset")
    print(
        f"PASS {directory.name}: {count} trials, expected reward {expected}, no infrastructure errors"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--expected", type=float, required=True)
    parser.add_argument(
        "--count",
        type=int,
        help="Expected unique tasks (default: the complete current dataset)",
    )
    args = parser.parse_args()
    check(args.directory, args.expected, args.count)
