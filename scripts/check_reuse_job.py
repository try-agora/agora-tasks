#!/usr/bin/env python3
"""Validate capture-to-reuse evidence without running an agent or container."""

import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_PINS = {
    "server_sha",
    "server_drop_sha256",
    "agent_sha",
    "agent_drop_sha256",
    "hook_sha256",
    "hook_version",
    "executor",
    "agora_tasks_sha",
    "task_checksum",
    "harbor_version",
    "codex_version",
    "model",
    "accept",
}
PIN_VALUES = {
    "executor": {"fixture-v1", "ported"},
    "accept": {"person", "scripted-console-v1"},
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_json(path):
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Missing or invalid evidence: {path}") from error
    return value


def load_jsonl(path):
    try:
        return [json.loads(line) for line in path.read_text().splitlines() if line]
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Missing or invalid evidence: {path}") from error


def expand_jobs(paths):
    jobs = []
    for path in map(Path, paths):
        if (path / "result.json").is_file():
            jobs.append(path)
        else:
            jobs.extend(sorted(p.parent for p in path.glob("*/result.json")))
    require(bool(jobs), "No job evidence found")
    return jobs


def trials(job):
    summary = load_json(job / "result.json")
    paths = sorted(job.glob("*/result.json"))
    require(
        bool(paths) and len(paths) == summary.get("n_total_trials"),
        f"{job}: trial count disagrees with job summary",
    )
    return summary, paths


def parse_time(value, message):
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError) as error:
        raise ValueError(message) from error


def native_events(path):
    return [
        json.loads(line)
        for line in path.read_text().splitlines()
        if line.lstrip().startswith("{")
    ]


def task_steps(result):
    task = result.get("task_name", "").removeprefix("agora/")
    stages = result.get("step_results") or []
    names = [stage.get("step_name") for stage in stages]
    require(task and len(names) == 2 and len(set(names)) == 2, "Expected two distinct task steps")
    task_root = ROOT / "evals" / task / "steps"
    require(all((task_root / name / "instruction.md").is_file() for name in names), "Unknown task steps")
    return task, stages, names


def principal_id(row):
    principal = row.get("principal")
    return principal.get("id") if isinstance(principal, dict) else principal


def check_principals(product, stages, names):
    value = load_json(product / "principals.json")
    declared = value.get("steps") if isinstance(value.get("steps"), dict) else value
    agents = [declared.get(name) for name in names]
    human, executor = value.get("human"), value.get("executor")
    require(all(isinstance(item, str) and item for item in agents), "Missing agent principals")
    require(len(set(agents)) == len(agents), "Step principals must be distinct")
    require(
        isinstance(human, str) and human not in agents,
        "Human principal must be distinct from agent principals",
    )
    require(isinstance(executor, str) and executor, "Missing executor principal")

    calls = load_jsonl(product / "calls.jsonl")
    windows = []
    for stage in stages:
        timing = stage.get("agent_execution") or {}
        start = parse_time(timing.get("started_at"), "Invalid agent window")
        end = parse_time(timing.get("finished_at"), "Invalid agent window")
        require(start <= end, "Invalid agent window")
        windows.append((start, end))
    for row in calls:
        actor = principal_id(row)
        if actor not in agents:
            continue
        when = parse_time(row.get("recordedAt"), "Invalid call timestamp")
        own = agents.index(actor)
        other = 1 - own
        require(
            not (windows[other][0] <= when <= windows[other][1]),
            "A step principal appears inside the other step's agent window",
        )
    return value, agents, human, executor, calls


