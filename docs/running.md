# Run the local dataset

Requirements: Python 3.12 or 3.13, uv, Docker with Compose and Buildx, and network access for the
initial dependency/image build. Synthetic tasks use the Python standard library; Django and Sphinx fixtures
include their pinned runtime dependencies locally. Harbor is pinned in uv.lock; the Python base image is pinned by digest.

## Credential-free validation

```sh
uv sync --locked
uv run python scripts/check.py
uv run harbor run -p evals -a oracle --env docker --jobs-dir evals/jobs --job-name oracle
```

The first check validates structure and runs every verifier against the untouched
fixture, a reference implementation, and a plausible incorrect implementation.
The Harbor command executes the actual lifecycle in Docker, including solution scripts,
hidden-test upload, multi-step resets, and artifact collection.

Task directories are also independently runnable. Copy any one directory and run
`harbor run -p /path/to/task -a oracle --env docker`; no parent-repository code is imported.
The dataset uses Harbor's native local directory discovery: `-p evals` selects its 25
task directories. No registry, remote repository, or published package is involved.
See [local datasets](https://docs.harborframework.com/core-concepts/datasets/datasets).

## Evaluate an agent

From the repository root, use the native Harbor Codex launch configuration:

```sh
CODEX_FORCE_AUTH_JSON=1 uv run harbor run -c overlays/baseline.yaml -p evals
```

This uses an existing `codex login` session from `~/.codex/auth.json`, consuming your
Codex subscription usage. Credentials are supplied at runtime, not stored in the dataset.
For API billing, set `OPENAI_API_KEY` securely in your shell and omit
`CODEX_FORCE_AUTH_JSON=1`. API-key authentication has not been tested here.

The config selects Codex 0.144.3, `openai/gpt-5.6-luna`, low reasoning effort, disabled
web search, and two concurrent trials. Luna is a
[cost-sensitive model](https://developers.openai.com/api/docs/models/gpt-5.6-luna).
To smoke-test only one task, replace `-p evals` with
`-p evals/notification-api-compatibility`.
To change only the model, append `-m openai/<model-id>`. Do not append `-a codex`
to this config: Harbor 0.23.0 replaces the entire agent entry when `-a` is supplied,
discarding its allowlist and pinned settings. Inspect any override with `--print-config`.

The usual `harbor run -p evals -a codex -m openai/gpt-5.6-luna` syntax discovers the
dataset, but **is not sufficient by itself**: tasks default to no network. Use the launch
command above instead: `-c overlays/baseline.yaml` supplies package-download hosts and OpenAI
hosts for inference. Package hosts remain reachable during the agent phase; verification
still runs without network access. No task definition is coupled to Codex.

Use the pinned runtime via `uv run harbor`, not a potentially older global installation.
Other agents need their own native Harbor launch configuration, provider credentials,
and package/API allowlists. Add only hosts required by the selected agent and tool.

Use [independent runtime overlays](../overlays/README.md) to compare a baseline, plain
notes, and a knowledge tool. Do not use `--resume-trajectory` for the cross-session
tasks: a fresh conversation is part of their contract.

## Evidence

Inspect the derived completion/token/latency score without starting any containers or
model calls:

```sh
uv run python scripts/score_job.py evals/jobs/codex-luna-dataset
```

The command prints JSON with task and step scores, correctness, finished/completed
status, tokens, agent seconds, scoring policy, and errors. It never rewrites the original
Harbor job or traces. See [the formula and limits](methodology.md#completion-and-efficiency-reward).
Use `--token-scale 100000 --seconds-scale 120` to make the defaults explicit.

Harbor writes the resolved job configuration, trial results, timing, agent trajectory
(when provided by the integration), verifier output, and source artifacts under
`evals/jobs/`. Each verifier writes:

- `reward.txt`: 1 for complete behavioral success, 0 for a completed failed suite.
- `checks.json`: test count and failure/error tracebacks.
- `checks.log`: readable test output.

Read both the job result and the per-step results. Missing scores, timeouts, build errors,
or verifier process crashes are infrastructure failures, not successful evaluations
and not evidence that the agent failed the task.

Do not publish raw jobs without reviewing them: credentialed agent traces can include
private inputs or environment details. They are intentionally Git-ignored.
