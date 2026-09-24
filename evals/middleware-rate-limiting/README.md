# Per-client rate limiting

Extend an unfamiliar middleware pipeline without breaking state lifetime or routing.

## Run

From the repository root (Docker must be running):

```sh
uv run harbor run -p evals/middleware-rate-limiting -a oracle --env docker --jobs-dir evals/jobs
```

This credential-free command checks the reference solution. See [running an agent](../../docs/running.md)
for model-backed trials and [tool integrations](../../tools/README.md) for independent tool selection.

## Contract

Implement per-client request limits in Microapp using its registered middleware extension point.
Allow exactly config.DEFAULTS["rate_limit"] requests for each client per App instance,
then return status 429. Counts must persist across requests, but not across App instances.
A zero limit blocks every request. The configuration is a nonnegative integer.
Preserve routing, request headers, and the existing logging middleware's before/after events.
Keep the existing App.handle interface. Run the public tests and add your own checks.


## Verification

The verifier executes hidden Python standard-library behavioral tests and writes
`/logs/verifier/reward.txt`, `checks.json`, and `checks.log`.
A completed check suite scores 1 only when all checks pass; incorrect or missing
implementations score 0. Setup failures and verifier crashes produce no score.
The mutation check rejects: A middleware that resets its counter on every request.
Public smoke tests, when present, are development aids; editing them cannot change the hidden score.

## Layout

```text
middleware-rate-limiting/
├── README.md
├── task.toml
├── instruction.md
├── environment/                 # Dockerfile and frozen source
├── solution/                    # known-good implementation
└── tests/                       # hidden behavior checks and negative fixture
```

## Provenance and limits

Adapted from `agora-bench/evals/pilot-comprehension-floor` at commit
`7c1ba317267adf95dc13e043b73cca5daa43b48d`.
This is a synthetic, reduced fixture with rewritten contracts and stronger verifiers,
not a reproduction of a full upstream repository benchmark or its historical scores.
No task requires Agora or awards points for invoking a particular tool.
The fixture isolates this behavior; passing it is not evidence of general production readiness of the evaluated agent.