def check_capture(trial, product, executor, first_step):
    atif = load_json(trial / f"steps/{first_step}/agent/trajectory.json")
    source = atif.get("session_id")
    require(isinstance(source, str) and source, "Missing first-step native session identity")
    rows = []
    for path in sorted((product / "capture").glob("*.jsonl")):
        rows.extend(load_jsonl(path))
    accepted = [
        row
        for row in rows
        if row.get("source_identity") == source
        and (row.get("status") == "accepted" or row.get("http_status") in (200, 201, 202))
    ]
    require(bool(accepted), "No accepted capture for the first-step native session")
    grouped = {}
    for row in accepted:
        key = (row.get("source_identity"), row.get("cursor"))
        require(all(isinstance(value, str) and value for value in key), "Invalid capture identity or cursor")
        grouped.setdefault(key, []).append(row)
    for rows_for_cursor in grouped.values():
        if any("effect" in row for row in rows_for_cursor):
            effects = sum(row.get("effect") is True for row in rows_for_cursor)
        else:
            effects = len({row.get("job_id") for row in rows_for_cursor})
        require(effects == 1, "Each capture identity and cursor must have one effect")

    jobs = {row.get("id"): row for row in load_jsonl(product / "jobs.jsonl")}
    for job_id in {row.get("job_id") for row in accepted if row.get("effect", True)}:
        job = jobs.get(job_id)
        require(job and job.get("state") == "settled", "Capture job did not settle")
        require(
            job.get("settled_by") == executor,
            "Capture job settled_by differs from the executor principal",
        )
    return source


def proposal_claims(proposal):
    claims = proposal.get("claim_ids") or []
    if not claims and isinstance(proposal.get("claims"), list):
        claims = [claim.get("id") for claim in proposal["claims"]]
    return [claim for claim in claims if isinstance(claim, str) and claim]


def proposal_state(proposal):
    history = proposal.get("state_history") or proposal.get("history") or []
    return history[-1].get("state") if history else proposal.get("state")


def accepted_claims(product, human, agents, policy):
    proposals = load_json(product / "proposals.json")
    require(isinstance(proposals, list), "Invalid proposals evidence")
    acceptances = load_jsonl(product / "acceptance.jsonl")
    for row in acceptances:
        if row.get("decision") == "accepted":
            require(row.get("actor_class") == "human", "Accepted proposals require a human actor")
            require(row.get("policy") == policy, "Acceptance policy differs from pins.json")
            require(
                row.get("actor_id") == human and row.get("actor_id") not in agents,
                "Acceptance actor differs from the declared human principal",
            )

    claims = {}
    for proposal in proposals:
        if proposal_state(proposal) != "accepted":
            continue
        matched = [
            row
            for row in acceptances
            if row.get("proposal_id") == proposal.get("id")
            and row.get("revision") == proposal.get("revision")
            and row.get("decision") == "accepted"
            and row.get("actor_class") == "human"
        ]
        require(len(matched) == 1, "Each accepted proposal revision needs one human acceptance")
        ids = proposal_claims(proposal)
        require(bool(ids), "Accepted proposal has no claim ids")
        for claim_id in ids:
            claims[claim_id] = {
                "claim": proposal.get("claim", ""),
                "artifact_id": proposal.get("artifact_id"),
                "evidence_refs": proposal.get("evidence_refs") or proposal.get("evidence") or [],
            }
    return claims, proposals


def last_agent_message(atif):
    messages = [
        step.get("message", "")
        for step in atif.get("steps", [])
        if step.get("source") == "agent" and isinstance(step.get("message"), str)
    ]
    return messages[-1] if messages else ""


def task_instruction(atif):
    messages = [
        step.get("message")
        for step in atif.get("steps", [])
        if step.get("source") == "user" and isinstance(step.get("message"), str)
    ]
    require(bool(messages), "Missing task instruction in agent trajectory")
    return messages[-1]


def edited_paths(value):
    found = set()

    def visit(item):
        if isinstance(item, dict):
            for key, child in item.items():
                if key in {"file_edits", "files_changed", "changes"} and isinstance(child, list):
                    for edit in child:
                        path = edit.get("path") if isinstance(edit, dict) else edit
                        if isinstance(path, str):
                            found.add(path.removeprefix("/app/"))
                visit(child)
        elif isinstance(item, list):
            for child in item:
                visit(child)

    visit(value)
    return found


def stream_edits(stream, after):
    items = []
    for event in stream[after + 1 :]:
        item = event.get("item") or {}
        if (
            event.get("type") == "item.completed"
            and item.get("type") == "file_change"
            and item.get("status") == "completed"
        ):
            items.append(item)
    return edited_paths(items), items


