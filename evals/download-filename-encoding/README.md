# Safe download filenames

Preserve Unicode filenames and quoted parameters while rejecting header injection.

## Run

From the repository root (Docker must be running):

```sh
uv run harbor run -p evals/download-filename-encoding -a oracle --env docker --jobs-dir evals/jobs
```

This credential-free command checks the reference solution. See [running an agent](../../docs/running.md)
for model-backed trials and [tool integrations](../../tools/README.md) for independent tool selection.

## Contract

Implement attachment_header(filename) in src/downloads.py.
Return an ASCII Content-Disposition value with disposition "attachment" and a quoted
filename parameter. ASCII basenames must round-trip exactly, including quotes,
backslashes, spaces, and semicolons. Non-ASCII names must include a nonempty ASCII fallback
and filename*=UTF-8'' followed by percent-encoded UTF-8 preserving the exact original name.
Reject empty/non-string inputs and every ASCII control character (U+0000–001F, U+007F)
with ValueError. In particular, CR and LF must never enter a response header.
The input is a basename; no path resolution is required.


## Verification

The verifier executes hidden Python standard-library behavioral tests and writes
`/logs/verifier/reward.txt`, `checks.json`, and `checks.log`.
A completed check suite scores 1 only when all checks pass; incorrect or missing
implementations score 0. Setup failures and verifier crashes produce no score.
The mutation check rejects: An encoder accepts CR/LF and other forbidden control characters.
Public smoke tests, when present, are development aids; editing them cannot change the hidden score.

## Layout

```text
download-filename-encoding/
├── README.md
├── task.toml
├── instruction.md
├── environment/                 # Dockerfile and frozen source
├── solution/                    # known-good implementation
└── tests/                       # hidden behavior checks and negative fixture
```

## Provenance and limits

Adapted from `agora-bench/evals/pilot-rework2` at commit
`7c1ba317267adf95dc13e043b73cca5daa43b48d`.
This is a synthetic, reduced fixture with rewritten contracts and stronger verifiers,
not a reproduction of a full upstream repository benchmark or its historical scores.
No task requires Agora or awards points for invoking a particular tool.
The fixture isolates this behavior; passing it is not evidence of general production readiness of the evaluated agent.
