# Backward-compatible notification metadata

Evolve a shared API without changing legacy payloads or breaking sibling callers.

## Run

From the repository root (Docker must be running):

```sh
uv run harbor run -p evals/notification-api-compatibility -a oracle --env docker --jobs-dir evals/jobs
```

This credential-free command checks the reference solution. See [running an agent](../../docs/running.md)
for model-backed trials and [tool integrations](../../tools/README.md) for independent tool selection.

## Contract

Extend src/notify/core.py's build_payload to accept optional keyword-only sender and
category strings. Include each key only when its value is not None; empty strings are
intentional values and must be preserved. Calling build_payload(message) must still
produce exactly {"msg": message}. All existing alert, digest, and scheduler callers
must retain their behavior. Calls supplying metadata positionally must raise TypeError.
Do not introduce shared mutable payload state.


## Verification

The verifier executes hidden Python standard-library behavioral tests and writes
`/logs/verifier/reward.txt`, `checks.json`, and `checks.log`.
A completed check suite scores 1 only when all checks pass; incorrect or missing
implementations score 0. Setup failures and verifier crashes produce no score.
The mutation check rejects: Truthiness checks silently drop valid empty-string metadata.
Public smoke tests, when present, are development aids; editing them cannot change the hidden score.

## Layout

```text
notification-api-compatibility/
├── README.md
├── task.toml
├── instruction.md
├── environment/                 # Dockerfile and frozen source
├── solution/                    # known-good implementation
└── tests/                       # hidden behavior checks and negative fixture
```

## Provenance and limits

Adapted from `agora-bench/evals/pilot-bwcompat-floor` at commit
`7c1ba317267adf95dc13e043b73cca5daa43b48d`.
This is a synthetic, reduced fixture with rewritten contracts and stronger verifiers,
not a reproduction of a full upstream repository benchmark or its historical scores.
No task requires Agora or awards points for invoking a particular tool.
The fixture isolates this behavior; passing it is not evidence of general production readiness of the evaluated agent.
