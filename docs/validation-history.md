# Historical validation: original ten-task suite

This record describes September 24, 2026 checks on the original ten tasks.
It is not current 25-task release coverage. See [current validation](validation.md).

# Validation record

Validated locally on 2026-09-24 with Harbor 0.23.0, Docker 29.5.2, and Linux ARM64
containers on Colima. Reference-solution checks establish solvability; the live Codex
run below checks end-to-end usability, not comparative model or tool performance.

## Measurement readiness: validated locally

The current overlays and tasks are ready for the controlled local measurement
protocol. This is readiness evidence, not a claim that any MCP is best.

| Requirement | Verified evidence |
| --- | --- |
| Independent dataset and runtime treatments | 10 native Harbor tasks, 12 stages; no task imports an overlay |
| All-fixture initialization and reference correctness | 50/50 task/overlay combinations, 60/60 stages, zero infrastructure errors |
| Current dependency locks | Canonical setup logs match the current lock hashes |
| Reset-aware indexing outside agent time | All relay reference runs pass; live Graphify relay has two reconciled sessions |
| Actual MCP use | All four MCPs return useful source/graph information before edits in the locked smoke |
| Tokens and latency | All five locked smoke runs reconcile Harbor, ATIF, native cumulative usage, and completed-turn counts |
| Correctness-first scoring | Failed work scores zero; missing evidence/infrastructure errors remain unscored |
| Failure gates | Degraded GitNexus evidence rejected; native Harbor entrypoint test confirms index failure prevents agent/timer startup |
| Validation and packaging | 36 verifier scenarios, 12 unit tests, lint, shell syntax, and local documentation links pass |
| Local-only sharing boundary | No remote configured; raw jobs remain Git-ignored |

Canonical full-fixture jobs are `overlay-locked-<arm>-oracle` for baseline,
CodeGraph, GitNexus, and codebase-memory-mcp; Graphify uses
`overlay-locked-graphify-oracle-v2`. Its earlier passing job used a lock generated
for Python 3.13 and remains retained, but is superseded by the Python 3.12 recheck.

Native npm locks now freeze Codex, CodeGraph, and GitNexus dependencies; Graphify
uses hashed, wheel-only requirements. Node and codebase-memory-mcp archives are checksum pinned.
All five locked live smoke runs passed, with useful MCP responses manually inspected,
four-way token reconciliation, and sequential trial timestamps. All five full-dataset
reference jobs passed 10 tasks/12 stages and initialization checks, including
Graphify's final lock repeat. OS-package inventories were identical
across those 50 reference trials. Debian packages and the runtime FTS extension remain
external provisioning inputs, not fully hermetic build inputs.