def atif_edits_after_retrieval(atif, claim_id):
    steps = atif.get("steps") or []
    for index, step in enumerate(steps):
        raw = json.dumps(step, sort_keys=True)
        if claim_id in raw and "recall" in raw:
            later = steps[index + 1 :]
            return edited_paths(later), later
    return set(), []


def tokens(value):
    return re.findall(r"[a-z0-9_./:-]+", value.lower())


def overlap(left, right, size=5):
    def grams(value):
        words = tokens(value)
        if len(words) < size:
            return {tuple(words)} if words else set()
        return {tuple(words[index : index + size]) for index in range(len(words) - size + 1)}

    proposal = grams(right)
    return len(grams(left) & proposal) / len(proposal) if proposal else 0


def check_instruction(task, step, atif, proposals, threshold):
    expected = (ROOT / f"evals/{task}/steps/{step}/instruction.md").read_text()
    instruction = task_instruction(atif)
    require(instruction == expected, "Step 2 instruction differs from the declared task bytes")
    for proposal in proposals:
        text = proposal.get("claim")
        if isinstance(text, str) and text:
            require(
                overlap(instruction, text) < threshold,
                "Step 2 instruction exceeds the declared proposal overlap threshold",
            )


def evidence_paths(claim):
    paths = set()
    for ref in claim.get("evidence_refs", []):
        if isinstance(ref, str) and ref.startswith("repo://"):
            paths.add(ref.removeprefix("repo://").split("#", 1)[0].lstrip("/"))
    return paths


def reward(stage):
    return ((stage.get("verifier_result") or {}).get("rewards") or {}).get("reward")


def write_review(product, claim_id, claim, context, edits, evidence):
    body = (
        "# Capture-to-reuse review\n\n"
        f"Claim: `{claim_id}`\n\n"
        f"{claim.get('claim', '')}\n\n"
        "## Agent context\n\n"
        f"{context}\n\n"
        "## Diff\n\n"
        + "\n".join(f"- `{path}`" for path in sorted(edits))
        + "\n\n```json\n"
        + json.dumps(evidence, indent=2, sort_keys=True)
        + "\n```\n"
    )
    (product / "review.md").write_text(body)


def review_applies(product):
    path = product / "review.json"
    if not path.is_file():
        return False
    review = load_json(path)
    require(isinstance(review.get("reviewer"), str) and review["reviewer"], "Invalid semantic review")
    require(review.get("verdict") == "applies", "Semantic review verdict is not applies")
    parse_time(review.get("time"), "Invalid semantic review time")
    return True


