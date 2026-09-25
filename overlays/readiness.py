"""Fail-closed initialization evidence checks for the pinned tool versions."""

import json
from pathlib import PurePosixPath
import re


def check_index(arm, stdout):
    if arm == "baseline":
        if "No graph; baseline uses shell search." not in stdout:
            raise ValueError("Missing baseline initialization evidence")
        return {"graph_required": False}
    records = []
    for line in stdout.splitlines():
        if line.startswith("{"):
            records.append(json.loads(line))
    if arm == "codebase-memory-mcp":
        records = [r for r in records if r.get("status") == "indexed"]
        if len(records) != 1:
            raise ValueError("Missing codebase-memory-mcp indexed status")
        result = records[0]
        for key in ("skipped_count", "parse_partial_count"):
            if result.get(key) != 0:
                raise ValueError(f"Incomplete codebase-memory-mcp index: {key}")
        count = result.get("not_indexed_files_count")
        if type(count) is not int or count < 0:
            raise ValueError("Missing or invalid codebase-memory-mcp exclusion count")
        if count:
            excluded = result.get("not_indexed_files") or {}
            files = excluded.get("files") or []
            if (
                excluded.get("truncated") is not False
                or excluded.get("count") != count
                or len(files) != count
            ):
                raise ValueError("Incomplete codebase-memory-mcp exclusion evidence")
            for item in files:
                name = PurePosixPath(item.get("path", "")).name.casefold()
                notice = name in {
                    "license",
                    "authors",
                    "copying",
                    "copyright",
                    "notice",
                }
                # Explicit non-code exclusions only; ignored source and truncated
                # evidence still prevent agent startup. Preserve files in the task.
                asset = name.endswith(".svg") and item.get("reason") == "ignored-suffix"
                if not (notice and item.get("reason") == "skip-list" or asset):
                    raise ValueError(
                        f"Unapproved codebase-memory-mcp exclusion: {item}"
                    )
        nodes, edges = result.get("nodes"), result.get("edges")
        if (nodes, edges) != (
            result.get("expected_nodes"),
            result.get("expected_edges"),
        ):
            raise ValueError("codebase-memory-mcp index counts disagree")
    elif arm in {"codegraph", "graphify", "gitnexus"}:
        counts = re.findall(r"([\d,]+) nodes[, |]+([\d,]+) edges", stdout)
        if len(counts) != 1:
            raise ValueError(f"Missing or ambiguous {arm} graph counts")
        nodes, edges = (int(value.replace(",", "")) for value in counts[0])
        if arm == "gitnexus":
            capabilities = [r for r in records if "graph" in r and "fts" in r]
            if len(capabilities) != 1 or any(
                capabilities[0][key].get("status") != "available"
                for key in ("graph", "fts")
            ):
                raise ValueError("GitNexus graph/FTS readiness not proven")
    else:
        raise ValueError(f"Unknown overlay: {arm}")
    if any(type(count) is not int or count <= 0 for count in (nodes, edges)):
        raise ValueError(f"Empty or invalid {arm} graph")
    return {"graph_required": True, "nodes": nodes, "edges": edges}
