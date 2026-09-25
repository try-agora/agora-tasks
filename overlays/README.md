# Runtime overlays

The experimental treatment lives here; the workload stays in `evals/`.
An overlay selects the agent/tool configuration, installation requirements, and
optional adoption instructions. No task imports this directory.

Native Harbor configs select the agent and MCP. A small Docker environment subclass
adds installation and indexing before the agent starts; it contains no task answers
or agent decision logic. The base task Dockerfile is unchanged.
Check their compatibility without starting a trial:
`uv run python scripts/test_overlays.py`. This checks configs, setup failure handling,
and accounting invariants without tool installation or MCP connectivity.
Harbor's [runtime MCP injection](https://github.com/harbor-framework/harbor/pull/1675)
lets the same task run with different MCP servers. Its
[Compose overlays](https://github.com/harbor-framework/harbor/pull/1676) can supply
tool infrastructure without changing task Dockerfiles; its
[skills option](https://docs.harborframework.com/core-concepts/jobs/skills) supplies
optional agent instructions independently.

## Compatibility and readiness

Task validation covers 25 tasks; the historical all-arm provisioning matrix below
covers only the original ten. It does not establish support for every new fixture.
The release readiness policy accepts a complete list of intentionally excluded
`LICENSE`, `AUTHORS`, `COPYING`, `COPYRIGHT`, or `NOTICE` files and ignored SVG assets.
It still rejects skipped source, truncated exclusion evidence, and partial parses.
This corrects the non-code exclusion failure without altering any task or old result.

Known limits of the pinned codebase-memory-mcp fast-mode integration:

- Sphinx includes templates/TeX with partial parses; readiness still rejects it.
- Excalidraw excludes declaration source and truncates its exclusion list; readiness
  still rejects it. A useful graph alone is insufficient to satisfy this contract.
- The [25-task campaign](../docs/campaign-n1-report.md) additionally found partial
  parses in Alamofire (18 files), Jellyfin (1), and both LevelDB fixtures (29 each).
  Those attempts stopped before model execution; permitted notice exclusions alone
  do not establish complete source coverage.
- eShop, NestJS, Jellyfin, and LevelDB previously failed on license/author exclusions.
  These exclusions are now permitted; a fresh eShop reference run passed the corrected
  startup path. Historical failed jobs are not rescored.

Unsupported combinations stop before model execution. Task correctness and optional
integration compatibility are reported independently. See [release checks](../docs/validation.md).

### Historical original-suite matrix

| Arm | Pinned version | Interface | Current status |
| --- | --- | --- | --- |
| [Baseline](baseline.yaml) | Codex 0.144.3 | Shell, grep/ripgrep; no MCP | Full dataset measured; locked setup/smoke passed |
| [CodeGraph](codegraph.mcp.json) | `@colbymchenry/codegraph@1.5.0` | MCP + CLI | 12-stage setup + locked live smoke passed |
| [GitNexus](gitnexus.mcp.json) | `gitnexus@1.6.9` | MCP + CLI | 12-stage setup + locked live smoke passed; FTS enforced |
| [Graphify](graphify.mcp.json) | `graphifyy[mcp]==0.9.32` | MCP + CLI | 12-stage setup + locked live smoke passed; AST-only |
| [codebase-memory-mcp](codebase-memory-mcp.mcp.json) | `v0.10.8` | MCP + CLI | 12-stage setup + locked live smoke passed; `/app/src` |

The pins identify measured versions, not latest releases. Multi-step overlays require
the reset-aware `StepIndexPlugin` below; omission fails before environment startup.
Graphify has also passed a two-step live trial with fresh sessions and rebuilt indexes.
All five arms passed two-step reference-solution checks of the reset/index lifecycle;
this does not substitute for live MCP adoption checks on every task.
The codebase-memory-mcp arm uses [DeusData/codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp),
not the complete Agora product. Results from other datasets are not imported here.

## Measured control

From the repository root:

```sh
CODEX_FORCE_AUTH_JSON=1 uv run harbor run -c overlays/baseline.yaml -p evals
```

This makes hosted model calls and consumes Codex usage. See
[authentication and network policy](../docs/running.md#evaluate-an-agent).
The baseline permits normal shell tools; it is not a forced grep-only algorithm.

An optional plain-notes control adds one run-time instruction:

```sh
CODEX_FORCE_AUTH_JSON=1 uv run harbor run -c overlays/baseline.yaml \
  -p evals --extra-instruction-path overlays/notes.md
```

It has not been benchmarked. Do not silently add notes to the existing baseline.

## MCP connection descriptors

The JSON files use Harbor's native `mcpServers` format. Commands execute **inside
the task sandbox**, not on the host. They require the matching pinned binary on
the sandbox's PATH. `--mcp-config` does not install that binary.

## Dependency locks

`locks/` contains native npm manifests/lockfiles for Codex, CodeGraph, and GitNexus,
plus a hashed Python 3.12 requirements lock for Graphify. Setup uses `npm ci` and
`pip --require-hashes --only-binary=:all:`; it does not resolve new tool dependencies
on each trial. Node and codebase-memory-mcp release archives have explicit SHA-256 checks.
The locks cover Linux ARM64/x64 packages; runtime validation here uses Linux ARM64.

Lock hashes, resolved tool packages, and the OS package inventory are retained in
environment phase logs. Debian packages and GitNexus's runtime FTS extension remain
external provisioning inputs, so this is not a fully hermetic/offline image build.
Keep image IDs and resolved inventories with each measured campaign.

To intentionally update a dependency, edit its manifest and regenerate the native
lock, then repeat reference and live smoke validation before comparing scores:

```sh
npm install --package-lock-only --ignore-scripts --no-audit --no-fund --prefix overlays/locks/codegraph
uv pip compile overlays/locks/graphify.in --universal --python-version 3.12 \
  --generate-hashes --output-file overlays/locks/graphify.txt
```

For full-fixture provisioning checks without model calls, use any arm name:

```sh
PYTHONPATH=. uv run harbor run -c overlays/smoke.yaml -p evals --ek arm=codegraph \
  --plugin overlays.environment:StepIndexPlugin -a oracle --job-name preflight-codegraph
uv run python scripts/check_overlay_job.py evals/jobs/preflight-codegraph --oracle
```

Oracle checks initialization and reference correctness, not MCP use or token efficiency.
The five locked overlays passed the original ten fixtures, including both workspace resets;
live MCP checks are recorded separately in [results](../results.md).

## Run one task across the overlays

From the repo root, after `uv sync --locked`:

```sh
PYTHONPATH=. CODEX_FORCE_AUTH_JSON=1 uv run harbor run -c overlays/smoke.yaml \
  -p evals/checkout-discount-once --ek arm=baseline \
  --extra-instruction-path overlays/smoke-instruction.md --job-name smoke-baseline
uv run python scripts/check_overlay_job.py evals/jobs/smoke-baseline

for arm in codegraph gitnexus graphify codebase-memory-mcp; do
  PYTHONPATH=. CODEX_FORCE_AUTH_JSON=1 uv run harbor run -c overlays/smoke.yaml \
    -p evals/checkout-discount-once --ek arm="$arm" \
    --mcp-config "overlays/$arm.mcp.json" \
    --extra-instruction-path overlays/smoke-instruction.md --job-name "smoke-$arm"
  uv run python scripts/check_overlay_job.py "evals/jobs/smoke-$arm" || break
done
```

The shared instruction asks for MCP-first exploration when available and grep
otherwise. This is **prompted adoption**, not a measurement of natural tool choice.
The task itself is unchanged. These commands consume model usage. Use fresh job
names for repeats; do not discard failed jobs.

### Multi-step workspace resets

Add the native pre-agent hook when selecting either relay task or the full dataset:

```sh
PYTHONPATH=. CODEX_FORCE_AUTH_JSON=1 uv run harbor run -c overlays/smoke.yaml \
  -p evals/cross-session-framework-reuse --ek arm=graphify \
  --plugin overlays.environment:StepIndexPlugin \
  --mcp-config overlays/graphify.mcp.json \
  --extra-instruction-path overlays/smoke-instruction.md --job-name relay-graphify
uv run python scripts/check_overlay_job.py evals/jobs/relay-graphify
```

Harbor uploads the step's workdir and runs its reset script, then the hook rebuilds
the graph, then Harbor starts the agent timer. Every step gets a fresh conversation;
`--resume-trajectory` is rejected. Tool installation happens once per trial, not per
step. No task file imports the hook or knows which tool is selected.

Step indexing is recorded under `environment/steps/<name>/index.*.log` and in
`environment/setup.jsonl`. It is **outside agent time**, but also outside Harbor's
initial `environment_setup` field. Report it separately; total trial time already
includes it. Agent traces and verifier artifacts live under `steps/<name>/`.
The offline checker audits every trial and every declared step, including setup
order, per-step usage reconciliation, and summed token totals.

[`environment.py`](environment.py) extends native Harbor Docker startup and runs
[`setup.sh`](setup.sh) in the disposable sandbox. The sequence is:

```text
unchanged task environment → common runtime → tool install → index → Codex → verifier
                            └──────── environment_setup ─────────┘
```

All arms use one CPU, 4 GiB, Node 22.14.0, Codex 0.144.3, and Luna low reasoning.
Git initialization is common to every arm. The environment layer checks that
initialization does not change tracked task inputs. Graph construction runs as
the same unprivileged user that later runs the MCP, preserving index ownership.

| Arm | Initialization before the agent |
| --- | --- |
| Baseline | No graph |
| CodeGraph | `codegraph init /app`; 5 source files in the smoke |
| GitNexus | `gitnexus analyze /app --index-only --workers 1`; require FTS available |
| Graphify | `graphify update /app --no-cluster`; AST-only, no LLM |
| codebase-memory-mcp | `codebase-memory-mcp cli index_repository --repo-path /app/src --name app --mode fast` |

codebase-memory-mcp rejects `/app` as too broad; `/app/src` contains all five source files
in this task but excludes README/CHANGELOG. GitNexus embeddings are off; Graphify
semantic extraction and clustering are off. These are explicit modes, not complete
feature-parity claims. All index state starts empty per trial.

Setup evidence lives in `<trial>/environment/`: `setup.jsonl` records UTC boundaries,
monotonic durations, exit codes, and exceptions for `common`, `install`, and `index`;
each phase retains stdout/stderr. Installation logs retain tool/dependency versions.
The index phase includes CLI startup and common git initialization, not just parsing.
Harbor's `environment_setup` also includes container startup and file upload. Neither
is counted in the agent-only efficiency score; report cold-start time separately.

```sh
uv run python scripts/check_overlay_job.py evals/jobs/smoke-codegraph
```

This reconciles tokens across Harbor, ATIF, native cumulative usage, and Codex's
completed-turn event; checks setup precedes agent execution; and requires an observed
MCP call for tool arms. The shared `readiness.py` gate also requires a nonempty graph,
proven GitNexus graph/FTS availability, and complete codebase-memory-mcp parsing/counts for the declared source scope. Environment
startup runs the same gate before spending model tokens and records its verdict in
`setup.jsonl`. Missing or ambiguous initialization evidence fails closed, including
older runs that exited zero with degraded search. It does **not** judge the semantic
usefulness of a call:
inspect `agent/codex.txt` and `agent/trajectory.json` manually. MCP calls can be nested
inside ATIF `exec` calls, so counting top-level ATIF function names alone is incorrect.

For adoption instructions, append `--skill /absolute/path/to/reviewed-skill`.
Pin and record that skill revision; compare skill-on and skill-off separately.
Do not append `-a codex`: that replaces the agent configuration in Harbor 0.23.0.
Inspect any candidate command with `--print-config` before executing it.

Provisioning must use upstream installation instructions for the pinned release:
[CodeGraph](https://github.com/colbymchenry/codegraph),
[GitNexus](https://github.com/abhigyanpatwari/GitNexus),
[Graphify](https://github.com/Graphify-Labs/graphify), and
[codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp).
Do not use unpinned `npx ...@latest` or download tools on the first MCP call.
Those hide installation cost inside agent latency and complicate failure diagnosis.

### Graphify

Graphify has a [local MCP server](https://graphify.com/mcp). The pinned
[`graphifyy` 0.9.32 package](https://pypi.org/project/graphifyy/0.9.32/) declares
`graphify-mcp = graphify.serve:_main` as a console entrypoint. Its `mcp` extra
installs the server dependencies. For a standalone installation:

```sh
uv tool install "graphifyy[mcp]==0.9.32"
```

The overlay invokes `graphify-mcp /app/graphify-out/graph.json --transport stdio`.
This console script uses the tool environment's Python; a bare
`python -m graphify.serve` can fail when system Python cannot see uv's isolated
installation. Ensure uv's tool-bin directory is on the sandbox agent's PATH.

Our environment layer installs the same package into `/opt/graphify` using the
already available Python/venv, puts its console scripts on PATH, then generates the
graph separately. No extra uv runtime is needed in the container. No hosted Graphify
endpoint, account, semantic model call, or source upload is used.

## Isolation and fair comparison

- Keep instructions, source fixtures, verifiers, and reference solutions unchanged.
- Give the tool only `/app` as its repository input. Never mount or index the host
  dataset, `/tests`, `/solution`, or reference sources under `/opt/task`.
- Use fresh per-trial tool state, no shared external index, and no host Docker socket.
  Treat `/memory` as trial-local persistent state, not a cross-trial cache.
- Reconcile indexes after multi-step workspace resets. Measure cold indexing and
  warm reuse separately; do not reuse stale code or a previous trial's answers.
- Hold model, reasoning effort, budgets, network policy, and concurrency fixed.
  Record tool versions, resolved dependencies, skill hashes, installation/indexing
  time, agent latency, and any tool-side model usage separately.
- Verify MCP connection and actual calls in the trace. A passing task with a failed
  MCP connection or unused tool is not evidence of tool effectiveness.
- Fail provisioning errors visibly. Never silently replace a broken MCP arm with
  the baseline. Run a smoke test before a paid comparison campaign.

This is a cooperative evaluation boundary, not protection against a malicious
agent or MCP. See [methodology](../docs/methodology.md) for verifier limitations.
The same completion scorer applies to every arm; see [results](../results.md).
