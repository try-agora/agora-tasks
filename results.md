# Historical benchmark results

This report covers the original ten-task suite and its September 24, 2026 experiments.
The repository now has 25 tasks; later task-local experiments remain in their READMEs.
See [current engineering validation](docs/validation.md) for release readiness. Historical
failed runs remain failed even when a later release corrects a readiness policy.

**Baseline: 10/10 tasks completed, 12/12 stages passed, 0 infrastructure errors.**

The full-dataset measurement establishes a no-MCP control. A subsequent one-task
smoke test exercised all five arms and audited their initialization and traces.
Neither establishes a winning coding MCP.

**Measurement readiness:** the locked overlays passed all **50 task/overlay
combinations and 60 stages**, including initialization after both relay resets.
The canonical reference jobs are `overlay-locked-<arm>-oracle`, except Graphify's
final Python 3.12 lock check is `overlay-locked-graphify-oracle-v2`. These are
credential-free provisioning/reference checks, not full-dataset agent benchmarks.
See the [requirement-by-requirement audit](docs/validation-history.md#measurement-readiness-validated-locally).

## Locked-installation smoke

After introducing native dependency locks, all five arms passed a fresh
`checkout-discount-once` run. These jobs ran **sequentially**, with no overlap between
their trial timestamps. They are still single observations on one synthetic fixture,
not the repeated comparison described in the [measurement protocol](docs/methodology.md#measurement-protocol).

| Arm | Pass | MCP calls | Tokens | Index seconds | Agent seconds | Trial seconds | Derived score |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | Yes | 0 | 128,072 | 0.359 | 39.976 | 78.317 | 0.9189 |
| CodeGraph | Yes | 2 | 173,389 | 0.498 | 63.301 | 108.856 | 0.9020 |
| GitNexus | Yes | 1 | 203,539 | 3.956 | 66.187 | 139.021 | 0.8974 |
| Graphify | Yes | 1 | 173,237 | 0.385 | 54.032 | 102.842 | 0.9056 |
| codebase-memory-mcp | Yes | 8 | 307,131 | 6.569 | 87.839 | 134.293 | 0.8823 |

All four MCPs returned useful current-repository information before the edit: CodeGraph
returned source and callers, GitNexus returned indexed flows/symbols with FTS available,
Graphify returned nine relevant nodes and call edges, and codebase-memory-mcp returned its
project, six search hits, and six source snippets. No MCP transport errors were recorded.
The baseline used shell search without MCP. All four token representations matched.
Installation and indexing remained outside the agent execution timer.

Manual inspection also found failed agent self-checks and missing `pytest`; these were
not mistaken for verifier results. GitNexus, Graphify, and codebase-memory-mcp additionally
used the existing half-up quantizer after checking sub-cent direct-serialization inputs.
Baseline and CodeGraph used a pure formatter. All passed the unchanged verifier, whose
direct-serialization check supplies an already-finalized two-decimal total. Do not
interpret a verifier pass as exhaustive coverage of every possible input.

Evidence: `evals/jobs/overlay-locked-<arm>-codex/`, with arm names `baseline`,
`codegraph`, `gitnexus`, `graphify`, and `codebase-memory-mcp`.
These supersede neither the original traces nor their historical scores.

```sh
uv run python scripts/check_overlay_job.py evals/jobs/overlay-locked-graphify-codex
```

## Full-dataset coverage

| Arm | Tasks completed | Completion + efficiency | Evidence |
| --- | --- | --- | --- |
| Codex + shell/grep/ripgrep, no MCP | 10/10 | 0.9330 | One full local run |
| CodeGraph | — | — | Not run |
| GitNexus | — | — | Not run |
| Graphify | — | — | Full dataset not run |
| codebase-memory-mcp | — | — | Not run |

An em dash means unmeasured, not zero. Runtime integration readiness is tracked in
[`overlays/`](overlays/README.md), independently of task definitions.

## One-task overlay smoke: initialization and trace audit

Task: `checkout-discount-once`. **All five healthy arms passed** the unchanged
behavioral verifier. All four MCP arms made successful, useful MCP calls before
editing source; none silently fell back from a broken MCP in the retained healthy run.

| Arm | Pass | MCP calls | Total tokens | Init seconds | Agent seconds | Trial seconds | Derived score |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Shell / grep baseline | Yes | 0 | 130,652 | 0.33* | 47.60 | 87.68 | 0.9150 |
| CodeGraph | Yes | 2 | 173,419 | 1.05 | 52.52 | 101.79 | 0.9061 |
| GitNexus (corrected setup) | Yes | 1 | 229,472 | 3.59 | 69.01 | 178.17 | 0.8938 |
| Graphify | Yes | 1 | 172,436 | 0.37 | 52.62 | 111.54 | 0.9062 |
| codebase-memory-mcp (corrected setup) | Yes | 8 | 236,619 | 7.17 | 67.70 | 115.34 | 0.8936 |

`Init` is the environment's index phase, including common git initialization, CLI
startup, and required index components. *The baseline builds no graph; its 0.33s
is git initialization and command overhead. `Agent` excludes all environment setup.
`Trial` includes container startup, installation, indexing, agent setup/execution,
verification, artifact collection, and cleanup. The derived score uses agent time,
not cold-start time; initialization is **reported, not hidden or charged twice**.

All initial indexes were built before agent execution, as verified against Harbor's
phase timestamps. Total environment setup was 22.15 / 31.61 / 90.75 / 41.23 / 29.85s
in table order. Tool-install phases were 0.12 / 6.99 / 67.18 / 12.85 / 2.57s;
the common runtime phase was 15–24s. These are observed cold-container installations,
not controlled package-download benchmarks.

### What the traces showed

- **Baseline:** used `rg` for initial exploration and no MCP. It fixed the same
  serializer as every other arm.
- **CodeGraph:** initialization reported 5 files, 22 nodes, and 41 edges. Two
  `codegraph_explore` calls returned current source and caller relationships before
  editing; shell search and direct checks followed.
- **GitNexus:** initialization reported 22 nodes, 46 edges, 2 clusters, and 2 flows.
  The corrected run had FTS available; its `query` returned checkout/export flows,
  source definitions, and the offending serializer. Embeddings were disabled.
- **Graphify:** AST-only initialization reported 16 nodes and 33 edges without an
  LLM. `query_graph` returned nine relevant nodes and call edges before shell reads.
  Clustering and semantic extraction were disabled.
- **codebase-memory-mcp:** initialization reported 34 nodes and 105 edges, zero skipped or
  partial files. Calls were `list_projects` ×1, `search_graph` ×1, and
  `get_code_snippet` ×6, returning the indexed project, relevant symbols, source,
  and caller/callee data. Its index root was `/app/src`, not `/app`, because of
  the engine's broad-root guard; this covers all task source but excludes root docs.

Node/edge counts describe different graph schemas, not graph quality. Initialization
did not modify the tracked task inputs. Final collected source showed the same
serializer-only repair in every arm, and both verifier test methods passed each time.
The observed calls did not access hidden verifier or reference-solution paths.

The agents also made self-check mistakes: incorrect rounding expectations, searches
for a nonexistent public tests directory, and a Graphify-arm attempt to run unavailable
`pytest`. They recovered. Some chained shell commands returned zero even when an
earlier assertion failed; those exit codes were **not** treated as correctness proof.
Completion comes from the independent Harbor verifier, not the agent's claims.

### Token reconciliation

For every healthy arm, input, cached-input, and output counts matched in all four
places: Harbor `agent_result`, ATIF `final_metrics`, the final native cumulative
`token_count`, and Codex's `turn.completed` event. We use the last cumulative snapshot,
not the sum of snapshots. Cached input is already included in input; reasoning output
is already included in output. Neither is added again.

The five input / cached-input / output triples were:

| Arm | Input | Cached input (subset) | Output |
| --- | ---: | ---: | ---: |
| Baseline | 128,987 | 110,848 | 1,665 |
| CodeGraph | 172,025 | 131,072 | 1,394 |
| GitNexus | 227,542 | 197,120 | 1,930 |
| Graphify | 170,747 | 150,272 | 1,689 |
| codebase-memory-mcp | 234,561 | 196,608 | 2,058 |

MCP calls were counted from completed native tool events, not from text mentioning
a tool or only top-level ATIF names: Codex can wrap MCP calls inside `exec`.
Returned content was inspected manually; transport success alone is insufficient.

### Setup failures retained, not scored as tool performance

- `overlays-checkout-baseline`: host sandbox blocked Docker's build-cache write.
  Rerun with the required filesystem permission; no model ran in the failed attempt.
- `overlays-checkout-gitnexus`: graph construction exited zero but FTS download was
  blocked. The MCP returned an explicit degraded-search warning and no symbols;
  the agent fell back to grep and passed. **Excluded as a healthy MCP measurement.**
  Added the required extension host and a readiness assertion that refuses missing
  FTS. The `-v2` run confirmed useful search results.
- `overlays-checkout-codebase-memory-mcp`: `/app` was rejected as too broad. Setup
  failed before a model ran. The `-v2` run indexed `/app/src` under project `app`.

These earlier attempts remain under `evals/jobs/`. Their time and any model usage
are additional development cost, not included in the five retained-run rows.

### Reproduce this audit

Use the [five-arm launch commands](overlays/README.md#run-one-task-across-the-overlays).
The retained local jobs are `overlays-checkout-baseline-v2`,
`overlays-checkout-codegraph`, `overlays-checkout-gitnexus-v2`,
`overlays-checkout-graphify`, and `overlays-checkout-codebase-memory-mcp-v2`.

```sh
uv run python scripts/check_overlay_job.py evals/jobs/overlays-checkout-graphify
```

Inspect `<trial>/environment/{setup.jsonl,index.stdout.log,index.stderr.log}`,
`agent/codex.txt`, `agent/trajectory.json`, `agent/sessions/`, and `verifier/checks.json`.
The checker validates accounting and setup boundaries; manual trace review supplies
the semantic-use judgment. It now also checks backend initialization evidence and
automatically rejects the retained degraded GitNexus run. The same readiness check
runs before the agent in new trials. Raw evidence remains local and Git-ignored.

Settings: Harbor 0.23.0, Codex 0.144.3, Luna low, Node 22.14.0, one CPU, 4 GiB,
fresh per-trial state, and the same explicit MCP-first/grep-fallback instruction.
This is a **prompted-adoption integration smoke**, not natural tool selection.
Some setup/agent phases from different jobs overlapped on the host, the GitNexus
allowlist was repaired during the campaign, and transitive dependencies are recorded
but not fully locked. Treat timings as diagnostic, not a statistically controlled
ranking. The baseline used fewer tokens here; one tiny task cannot establish a winner.
The later relay check below validates reset-aware indexing; it does not retroactively
change this single-task campaign or establish full-dataset MCP coverage.

## Multi-step reset and accounting check

`overlay-relay-graphify-codex` passed both stages of
`cross-session-framework-reuse` using the native pre-agent indexing hook. A separate
credential-free reference run, `overlay-relay-graphify-oracle`, also passed both.
The same two-stage reference check passed for baseline, CodeGraph, GitNexus, and
codebase-memory-mcp (`overlay-relay-<arm>-oracle`). All ten reference stages had valid
pre-agent initialization evidence. Reference runs make no model or MCP calls;
they establish setup/solution compatibility, not comparative tool effectiveness.

| Stage | Correctness | MCP calls | Tokens | Index seconds | Agent seconds |
| --- | --- | ---: | ---: | ---: | ---: |
| rate-limit | 1 | 1 `query_graph` | 243,547 | 0.372 | 77.948 |
| authenticate | 1 | 1 `query_graph` | 132,533 | 0.391 | 53.237 |
| Total | 2/2 stages | 2 | 376,080 | 0.763 | 131.185 |

Derived task score: **0.901002**. Initial environment setup was 33.545s and total
trial time was 188.743s. Each step's indexing ran after workspace preparation and
before its agent timer; these index durations are separate from initial environment
setup and already included in total trial time.

Manual inspection found useful middleware, configuration, and routing symbols in
both MCP responses before edits. Each rebuilt graph had 20 nodes and 30 edges;
the second response described the reset source, not the first step's solution.
Both stages ran public/direct checks and passed the independent hidden verifier.
Fresh native sessions and all four token representations agreed per stage:
input/cache/output were 240,962/218,112/2,585 and 130,927/110,848/1,606.
This establishes lifecycle and accounting behavior, **not memory benefit or ranking**.

```sh
uv run python scripts/check_overlay_job.py evals/jobs/overlay-relay-graphify-codex
```

## Baseline evidence

Measured September 24, 2026, with Harbor **0.23.0**, Codex **0.144.3**,
`openai/gpt-5.6-luna`, low reasoning effort, web search disabled, two concurrent
trials, no injected MCP, skill, or notes instruction. Each task ran once; there
were no retries. This was a shell-capable agent, not an enforced grep-only policy.

| Task | Stages passed | Tokens | Agent seconds | Derived score |
| --- | ---: | ---: | ---: | ---: |
| Checkout discount once | 1/1 | 62,362 | 40.84 | 0.9362 |
| Cross-session deduplication reuse | 2/2 | 142,780 | 80.81 | 0.9332 |
| Cross-session framework reuse | 2/2 | 192,574 | 128.72 | 0.9167 |
| Download filename encoding | 1/1 | 39,706 | 43.84 | 0.9448 |
| Git remote normalization | 1/1 | 55,718 | 58.99 | 0.9313 |
| Middleware authentication | 1/1 | 65,762 | 55.24 | 0.9288 |
| Middleware rate limiting | 1/1 | 101,666 | 59.01 | 0.9166 |
| Notification API compatibility | 1/1 | 49,952 | 34.51 | 0.9444 |
| Stable record deduplication | 1/1 | 48,297 | 32.04 | 0.9464 |
| Transactional buffer acknowledgement | 1/1 | 63,139 | 49.72 | 0.9320 |
| **Total / task-mean score** | **12/12** | **821,956** | **583.71** | **0.9330** |

Input: 801,879 tokens, including 649,728 cached input tokens. Output: 20,077.
Cached tokens are already part of input and are not added twice. Multi-step row
tokens and seconds are sums; their scores average the two stage scores.
Job wall time was **13m 17s**, including setup and cleanup; agent seconds above
exclude installation, verification, and cleanup and are summed across trials.

Harbor reported an estimated API-equivalent cost of **$0.0675**. The run used
Codex subscription authentication, so this is **not a billed invoice** or a
promise of future pricing. Tool-side model costs are not included.

## Correctness first

Native verifier rewards remain binary and tool-independent. The separate,
versioned `completion-efficiency-v1` score is computed from saved Harbor results:

```text
stage score = 0.8 + 0.1 / (1 + tokens / 100000)
                  + 0.1 / (1 + agent_seconds / 120)
task score  = mean(stage scores), only if every declared stage passed
             0 for completed but incorrect work
             unscored for missing evidence or infrastructure failures
```

The report shows completion, tokens, and latency alongside this summary. The
80/10/10 weights and scales are an explicit exploratory policy, not a validated
universal ranking. See [scoring details](docs/methodology.md#completion-and-efficiency-reward).

## Reproduce and inspect

```sh
# New measurement: consumes model usage.
CODEX_FORCE_AUTH_JSON=1 uv run harbor run -c overlays/baseline.yaml \
  -p evals --job-name baseline-repeat

# Read the existing local evidence; no model calls.
uv run python scripts/check_job.py evals/jobs/codex-luna-dataset --expected 1 --count 10
uv run python scripts/score_job.py evals/jobs/codex-luna-dataset
```

The measured job is `evals/jobs/codex-luna-dataset`. Each trial stores `result.json`,
verifier outputs, source artifacts, and `agent/trajectory.json` (ATIF 1.7).
Multi-step evidence is under `steps/<step>/`; raw Codex sessions are under the
corresponding `agent/sessions/` directory. The job also records its resolved config.

Raw jobs are local and Git-ignored; they are **not bundled in this repository**.
This table is a summary of those local results, not a downloadable evidence archive.
Review and redact traces before publishing an evidence bundle. Earlier preflight
failures and the standalone smoke test are excluded from this full-dataset score.
The live run predates the shared-test-helper refactor; subsequent oracle checks
passed both multi-step tasks. See [validation history](docs/validation-history.md).

## What this establishes—and does not

The dataset executes end to end and the control agent solves every task. The
fixtures are small and synthetic, and correctness is already saturated. A single
run cannot establish statistical significance, real-repository performance, or
which MCP is best. Cross-session tasks permit relearning from source, so passing
without memory is expected and is not proof of memory effectiveness.

Before making comparative claims: validate each integration, collect repeated
paired runs with fixed settings, inspect actual tool use, and report variability,
indexing overhead, failures, and external usage—not just the composite score.
Larger tasks may be needed to discriminate correctness. Existing task contracts
will remain fixed for this comparison; any harder suite should be versioned.
