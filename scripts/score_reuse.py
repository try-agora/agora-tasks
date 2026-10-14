#!/usr/bin/env python3
"""Score paired capture-to-reuse jobs without changing their raw results."""

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

from check_reuse_job import (
    audit_trial,
    expand_jobs,
    load_json,
    load_jsonl,
    native_events,
    require,
)
from score_job import score_job


def mean(values):
    return sum(values) / len(values) if values else None


def job_arm(trial):
    if (trial / "environment/product").is_dir():
        return "agora"
    setup = trial / "environment/setup.jsonl"
    if not setup.is_file():
        return "baseline"
    phases = load_jsonl(setup)
    arms = {phase.get("arm") for phase in phases}
    require(len(arms) == 1 and None not in arms, f"{trial}: invalid arm evidence")
    return arms.pop()


def product_usage(path):
    value = load_json(path)
    records = value.get("jobs") if isinstance(value, dict) and "jobs" in value else [value]
    require(isinstance(records, list) and records, "Invalid product usage")
    total = 0
    sources = Counter()
    for record in records:
        require(isinstance(record, dict), "Invalid product usage record")
        source = record.get("source")
        require(source in {"agent", "fixture"}, "Invalid product usage source")
        inputs, outputs = record.get("input_tokens"), record.get("output_tokens")
        require(
            type(inputs) is int and inputs >= 0 and type(outputs) is int and outputs >= 0,
            "Invalid product token usage",
        )
        sources[source] += 1
        if source == "agent":
            total += inputs + outputs
    return total, sources


def explicit_file_reads(value):
    found = set()

    def visit(item):
        if isinstance(item, dict):
            for key, child in item.items():
                if key in {"file_reads", "files_read"} and isinstance(child, list):
                    found.update(path for path in child if isinstance(path, str))
                visit(child)
        elif isinstance(item, list):
            for child in item:
                visit(child)

    visit(value)
    return found


def traversal(trial, stages):
    calls = Counter()
    shell = 0
    files = set()
    for stage in stages:
        name = stage.get("step_name")
        agent = trial / "steps" / name / "agent" if name else trial / "agent"
        atif = load_json(agent / "trajectory.json")
        files.update(explicit_file_reads(atif))
        for event in native_events(agent / "codex.txt"):
            item = event.get("item") or {}
            if event.get("type") != "item.completed":
                continue
            if item.get("type") == "mcp_tool_call":
                calls[item.get("tool", "unknown")] += 1
            elif item.get("type") == "command_execution":
                shell += 1
    return {"mcp_calls": calls, "shell_execs": shell, "files_read": files}


def phase_seconds(trial):
    totals = Counter()
    path = trial / "environment/setup.jsonl"
    if not path.is_file():
        return totals
    for row in load_jsonl(path):
        value = row.get("seconds")
        require(type(value) in (int, float) and value >= 0, "Invalid setup phase timing")
        totals[row.get("phase")] += value
    return totals


def trial_record(trial, task_score, arm, errors):
    result = load_json(trial / "result.json")
    stages = result.get("step_results") or [result]
    task = result.get("task_name", "").removeprefix("agora/")
    valid = not task_score["errors"]
    product_tokens = 0
    sources = Counter()
    reuse = "absent"
    accept = None
    pins = None
    if arm == "agora":
        try:
            verdict = audit_trial(trial)
            reuse = verdict["reuse"]
            accept = verdict["accept"]
            pins = verdict["pins"]
        except ValueError as error:
            errors.append(f"{trial}: {error}")
            valid = False
        try:
            product_tokens, sources = product_usage(
                trial / "environment/product/product-usage.json"
            )
        except ValueError as error:
            errors.append(f"{trial}: {error}")
            valid = False
    phases = phase_seconds(trial)
    observed = traversal(trial, stages)
    return {
        "job": trial.parent.name,
        "trial": trial.name,
        "task": task,
        "arm": arm,
        "valid": valid,
        "reuse": reuse,
        "accept": accept,
        "pins": pins,
        "agent_tokens": task_score["total_tokens"],
        "step_2_tokens": task_score["stages"][-1]["total_tokens"],
        "product_tokens": product_tokens if valid else None,
        "product_source": sources,
        "agent_seconds": task_score["agent_seconds"],
        "capture_seconds": phases["capture"],
        "accept_seconds": phases["accept"],
        **observed,
    }


def validate_protocol(jobs, count):
    require(count is not None, "Protocol mode requires a declared count")
    require(len(jobs) == count, f"Protocol declared count {count}, found {len(jobs)} jobs")
    require(count == 12, "Protocol requires 12 jobs")
    resolved = [job.resolve() for job in jobs]
    require(len(set(resolved)) == len(resolved), "Protocol job names must be unique")
    cells = Counter()
    names = []
    for job in jobs:
        summary, paths = load_json(job / "result.json"), sorted(job.glob("*/result.json"))
        names.append(summary.get("job_name", job.name))
        require(len(paths) == summary.get("n_total_trials") == 1, "Protocol requires one trial per job")
        require((summary.get("stats") or {}).get("n_retries", 0) == 0, "Protocol refuses retried jobs")
        trial = paths[0].parent
        task = load_json(paths[0]).get("task_name", "").removeprefix("agora/")
        cells[(task, job_arm(trial))] += 1
    require(len(set(names)) == len(names), "Protocol job names must be unique")
    require(
        {task for task, _ in cells}
        == {"cross-session-framework-reuse", "cross-session-deduplication-reuse"}
        and {arm for _, arm in cells} == {"baseline", "agora"}
        and set(cells.values()) == {3},
        "Protocol requires two tasks, two arms, and three attempts per cell",
    )


