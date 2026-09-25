# Transactional acknowledgement of a durable buffer

Release acknowledged records without losing unacknowledged data or violating atomicity.

## Run

From the repository root (Docker must be running):

```sh
uv run harbor run -p evals/transactional-buffer-acknowledgement -a oracle --env docker --jobs-dir evals/jobs
```

This credential-free command checks the reference solution. See [running an agent](../../docs/running.md)
for model-backed trials and [tool integrations](../../overlays/README.md) for independent tool selection.

## Contract

Repair Buffer.acknowledge(ids) in src/buffer.py.
Delete only the acknowledged positive integer IDs, preserving other payloads and their order.
Duplicate and unknown IDs are harmless; empty input changes nothing. Accept any finite
iterable, including generators. Reject booleans, non-integers, zero, and negative IDs
with ValueError before deleting anything. If iteration or a database operation fails,
propagate the exception and leave every row unchanged. Successful deletions must survive
closing and reopening the database. Do not renumber surviving IDs or change the existing API.
Reclaiming SQLite pages for reuse is sufficient; file compaction is outside the contract.


## Verification

The verifier executes hidden Python standard-library behavioral tests and writes
`/logs/verifier/reward.txt`, `checks.json`, and `checks.log`.
A completed check suite scores 1 only when all checks pass; incorrect or missing
implementations score 0. Setup failures and verifier crashes produce no score.
The mutation check rejects: Per-item commits delete earlier records before a later invalid ID or database failure.
Public smoke tests, when present, are development aids; editing them cannot change the hidden score.

## Layout

```text
transactional-buffer-acknowledgement/
├── README.md
├── task.toml
├── instruction.md
├── environment/                 # Dockerfile and frozen source
├── solution/                    # known-good implementation
└── tests/                       # hidden behavior checks and negative fixture
```

## Provenance and limits

Adapted from `agora-bench/evals/chain2` at commit
`7c1ba317267adf95dc13e043b73cca5daa43b48d`.
This is a synthetic, reduced fixture with rewritten contracts and stronger verifiers,
not a reproduction of a full upstream repository benchmark or its historical scores.
No task requires Agora or awards points for invoking a particular tool.
The fixture isolates this behavior; passing it is not evidence of general production readiness of the evaluated agent.