The [measurement protocol](methodology.md#measurement-protocol) freezes settings,
rotates arm order across repetitions, runs one job at a time, and distinguishes
infrastructure/adoption failures from task correctness. A repeated full model campaign
is the next measurement, not a prerequisite for claiming that the runner can measure.

Closed gap: the offline checker previously accepted the degraded GitNexus run
because its call completed at the transport level. `overlays/readiness.py` now checks
index counts, graph/FTS availability, and codebase-memory-mcp parse completeness. Environment
startup and offline inspection share this fail-closed gate. All five healthy saved
runs pass; the retained degraded run is rejected. Tests cover zero/absent graphs,
missing/unavailable FTS, partial parsing, and setup exceptions. No historical
scores or raw run artifacts were rewritten.

Reset-aware indexing now uses Harbor's native pre-agent hook, after each step's
workspace setup and before the agent execution timer. All five overlays passed
two-step reference runs on `cross-session-framework-reuse`; initialization evidence
passed the timing/readiness checker for each step. Graphify also passed a live
Codex run on that relay. Both live
steps used fresh sessions and useful MCP responses from rebuilt graphs; their
token counts reconciled across all four telemetry formats. See the relay evidence
in [results](../results.md#multi-step-reset-and-accounting-check).

The checker now covers multiple trials and stages. Regressions exercise missing
or reordered setup, indexing that overlaps agent execution, repeated cumulative
token snapshots, and mismatched usage in the second stage of a second trial.
Hook tests reject repeated steps, cross-trial lookup, resumed conversations, and
failed indexing without advancing the step lifecycle.

After these changes, all 36 task verifier scenarios, all 12 result/scoring/overlay
unit tests, shell syntax, and Python lint passed. No task source was changed by
the overlay lifecycle work. Reference-run jobs are named
`evals/jobs/overlay-relay-<arm>-oracle`; these validate setup and solutions, not
actual MCP adoption or model efficiency.

Recheck the final full-fixture setup evidence without running agents:

```sh
uv run python scripts/check_overlay_job.py evals/jobs/overlay-locked-graphify-oracle-v2 --oracle --count 10
```

## Results

| Check | Result |
| --- | --- |
| Native local-dataset discovery | 10 tasks resolved from evals/ |
| Task configuration and structure | 10 task configurations parsed |
| Reference implementations against hidden verifiers | 12/12 stages pass |
| Untouched fixtures against hidden verifiers | 12/12 correctly rejected |
| Plausible wrong implementations against hidden verifiers | 12/12 correctly rejected |
| Harbor/Docker reference solutions | All 10 tasks, including all 12 stages, pass after the correction below |
| Live Codex / GPT-5.6 Luna | 10/10 tasks and 12/12 stages pass; zero trial or step exceptions |
| False-green job-result regression | Pass |
| Python lint and formatting | Pass |
| Formatting behavior check | Python ASTs unchanged for all 77 task Python files |

The eight single-step tasks passed in the `oracle-validation` job. Both multi-step tasks
passed in the subsequent `oracle-relay-validation` job:

| Multi-step task | First stage | Second stage |
| --- | --- | --- |
| cross-session-framework-reuse | rate-limit: 1 | authenticate: 1 |
| cross-session-deduplication-reuse | accounts: 1 | emails: 1 |

## Failure found and corrected

The first container run exposed a real isolation issue: verification ran Python with
`-I`, which ignores environment flags. It created root-owned bytecode caches inside
the agent-owned source tree. The next session could not remove those caches during reset.
The verifier now uses `python -I -B`, explicitly disabling bytecode writes.
Only the two affected multi-step trials were rerun.

Harbor's aggregate output reported a reward of 1 even though those second-step setups
had failed. The repository's result checker therefore requires every expected stage,
rejects step-level exceptions and missing scores, and checks each stage's reward.
`scripts/test_check_job.py` retains a regression for that false-green summary.

Initial attempts also exposed missing host prerequisites: writable Harbor build cache
and Docker Buildx. Those attempts are infrastructure failures and are excluded from
the passing results.

## Live Codex validation

Codex 0.144.3 with `openai/gpt-5.6-luna`, low reasoning effort, and web search disabled
passed the notification compatibility smoke task. The trajectory shows source inspection,
a real code edit, and public/direct behavior checks; the hidden verifier passed both
checks and Harbor recorded no exception. Authentication used an existing ChatGPT login,
not an API key. This consumes Codex usage; any dollar estimate in Harbor is not an invoice.

The subsequent full local dataset run, `evals/jobs/codex-luna-dataset/`, completed all
10 tasks and all 12 stages with reward 1. There were no retries, missing stages, or
trial/step exceptions. Both multi-step tasks produced distinct Codex session IDs per
stage. Trajectories contain source inspection and code edits; the hidden behavioral
checks passed. No memory-tool configuration or notes instruction was injected.

| Full dataset run | Recorded value |
| --- | --- |
| Attempts | One per task, two concurrent trials |
| Wall time, including installation and cleanup | 13 minutes 17 seconds |
| Input tokens, including cached input | 801,879 |
| Cached input tokens | 649,728 |
| Output tokens | 20,077 |
| Harbor token-cost estimate | $0.0675; not subscription billing evidence |

This is a single end-to-end validation run on small synthetic fixtures, not a model
ranking or evidence of memory-tool benefit. Source artifacts were collected successfully;
Harbor emitted relative-path Compose-copy warnings and recovered using its engine-copy
fallback. Trial containers were cleaned up automatically.

```sh
CODEX_FORCE_AUTH_JSON=1 uv run harbor run -c overlays/baseline.yaml -p evals
uv run python scripts/check_job.py evals/jobs/codex-luna-dataset --expected 1 --count 10
```

The second command audits the retained named run; a new run uses a timestamped directory
unless `--job-name` is supplied.

### Completion/efficiency scoring and test organization

The saved Luna evidence, without any new inference, scores **0.933027** under
`completion-efficiency-v1` (80% correct completion, 10% token efficiency, 10% latency
efficiency; scales 100,000 tokens and 120 agent seconds per stage). All 10 tasks still
have behavioral correctness 1. The original Harbor rewards and traces were not changed.
This is retrospective scoring under an explicit initial policy, not evidence of a
memory benefit; see [the formula and caveats](methodology.md#completion-and-efficiency-reward).

Both multi-step tasks now share grading/output plumbing in their own root
`tests/helpers.py`, with distinct behavioral assertions remaining in each step. This
matches Harbor's base-tests-plus-step-overlay layout and preserves task independence.
All 36 baseline/reference/mutation checks passed after the refactor. A new credential-free
Docker job, `evals/jobs/oracle-shared-tests/`, passed both tasks and all four stages with
zero exceptions. The live Luna run above predates this behavior-preserving refactor.

`scripts/test_score_job.py` checks correctness gating, efficiency ordering, cache counting,
all-step completion, missing/invalid telemetry, infrastructure errors, retry rejection,
and preservation of original result files.

Two preliminary attempts were infrastructure failures, not model task failures:

- `codex-mini-preflight`: the bare command could not install Codex dependencies because
  task containers default to no network. `overlays/baseline.yaml` now supplies run-specific
  package and inference host allowlists; verifier networking remains disabled.
- `codex-mini-smoke`: installation and model connectivity succeeded, but the service
  rejected `gpt-5.1-codex-mini` for ChatGPT authentication. The current launch config uses
  the supported, low-cost Luna model instead.

The successful smoke job is `evals/jobs/codex-luna-smoke/`:

```sh
uv run python scripts/check_job.py evals/jobs/codex-luna-smoke --expected 1 --count 1
```

## Inspect or reproduce

Local run artifacts are retained under `evals/jobs/oracle-validation/` and
`evals/jobs/oracle-relay-validation/`, including the initial failed stages. Jobs are
Git-ignored and are not part of the shareable dataset. The corrected relay evidence can
be checked without launching anything:

```sh
uv run python scripts/check_job.py evals/jobs/oracle-relay-validation --expected 1 --count 2
```

For a future full validation:

```sh
uv run python scripts/check.py
uv run python scripts/test_check_job.py
uv run harbor run -p evals -a oracle --env docker --jobs-dir evals/jobs --job-name oracle
uv run python scripts/check_job.py evals/jobs/oracle --expected 1
```

The CI workflow repeats source checks and Oracle trials, and additionally runs a Harbor
no-op agent. That workflow has been authored but has not run on GitHub; the repository
is local only. Tool integrations have been smoke-tested; repeated full-dataset MCP
comparisons and general full-repository performance remain unmeasured.
