# Run the local dataset

Requirements: Python 3.12 or 3.13, uv, Docker with Compose and Buildx, and network access for the
initial dependency/image build. The task code and verifiers use only Python's standard
library. Harbor is pinned in uv.lock; the Python base image is pinned by digest.

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
The dataset uses Harbor's native local directory discovery: `-p evals` selects its ten
task directories. No registry, remote repository, or published package is involved.
See [local datasets](https://docs.harborframework.com/core-concepts/datasets/datasets).

## Evaluate an agent

For an Anthropic-backed Claude Code run, configure the provider credentials using Harbor's
documented agent setup, then choose the model explicitly:

```sh
export MODEL='your-provider/model-id'
uv run harbor run -p evals/notification-api-compatibility \
  -a claude-code -m "$MODEL" --env docker --jobs-dir evals/jobs \
  --allow-agent-host api.anthropic.com
```

Use the agent's documented model identifier. The example leaves the model choice to the
runner; it is not a benchmark claim. Other agents and providers have different setup,
credentials, and required hosts. Agent setup can download its runtime; task execution
defaults to no network, and the verifier always runs without network access.
Add only the hosts needed by the chosen model and tool.

Use [independent tool configuration](../tools/README.md) to compare a baseline, plain
notes, and a knowledge tool. Do not use `--resume-trajectory` for the cross-session
tasks: a fresh conversation is part of their contract.

## Evidence

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
