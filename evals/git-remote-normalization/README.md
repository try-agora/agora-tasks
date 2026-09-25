# Normalize Git remotes without losing ports

Parse URL and SCP-style remotes while preserving identity and validating malformed input.

## Run

From the repository root (Docker must be running):

```sh
uv run harbor run -p evals/git-remote-normalization -a oracle --env docker --jobs-dir evals/jobs
```

This credential-free command checks the reference solution. See [running an agent](../../docs/running.md)
for model-backed trials and [tool integrations](../../overlays/README.md) for independent tool selection.

## Contract

Repair parse_remote(value) in src/remotes.py. Return exactly these fields:
transport ("ssh" or "https"), lowercase host, integer port, user (string or None),
and repository path without surrounding slashes or a terminal ".git".
Support absolute ssh:// and https:// URLs and SCP-style [user@]host:path.
Preserve nested repository paths and explicit ports, including bracketed IPv6 URL hosts.
Default ports are 22 and 443. SCP syntax always means SSH, never host:port.
Raise ValueError for local paths, empty/non-string inputs, any whitespace, unsupported
schemes, embedded passwords, invalid ports, query strings, fragments, and repository
paths containing empty, "." or ".." components. No network access is needed.


## Verification

The verifier executes hidden Python standard-library behavioral tests and writes
`/logs/verifier/reward.txt`, `checks.json`, and `checks.log`.
A completed check suite scores 1 only when all checks pass; incorrect or missing
implementations score 0. Setup failures and verifier crashes produce no score.
The mutation check rejects: An otherwise valid parser silently drops explicit ports.
Public smoke tests, when present, are development aids; editing them cannot change the hidden score.

## Layout

```text
git-remote-normalization/
├── README.md
├── task.toml
├── instruction.md
├── environment/                 # Dockerfile and frozen source
├── solution/                    # known-good implementation
└── tests/                       # hidden behavior checks and negative fixture
```

## Provenance and limits

Adapted from `agora-bench/evals/chain1` at commit
`7c1ba317267adf95dc13e043b73cca5daa43b48d`.
This is a synthetic, reduced fixture with rewritten contracts and stronger verifiers,
not a reproduction of a full upstream repository benchmark or its historical scores.
No task requires Agora or awards points for invoking a particular tool.
The fixture isolates this behavior; passing it is not evidence of general production readiness of the evaluated agent.