def audit_trial(trial, *, receipt=False, overlap_threshold=0.5):
    result = load_json(trial / "result.json")
    task, stages, names = task_steps(result)
    product = trial / "environment/product"
    pins = load_json(product / "pins.json")
    require(isinstance(pins, dict) and REQUIRED_PINS <= pins.keys(), "Incomplete pins.json")
    require(all(isinstance(pins[key], str) and pins[key] for key in REQUIRED_PINS), "Invalid pins.json")
    for key, allowed in PIN_VALUES.items():
        require(pins[key] in allowed, f"Invalid {key} pin")
    require(pins["task_checksum"] == result.get("task_checksum"), "pins task_checksum differs from trial")
    if receipt:
        require(pins["executor"] == "ported", "--receipt requires executor == ported")
        require(pins["accept"] == "person", "--receipt requires accept == person")

    _, agents, human, executor, calls = check_principals(product, stages, names)
    check_capture(trial, product, executor, names[0])
    claims, proposals = accepted_claims(product, human, agents, pins["accept"])
    atif = load_json(trial / f"steps/{names[1]}/agent/trajectory.json")
    check_instruction(task, names[1], atif, proposals, overlap_threshold)

    stream = native_events(trial / f"steps/{names[1]}/agent/codex.txt")
    retrievals = [
        (index, event["item"])
        for index, event in enumerate(stream)
        if event.get("type") == "item.completed"
        and event.get("item", {}).get("type") == "mcp_tool_call"
        and event["item"].get("server") == "agora"
        and event["item"].get("status") == "completed"
        and not event["item"].get("error")
    ]
    retrieved = None
    retrieval = None
    retrieval_index = None
    for index, item in retrievals:
        raw = json.dumps(item.get("result"), sort_keys=True)
        for claim_id in claims:
            if claim_id in raw:
                retrieved, retrieval, retrieval_index = claim_id, item, index
                break
        if retrieved:
            break

    final = last_agent_message(atif)
    edits = set()
    edit_evidence = []
    status, cited = "absent", False
    if retrieved:
        stage_2_start = parse_time(
            stages[1]["agent_execution"].get("started_at"), "Invalid step 2 agent window"
        )
        stage_2_end = parse_time(
            stages[1]["agent_execution"].get("finished_at"), "Invalid step 2 agent window"
        )
        matching_calls = [
            row
            for row in calls
            if principal_id(row) == agents[1]
            and row.get("tool") == retrieval.get("tool")
            and row.get("outcome") == "succeeded"
            and stage_2_start
            <= parse_time(row.get("recordedAt"), "Invalid call timestamp")
            <= stage_2_end
        ]
        require(bool(matching_calls), "Retrieved claim is missing from the step 2 call log")
        claim = claims[retrieved]
        stream_paths, stream_evidence = stream_edits(stream, retrieval_index)
        atif_paths, atif_evidence = atif_edits_after_retrieval(atif, retrieved)
        edits = stream_paths | atif_paths
        edit_evidence = stream_evidence + atif_evidence
        explicit_ids = [retrieved, claim.get("artifact_id")]
        cited = any(value and value in final for value in explicit_ids)
        edit_context = json.dumps(edit_evidence, sort_keys=True)
        cited = cited or any(value and value in edit_context for value in explicit_ids)
        applied = bool(evidence_paths(claim) & edits)
        if not applied:
            status = "retrieved-unapplied"
        elif reward(stages[1]) != 1:
            status = "failed-verifier"
        else:
            write_review(product, retrieved, claim, final, edits, edit_evidence)
            status = "verified" if review_applies(product) else "pending-review"

    return {
        "trial": trial.name,
        "task": task,
        "accept": pins["accept"],
        "executor": pins["executor"],
        "classification": "receipt" if pins["executor"] == "ported" else "plumbing",
        "reuse": status,
        "claim_id": retrieved,
        "cited": cited,
        "pins": pins,
    }


def audit_campaign(paths, *, receipt=False, overlap_threshold=0.5):
    require(0 <= overlap_threshold <= 1, "Overlap threshold must be between zero and one")
    reports = []
    campaign_pins = None
    for job in expand_jobs(paths):
        _, trial_paths = trials(job)
        job_pins = None
        for result_path in trial_paths:
            report = audit_trial(
                result_path.parent,
                receipt=receipt,
                overlap_threshold=overlap_threshold,
            )
            reports.append(report)
            pins = report["pins"]
            require(job_pins is None or pins == job_pins, f"{job}: mixed pins across trials")
            job_pins = pins
        stable = {key: value for key, value in job_pins.items() if key != "task_checksum"}
        require(campaign_pins is None or stable == campaign_pins, "Campaign has mixed pins across jobs")
        campaign_pins = stable
    policies = {report["accept"] for report in reports}
    classifications = {report["classification"] for report in reports}
    require(len(policies) == 1 and len(classifications) == 1, "Campaign has mixed verdict policy")
    return {
        "evidence_version": "capture-reuse-v1",
        "accept": policies.pop(),
        "classification": classifications.pop(),
        "receipt": receipt,
        "trials": reports,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directories", nargs="+", type=Path)
    parser.add_argument("--receipt", action="store_true")
    parser.add_argument("--overlap-threshold", type=float, default=0.5)
    args = parser.parse_args(argv)
    report = audit_campaign(
        args.directories,
        receipt=args.receipt,
        overlap_threshold=args.overlap_threshold,
    )
    print(json.dumps(report, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
