#!/usr/bin/env python3
"""Read a saved Harbor job and print a correctness-gated efficiency scorecard."""

import argparse
from datetime import datetime
import json
import math
from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def positive(value):
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ValueError("scoring scales must be finite and positive")
    return value


def score_stage(stage, token_scale, seconds_scale):
    rewards = (stage.get("verifier_result") or {}).get("rewards") or {}
    correctness = rewards.get("reward")
    errors = []
    if stage.get("exception_info"):
        errors.append("infrastructure exception")
    if type(correctness) not in (int, float) or correctness not in (0, 1):
        errors.append("missing or non-binary correctness reward")
        correctness = None
    finished = not errors
    usage = stage.get("agent_result") or {}
    input_tokens = usage.get("n_input_tokens")
    output_tokens = usage.get("n_output_tokens")
    cache_tokens = usage.get("n_cache_tokens")
    tokens = None
    if all(type(n) is int and n >= 0 for n in (input_tokens, output_tokens)):
        tokens = input_tokens + output_tokens
    else:
        errors.append("missing or invalid token usage")
        input_tokens = (
            input_tokens if type(input_tokens) is int and input_tokens >= 0 else None
        )
        output_tokens = (
            output_tokens if type(output_tokens) is int and output_tokens >= 0 else None
        )
    if cache_tokens is not None and (
        type(cache_tokens) is not int
        or cache_tokens < 0
        or type(input_tokens) is not int
        or cache_tokens > input_tokens
    ):
        errors.append("invalid cached-input count")
        cache_tokens = None
    seconds = None
    timing = stage.get("agent_execution") or {}
    try:
        start = datetime.fromisoformat(timing["started_at"])
        end = datetime.fromisoformat(timing["finished_at"])
        seconds = (end - start).total_seconds()
        if not math.isfinite(seconds) or seconds < 0:
            raise ValueError("invalid duration")
    except (KeyError, TypeError, ValueError):
        errors.append("missing or invalid agent timing")
        seconds = None
    reward = None
    if not errors:
        reward = correctness * (
            0.8 + 0.1 / (1 + tokens / token_scale) + 0.1 / (1 + seconds / seconds_scale)
        )
    return {
        "step": stage.get("step_name", "single"),
        "finished": finished,
        "correctness": correctness,
        "input_tokens": input_tokens,
        "cached_input_tokens": cache_tokens,
        "output_tokens": output_tokens,
        "total_tokens": tokens,
        "agent_seconds": seconds,
        "reward": reward,
        "errors": errors,
    }


def score_trial(trial, expected_steps, token_scale=100_000, seconds_scale=120):
    token_scale, seconds_scale = positive(token_scale), positive(seconds_scale)
    observed = trial.get("step_results") or []
    errors = []
    if [s.get("step_name") for s in observed] != expected_steps:
        errors.append("missing, unexpected, or reordered steps")
    if trial.get("exception_info"):
        errors.append("trial infrastructure exception")
    if not trial.get("finished_at"):
        errors.append("trial has not finished")
    stages = [score_stage(s, token_scale, seconds_scale) for s in (observed or [trial])]
    finished = not errors and all(s["finished"] for s in stages)
    for stage in stages:
        errors.extend(f"{stage['step']}: {error}" for error in stage["errors"])
    completed = all(s["correctness"] == 1 for s in stages) if finished else None
    return {
        "task": trial.get("task_name"),
        "trial": trial.get("trial_name"),
        "finished": finished,
        "completed": completed,
        # A partially solved multi-step task is not a completed task.
        "reward": (sum(s["reward"] for s in stages) / len(stages) if completed else 0)
        if not errors
        else None,
        "total_tokens": sum(s["total_tokens"] for s in stages)
        if all(s["total_tokens"] is not None for s in stages)
        else None,
        "agent_seconds": sum(s["agent_seconds"] for s in stages)
        if all(s["agent_seconds"] is not None for s in stages)
        else None,
        "stages": stages,
        "errors": errors,
    }


def score_job(directory, token_scale=100_000, seconds_scale=120):
    token_scale, seconds_scale = positive(token_scale), positive(seconds_scale)
    job = json.loads((directory / "result.json").read_text())
    contracts = {}
    for path in (ROOT / "evals").glob("*/task.toml"):
        config = tomllib.loads(path.read_text())
        contracts[config["task"]["name"]] = [s["name"] for s in config.get("steps", [])]
    trials = []
    errors = []
    for path in sorted(directory.glob("*/result.json")):
        trial = json.loads(path.read_text())
        name = trial.get("task_name")
        if name not in contracts:
            errors.append(f"unknown task contract: {name}")
            continue
        trials.append(score_trial(trial, contracts[name], token_scale, seconds_scale))
    total = job["n_total_trials"]
    if not job.get("finished_at") or not trials or len(trials) != total:
        errors.append("job is unfinished or trial results are missing")
    stats = job.get("stats") or {}
    if stats.get("n_completed_trials") != total or stats.get("n_errored_trials", 0):
        errors.append("job has incomplete or errored trials")
    if stats.get("n_retries", 0):
        errors.append("retried jobs require all-attempt usage accounting")
    if any(t["errors"] for t in trials):
        errors.append("one or more trials have missing/invalid scoring evidence")
    return {
        "scoring_version": "completion-efficiency-v1",
        "token_scale_per_stage": token_scale,
        "seconds_scale_per_stage": seconds_scale,
        "formula": "completed * mean(0.8 + 0.1/(1+tokens/token_scale) + 0.1/(1+seconds/seconds_scale))",
        "token_scope": "input (including cache) + output reported by Harbor; unreported external tool usage excluded",
        "latency_scope": "agent execution only; excludes environment/agent installation and verifier time",
        "finished_tasks": sum(t["finished"] for t in trials),
        "completed_tasks": sum(t["completed"] is True for t in trials),
        "expected_trials": total,
        "mean_reward": sum(t["reward"] for t in trials) / len(trials)
        if not errors
        else None,
        "trials": trials,
        "errors": errors,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--token-scale", type=positive, default=100_000)
    parser.add_argument("--seconds-scale", type=positive, default=120)
    args = parser.parse_args()
    report = score_job(args.directory, args.token_scale, args.seconds_scale)
    print(json.dumps(report, indent=2, allow_nan=False))
    raise SystemExit(1 if report["errors"] else 0)
