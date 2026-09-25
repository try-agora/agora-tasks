"""Reconcile Codex overlay usage, index readiness, and step setup boundaries."""

import argparse
from collections import Counter
from datetime import datetime
import json
from pathlib import Path
import sys

from score_job import score_job
from check_job import check as check_job

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from overlays.readiness import check_index  # noqa: E402


def require(condition, message):
    if not condition:
        raise ValueError(message)


def events(path):
    # codex.txt interleaves diagnostic text with its JSON event stream.
    return [
        json.loads(line)
        for line in path.read_text().splitlines()
        if line.lstrip().startswith("{")
    ]


def instant(value):
    return datetime.fromisoformat(value)


def seconds(timing):
    return (
        instant(timing["finished_at"]) - instant(timing["started_at"])
    ).total_seconds()


def check_setup(trial, result):
    """Usable for credential-free Oracle runs as well as measured Codex runs."""
    stages = result.get("step_results") or []
    names = [stage["step_name"] for stage in stages]
    require(len(names) == len(set(names)), "Duplicate step results")
    phases = events(trial / "environment/setup.jsonl")
    expected = [("common", None), ("install", None)] + [
        ("index", name) for name in (names or [None])
    ]
    require(
        [(p["phase"], p.get("step")) for p in phases] == expected,
        "Missing, repeated, or reordered setup phases",
    )
    arm = phases[0]["arm"]
    previous = instant(result["environment_setup"]["started_at"])
    env_end = instant(result["environment_setup"]["finished_at"])
    readiness = {}
    for phase in phases:
        require(
            phase["arm"] == arm
            and phase.get("return_code") == 0
            and not phase.get("error"),
            "Overlay setup failed",
        )
        start, end = instant(phase["started_at"]), instant(phase["finished_at"])
        require(previous <= start <= end, "Setup phases overlap or have invalid timing")
        require(
            abs((end - start).total_seconds() - phase["seconds"]) < 1,
            "Wall and monotonic setup clocks disagree",
        )
        previous = end
        name = phase.get("step")
        if phase["phase"] != "index" or not stages:
            require(end <= env_end, "Initial setup extends beyond environment setup")
        if phase["phase"] == "index":
            logs = trial / "environment"
            if name is not None:
                require(name in names, "Unknown setup step")
                logs = logs / "steps" / name
                i = names.index(name)
                stage = stages[i]
                # Step preparation follows initial setup / the previous verifier.
                boundary = (
                    stages[i - 1]["verifier"]["finished_at"]
                    if i
                    else result["environment_setup"]["finished_at"]
                )
                require(
                    instant(boundary) <= start,
                    "Step index precedes workspace preparation boundary",
                )
            else:
                stage = result
            require(
                end <= instant(stage["agent_execution"]["started_at"]),
                "Index construction overlaps agent execution",
            )
            evidence = check_index(arm, (logs / "index.stdout.log").read_text())
            recorded = phase.get("index_readiness")
            require(
                recorded is None or recorded == evidence,
                "Index readiness evidence disagrees",
            )
            readiness[name or "single"] = evidence
    return {"arm": arm, "phases": phases, "index_readiness": readiness}


