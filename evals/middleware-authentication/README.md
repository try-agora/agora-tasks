# Optional authentication middleware

Add a security boundary while preserving opt-in behavior and middleware composition.

## Run

From the repository root (Docker must be running):

```sh
uv run harbor run -p evals/middleware-authentication -a oracle --env docker --jobs-dir evals/jobs
```

This credential-free command checks the reference solution. See [running an agent](../../docs/running.md)
for model-backed trials and [tool integrations](../../tools/README.md) for independent tool selection.

## Contract

Add optional authentication to Microapp through its registered middleware extension point.
When config.DEFAULTS["auth_required"] is true, reject requests without a nonblank
Authorization header with status 401. Header names are case-insensitive. Presence is
the contract here: token cryptography is outside this fixture. When false, preserve
anonymous access. Authorized requests retain normal routing; logging must still wrap
every request, including rejected ones. Do not mutate caller-owned headers.
Keep the existing App.handle interface. Run the public tests and add your own checks.


## Verification

The verifier executes hidden Python standard-library behavioral tests and writes
`/logs/verifier/reward.txt`, `checks.json`, and `checks.log`.
A completed check suite scores 1 only when all checks pass; incorrect or missing
implementations score 0. Setup failures and verifier crashes produce no score.
The mutation check rejects: Case-sensitive header lookup that also accepts whitespace-only credentials.
Public smoke tests, when present, are development aids; editing them cannot change the hidden score.

## Layout

```text
middleware-authentication/
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
