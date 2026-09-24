#!/usr/bin/env python3
"""Fail CI on missing trials, infrastructure errors, or unexpected Harbor rewards."""

import argparse
import json
from pathlib import Path
import tomllib


def check(directory, expected, count):
    result = json.loads((directory / "result.json").read_text())
    stats = result["stats"]
    if result["n_total_trials"] != count or stats["n_completed_trials"] != count:
        raise AssertionError("missing or incomplete trials")
    if stats["n_errored_trials"]:
        raise AssertionError(f"infrastructure errors: {stats['n_errored_trials']}")
    trials = list(directory.glob("*/result.json"))
    if len(trials) != count:
        raise AssertionError(f"expected {count} trial results, found {len(trials)}")
    for path in trials:
        trial = json.loads(path.read_text())
        if trial.get("exception_info"):
            raise AssertionError(f"{path}: {trial['exception_info']}")
        rewards = trial.get("verifier_result", {}).get("rewards", {})
        if rewards.get("reward") != expected:
            raise AssertionError(f"{path}: expected {expected}, got {rewards}")
        task_name = trial["task_name"].removeprefix("agora/")
        task = Path(__file__).resolve().parents[1] / "evals" / task_name
        config = tomllib.loads((task / "task.toml").read_text())
        names = [step["name"] for step in config.get("steps", [])]
        observed = trial.get("step_results") or []
        if [step["step_name"] for step in observed] != names:
            raise AssertionError(f"{path}: missing or reordered steps")
        for step in observed:
            if (
                step.get("exception_info")
                or (step.get("verifier_result") or {}).get("rewards", {}).get("reward")
                != expected
            ):
                raise AssertionError(f"{path}: failed step {step['step_name']}")
    print(
        f"PASS {directory.name}: {count} trials, expected reward {expected}, no infrastructure errors"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--expected", type=float, required=True)
    parser.add_argument("--count", type=int, default=10)
    args = parser.parse_args()
    check(args.directory, args.expected, args.count)