def check_agent(directory, result, arm):
    atif = json.loads((directory / "agent/trajectory.json").read_text())
    sessions = list((directory / "agent/sessions").rglob("*.jsonl"))
    require(len(sessions) == 1, "Expected one fresh native Codex session per stage")
    usages = [
        e["payload"]["info"]["total_token_usage"]
        for e in events(sessions[0])
        if e.get("payload", {}).get("type") == "token_count"
        and e["payload"].get("info")
    ]
    require(bool(usages), "Missing native cumulative token usage")
    native = usages[-1]  # Cumulative snapshots must never be summed.
    stream = events(directory / "agent/codex.txt")
    turns = [e["usage"] for e in stream if e.get("type") == "turn.completed"]
    require(len(turns) == 1, "Expected one completed Codex turn per stage")
    for native_key, harbor_key, atif_key in (
        ("input_tokens", "n_input_tokens", "total_prompt_tokens"),
        ("cached_input_tokens", "n_cache_tokens", "total_cached_tokens"),
        ("output_tokens", "n_output_tokens", "total_completion_tokens"),
    ):
        require(
            native[native_key]
            == result["agent_result"][harbor_key]
            == atif["final_metrics"][atif_key]
            == turns[0][native_key],
            f"Token accounting mismatch: {native_key}",
        )
    require(
        native["total_tokens"] == native["input_tokens"] + native["output_tokens"],
        "Native total includes unexpected token dimensions",
    )
    calls = [
        e["item"]
        for e in stream
        if e.get("type") == "item.completed"
        and e.get("item", {}).get("type") == "mcp_tool_call"
    ]
    require(all(c["server"] == arm for c in calls), "Unexpected MCP server")
    if arm == "baseline":
        require(not calls, "Baseline unexpectedly used MCP")
    else:
        require(
            any(c["status"] == "completed" and not c.get("error") for c in calls),
            "No completed MCP call",
        )
    return {
        "step": result.get("step_name", "single"),
        "input_tokens": native["input_tokens"],
        "cached_input_tokens": native["cached_input_tokens"],
        "output_tokens": native["output_tokens"],
        "total_tokens": native["total_tokens"],
        "agent_seconds": seconds(result["agent_execution"]),
        "mcp_calls": dict(Counter(c["tool"] for c in calls)),
        "mcp_transport_errors": sum(
            c["status"] != "completed" or bool(c.get("error")) for c in calls
        ),
    }


def inspect(directory):
    score = score_job(directory)
    require(not score["errors"], f"Invalid scoring evidence: {score['errors']}")
    paths = sorted(directory.glob("*/result.json"))
    require(len(paths) == len(score["trials"]), "Trial evidence count disagrees")
    reports = []
    for path, task_score in zip(paths, score["trials"], strict=True):
        trial = path.parent
        result = json.loads(path.read_text())
        setup = check_setup(trial, result)
        stages = [
            check_agent(trial / "steps" / stage["step_name"], stage, setup["arm"])
            for stage in result.get("step_results") or []
        ] or [check_agent(trial, result, setup["arm"])]
        total = sum(stage["total_tokens"] for stage in stages)
        require(
            total == task_score["total_tokens"], "Scorer/native stage totals disagree"
        )
        reports.append(
            {
                "arm": setup["arm"],
                "trial": trial.name,
                "completed": task_score["completed"],
                "reward": task_score["reward"],
                "total_tokens": total,
                "agent_seconds": task_score["agent_seconds"],
                "stages": stages,
                "setup_seconds": [
                    {
                        "phase": p["phase"],
                        "step": p.get("step"),
                        "seconds": p["seconds"],
                    }
                    for p in setup["phases"]
                ],
                "index_readiness": setup["index_readiness"],
                "environment_seconds": seconds(result["environment_setup"]),
                "trial_seconds": seconds(result),
            }
        )
    return {
        "usage_reconciled": True,
        "mean_reward": score["mean_reward"] if "mean_reward" in score else None,
        "completed_tasks": sum(r["completed"] for r in reports),
        "trials": reports,
        "note": "MCP completion is not semantic success; inspect returned content manually.",
    }


def inspect_oracle(directory, count=None):
    """Check reference solutions and setup without pretending Oracle has token usage."""
    check_job(directory, expected=1, count=count)
    reports = []
    names = set()
    for path in sorted(directory.glob("*/result.json")):
        result = json.loads(path.read_text())
        name = result["task_name"].removeprefix("agora/")
        require(name not in names, "Duplicate task in reference coverage")
        names.add(name)
        setup = check_setup(path.parent, result)
        reports.append(
            {
                "task": name,
                "arm": setup["arm"],
                "index_readiness": setup["index_readiness"],
            }
        )
    expected = {
        p.parent.name
        for p in (Path(__file__).resolve().parents[1] / "evals").glob("*/task.toml")
    }
    if count == len(expected):
        require(names == expected, "Reference coverage differs from dataset")
    return {
        "tasks_checked": len(names),
        "stages_checked": sum(len(r["index_readiness"]) for r in reports),
        "trials": reports,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument(
        "--oracle",
        action="store_true",
        help="Check reference-solution setup, not model usage",
    )
    parser.add_argument(
        "--count",
        type=int,
        help="Expected unique Oracle tasks (default: complete dataset)",
    )
    args = parser.parse_args()
    report = (
        inspect_oracle(args.directory, args.count)
        if args.oracle
        else inspect(args.directory)
    )
    print(json.dumps(report, indent=2))
