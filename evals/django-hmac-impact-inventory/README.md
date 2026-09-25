# Django HMAC impact inventory

A read-only, repository-wide direct-caller audit with a bounded upstream impact
catalog. Uses 863 unmodified Django Python files (146,717 lines) from commit
`9ffd4eae2ce7a7100c98f681e2b6ab818df384a4`.

The agent inventories direct calls to `salted_hmac`, then classifies 22 APIs and
provides shortest source-linked paths for affected APIs. The longest path spans
9 call edges. Password hashing, CSRF, and a signer factory supply negative
controls; shared names and crypto terminology are insufficient evidence.

## Why this task

Earlier provider research suggested that reusable inbound/static relationship
queries can reduce repeated repository exploration. This task tests that
hypothesis across signing, session cookies, authentication, and reset tokens.
It does not require MCP usage, reward tool calls, or assume a particular tool
will beat shell search. Unlike the execution-map task, no runnable public
scenario provides a single stack to record.

## Contract and grading

Native Harbor layout: `instruction.md`, `task.toml`, `environment/`, `solution/`,
and `tests/`. All source and the public endpoint catalog live under `/app/src`,
inside every frozen overlay's index boundary. Tool setup remains outside this
task. No model, adapter, overlay, or efficiency-scoring changes are required.

The hidden verifier checks source integrity, the complete direct-call set, all
22 classifications, shortest-path length, each edge, and its physical call
location. Expected edges were read from pinned source and independently
witnessed in the real Django runtime by `tests/validate_evidence.py`, including
SQLite-backed authentication. An AST scan checks direct-caller completeness;
runtime calibration checks all 27 curated edges and all classifications.
Any shortest path supported by these scoped relationships is accepted, as are
alternative physical lines within a multiline call and reordered JSON keys.

Correct work receives native reward 1; incorrect or missing work receives 0.
Verifier/evidence errors leave no reward. The existing host-side scorer can
apply correctness-first token/latency weighting without changing task grading.

The reference artifact is a witness, not grader input. `mutation.json` removes
a real intermediary while preserving plausible endpoints; it must fail.

## Run

From the dataset root:

```bash
uv run harbor run -p evals/django-hmac-impact-inventory -a oracle
CODEX_FORCE_AUTH_JSON=1 uv run harbor run -c overlays/baseline.yaml -p evals/django-hmac-impact-inventory
TASK_WORKSPACE="$PWD/evals/django-hmac-impact-inventory/environment/workspace" \
  .venv/bin/python -I -B evals/django-hmac-impact-inventory/tests/validate_evidence.py
```

## Provenance and limits

`environment/SOURCES.json` records archive URLs, hashes, exact selection, and
licenses for Django, asgiref, and sqlparse. This is the Python source subset,
not the full Django distribution. Vendored source is byte-identical to the
existing pinned fixture, including empty files. The base image is digest-pinned;
APT installation still requires build-time network access. Verification needs
no network or external credentials.

“Repository-wide” describes direct-call discovery. Transitive impact is bounded
to the published 22-entrypoint catalog and explicit concrete dispatch bindings;
this does not claim whole-program reachability for arbitrary Django extensions.
Runtime witnesses corroborate the scoped source facts, not all possible inputs.
The upstream source is public and may occur in training data. Small pilot runs
measure harness behavior and feasibility, not statistical tool superiority.