def cell_report(task, arm, rows, completion_valid):
    valid = [row for row in rows if row["valid"]]
    reuse = Counter(
        row["reuse"] if row["reuse"] in {"verified", "pending-review"} else "absent"
        for row in rows
    )
    mcp = Counter()
    sources = Counter()
    for row in rows:
        mcp.update(row["mcp_calls"])
        sources.update(row["product_source"])
    completion = [row["completion"] for row in rows if row["completion"] is not None]
    acceptance = {row["accept"] for row in rows if row["accept"] is not None}
    return {
        "task": task,
        "arm": arm,
        "n": len(rows),
        "accept": acceptance.pop() if len(acceptance) == 1 else None,
        "reuse": {
            "verified": reuse["verified"],
            "pending_review": reuse["pending-review"],
            "absent": reuse["absent"],
            "denominator": len(rows),
        },
        "traversal": {
            "mcp_calls": dict(sorted(mcp.items())),
            "shell_execs": sum(row["shell_execs"] for row in rows),
            "files_read": sorted(set().union(*(row["files_read"] for row in rows))),
            "denominator": len(rows),
        },
        "tokens": {
            "pair_mean": mean([row["agent_tokens"] for row in valid]),
            "step_2_mean": mean([row["step_2_tokens"] for row in valid]),
            "product_mean": mean([row["product_tokens"] for row in valid]),
            "product_source": dict(sorted(sources.items())),
            "denominator": len(valid),
        },
        "time": {
            "agent_mean": mean([row["agent_seconds"] for row in valid]),
            "capture_mean": mean([row["capture_seconds"] for row in valid]),
            "accept_mean": mean([row["accept_seconds"] for row in valid]),
            "human_wait_mean": mean(
                [row["accept_seconds"] if row["accept"] == "person" else 0 for row in valid]
            ),
            "cost_mean": mean(
                [
                    row["agent_seconds"]
                    + row["capture_seconds"]
                    + (0 if row["accept"] == "person" else row["accept_seconds"])
                    for row in valid
                ]
            ),
            "denominator": len(valid),
        },
        "completion_composite": {
            "mean": mean(completion) if completion_valid and len(completion) == len(rows) else None,
            "denominator": len(completion) if completion_valid else 0,
            "version": "completion-efficiency-v1",
        },
    }


def score_campaign(paths, *, protocol=False, count=None):
    jobs = expand_jobs(paths)
    if protocol:
        validate_protocol(jobs, count)
    errors = []
    records = []
    for job in jobs:
        summary = load_json(job / "result.json")
        if (summary.get("stats") or {}).get("n_retries", 0):
            errors.append(f"{job}: retried jobs are refused")
        scored = score_job(job)
        errors.extend(f"{job}: {error}" for error in scored["errors"])
        paths_for_trials = sorted(job.glob("*/result.json"))
        require(len(paths_for_trials) == len(scored["trials"]), f"{job}: scoring evidence count differs")
        for path, task_score in zip(paths_for_trials, scored["trials"], strict=True):
            arm = job_arm(path.parent)
            record = trial_record(path.parent, task_score, arm, errors)
            record["completion"] = task_score["reward"]
            records.append(record)

    stable_pins = {
        json.dumps(
            {key: value for key, value in row["pins"].items() if key != "task_checksum"},
            sort_keys=True,
        )
        for row in records
        if row["pins"] is not None
    }
    if len(stable_pins) > 1:
        errors.append("Campaign has mixed pins across product jobs")
        for row in records:
            if row["pins"] is not None:
                row["valid"] = False
                row["product_tokens"] = None

    grouped = {}
    for row in records:
        grouped.setdefault((row["task"], row["arm"]), []).append(row)
    cells = [
        cell_report(task, arm, rows, all(row["valid"] for row in rows))
        for (task, arm), rows in sorted(grouped.items())
    ]
    by_key = {(cell["task"], cell["arm"]): cell for cell in cells}
    arm_rows = {}
    for row in records:
        arm_rows.setdefault(row["arm"], []).append(row)
    arms = {}
    for arm, rows in sorted(arm_rows.items()):
        complete = all(row["valid"] and row["completion"] is not None for row in rows)
        arms[arm] = {
            "n": len(rows),
            "completion_composite": {
                "mean": mean([row["completion"] for row in rows]) if complete else None,
                "denominator": len(rows) if complete else 0,
                "version": "completion-efficiency-v1",
            },
        }
    product_tasks = {task for task, arm in by_key if arm == "agora"}
    paired = []
    complete_pairs = bool(product_tasks)
    for task in sorted(product_tasks):
        baseline, product = by_key.get((task, "baseline")), by_key.get((task, "agora"))
        if not baseline:
            complete_pairs = False
            continue
        baseline_tokens = baseline["tokens"]["pair_mean"]
        product_tokens = product["tokens"]["pair_mean"]
        external = product["tokens"]["product_mean"]
        if None in (baseline_tokens, product_tokens, external):
            complete_pairs = False
            continue
        paired.append(
            {
                "task": task,
                "mean": baseline_tokens - product_tokens - external,
                "baseline_n": baseline["tokens"]["denominator"],
                "agora_n": product["tokens"]["denominator"],
            }
        )
    return {
        "scoring_version": "capture-reuse-v1",
        "protocol": protocol,
        "jobs": len(jobs),
        "arms": arms,
        "cells": cells,
        "tokens_saved": paired if complete_pairs else None,
        "errors": errors,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directories", nargs="+", type=Path)
    parser.add_argument("--protocol", action="store_true")
    parser.add_argument("--count", type=int)
    args = parser.parse_args(argv)
    report = score_campaign(args.directories, protocol=args.protocol, count=args.count)
    print(json.dumps(report, indent=2, allow_nan=False))
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
