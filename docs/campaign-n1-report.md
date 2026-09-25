# codebase-memory-mcp: single-pass engineering evaluation

One attempt per task using `openai/gpt-5.6-luna` at low reasoning effort. This is a descriptive run of the frozen 25-task suite, not evidence of a tool ranking. See the [protocol and scope amendment](campaign-n1.md).

Run on **2026-09-25, 13:53:56–14:40:54 UTC**.

## Observed coverage

Of 25 attempted tasks, **14 passed, 4 produced incorrect work, and 7 failed before a valid behavioral verdict**. Both stages must pass for a two-stage task to count as passed.

| Measurement | Observed value |
| --- | ---: |
| Completed agent stages with audited telemetry | 20 / 27 planned |
| Trials with audited MCP calls | 17 |
| MCP calls in audited stages | 82 |
| MCP transport errors in audited stages | 0 |
| Input tokens (cached input included) | 5,469,182 |
| Cached input tokens (subset of input) | 4,711,936 |
| Output tokens | 47,526 |
| Harbor price-based cost estimate (not subscription billing) | $0.3027 |
| Known agent time | 25.77 minutes |
| Whole-job wall time | 46.95 minutes |
| Audited common setup / installation / indexing time | 4.65 / 0.79 / 2.80 minutes |
| Full-suite derived efficiency score | unavailable (`null`) |

Input tokens already include cached input; adding cache again would double-count it. These are token volumes, not an invoice or a measure of remaining Codex credits. Agent time excludes provisioning, indexing, and verification. Audited phase totals above cover valid setups only; whole-job time also includes failed setup work. Missing usage is not zero-cost evidence.

## Per-task outcomes

| Task | Outcome | Tokens | Agent seconds | Index seconds | Audited MCP calls |
| --- | --- | ---: | ---: | ---: | ---: |
| alamofire-deferred-validation-audit | infra | — | — | — | 0 |
| checkout-discount-once | pass | 235,019 | 57.9 | 6.9 | 11 |
| cross-session-deduplication-reuse | pass | 420,677 | 116.9 | 13.4 | 6 |
| cross-session-framework-reuse | pass | 476,521 | 146.2 | 13.4 | 15 |
| django-hmac-impact-inventory | fail | 375,822 | 106.0 | 12.0 | 3 |
| django-lookup-hierarchy-audit | fail | 324,618 | 98.4 | 11.8 | 3 |
| django-multi-parent-update | pass | 612,327 | 111.0 | 11.4 | 3 |
| django-query-execution-map | fail | 438,282 | 111.1 | 11.8 | 2 |
| django-upsert-column-mapping | pass | 376,080 | 73.8 | 12.1 | 3 |
| django-utility-fan-in-ranking | pass | 203,743 | 87.9 | 11.8 | 2 |
| download-filename-encoding | pass | 161,124 | 48.1 | 6.7 | 3 |
| eshop-order-lifecycle-audit | pass | 402,755 | 94.4 | 7.2 | 2 |
| excalidraw-render-invalidation-audit | infra | — | — | — | 0 |
| git-remote-normalization | pass | 230,282 | 79.8 | 6.9 | 4 |
| jellyfin-playback-negotiation-audit | infra | — | — | — | 0 |
| leveldb-read-cache-audit | infra | — | — | — | 0 |
| leveldb-write-path-audit | infra | — | — | — | 0 |
| middleware-authentication | pass | 192,419 | 89.7 | 6.8 | 7 |
| middleware-rate-limiting | pass | 211,740 | 60.0 | 7.4 | 5 |
| nestjs-http-lifecycle-audit | fail | 172,806 | 66.3 | 7.9 | 0 |
| notification-api-compatibility | pass | 230,572 | 51.2 | 6.7 | 5 |
| sphinx-extension-event-routing | infra | — | — | — | 0 |
| sphinx-prolog-document-titles | infra | — | — | — | 0 |
| stable-record-deduplication | pass | 201,998 | 62.5 | 6.7 | 4 |
| transactional-buffer-acknowledgement | pass | 249,923 | 85.2 | 7.2 | 4 |

`fail` means the independent verifier rejected completed agent work. `infra` means no complete behavioral verdict; it is not scored as a model error. No attempt was retried.

## Evidence audit

All 25 native trial results were processed with the existing scorer. Each completed agent stage was inspected with the setup and four-way token reconciliation checks. Usage reconciled for 20 stages; 19 also passed the required MCP-adoption check. Findings:

Seven attempts stopped before agent execution. Their absent rewards, usage, and agent timing are expected consequences of setup rejection, not additional telemetry defects. CLI exit code zero did not override the readiness gate.

| Task | Readiness finding |
| --- | --- |
| alamofire-deferred-validation-audit | 18 partially parsed files |
| excalidraw-render-invalidation-audit | 13 excluded files, truncated evidence including declaration source |
| jellyfin-playback-negotiation-audit | 1 partially parsed file |
| leveldb-read-cache-audit | 29 partially parsed files |
| leveldb-write-path-audit | 29 partially parsed files |
| sphinx-extension-event-routing | 7 partially parsed files |
| sphinx-prolog-document-titles | 7 partially parsed files |

**NestJS adoption miss:** no MCP calls were observed. The original tool-arm check rejects it. Running the same checker’s no-call branch separately reconciled all four usage sources and confirmed zero calls; this does not relabel the trial as baseline or make its treatment adoption valid.

The full-suite composite remains unavailable when any attempt has invalid evidence. Do not substitute zero for an unsupported integration or average only successful tasks and call that the full-suite result.

## What the traces show

These are selected qualitative reviews, separate from the metadata audit of every
completed trial. They demonstrate why correctness, MCP transport, and useful assistance
must be reported separately.

| Task | Observed workflow | Interpretation |
| --- | --- | --- |
| Download filename encoding | Graph search found `attachment_header`; `get_code_snippet` returned its source. The agent edited it, ran local checks, and passed the independent verifier. | Substantive source retrieval, followed by independently verified repair. One pass does not establish causal benefit. |
| Notification API compatibility | Snippet retrieval and inbound tracing identified the scheduler, alerts, and digest callers. The independent verifier passed. | Task-relevant caller retrieval. The tool's coverage response itself described its signal as best effort. |
| Django utility fan-in | `list_projects` and an architecture overview succeeded. The agent calculated the ranking through shell Python AST traversal. The verifier independently checked 250 call expressions and source immutability. | Orientation-only MCP assistance; this pass is not evidence that graph traversal produced the ranking. |
| Django query execution map | MCP search for scenario labels returned no matches; the agent continued with source/runtime shell tracing. The verifier rejected `ValuesListIterable.__iter__` instead of `FlatValuesListIterable.__iter__`, and compiler-selector line 294 instead of 296. | Valid transport with unhelpful retrieval, followed by candidate error. Valid JSON and correct SQL counts did not satisfy the full contract. |
| Django lookup hierarchy | The inheritance query returned descendants including `KeyTransformExact`. The final artifact listed 49 classes; the verifier required 66 and identified 17 omitted JSON-field subclasses. Source was unchanged. | A populated graph and some relevant returned evidence did not yield an exhaustive candidate inventory. |
| NestJS HTTP lifecycle | Setup/index readiness passed, but the native stream contained no MCP calls. Shell-only work produced the wrong POST default status (200 instead of 201) and reversed exception-filter scope order. No verifier errors or source changes occurred. | Behavioral failure plus an adoption miss. Usage reconciliation passes; this is not a successful MCP measurement, and the trace does not establish why the tool was unused. |
| Cross-session framework reuse | Both stages retrieved framework snippets through MCP, and both passed. Fresh native sessions and an index rebuild after the workspace reset passed the boundary audit. | Lifecycle validation and repeated source retrieval; the observed MCP calls do not demonstrate retained-memory retrieval. |

A separate verifier/artifact review of the HMAC inventory found seven failing entrypoint checks: missing required path hops and an unsupported edge to `TimestampSigner.unsign_object`. The source remained unchanged. The declared three direct callers and 22 entrypoints were not enough to establish that their paths were correct.

The setup failures also carry useful evidence. A nonempty graph and CLI exit code zero
were insufficient: the readiness gate inspected exclusion and parsing metadata and
stopped degraded integrations before spending model tokens. This is evidence that the
failure gate operated, not evidence that the tool supports those repositories.

## Engineering interpretation

The campaign exercises a frozen workload, pinned runtime/tool versions, independently
validated reference and negative controls, fresh trial state, reset-aware multi-stage
execution, hidden behavioral verification, and reconcilable usage accounting. Incorrect
answers remain incorrect; unsupported integrations remain unscored. No result was repaired
by changing a task, loosening readiness, or selectively repeating an attempt.

The pinned fast-mode integration is not ready to claim complete support for this 25-task
suite. Its parsing/exclusion limitations require a separate future compatibility change
and new campaign; this run remains the original record. The repository can be reviewed
as an eval-engineering portfolio with those limits visible.

The earlier baseline completed before the scope amendment: 14 passed and 11 failed,
with no infrastructure or telemetry failures. It is retained as historical context;
this report does not rank the arms or estimate tool benefit. CodeGraph's first trial was
cancelled, with incomplete job finalization preserved. GitNexus and Graphify were not run.

## Reproduction and evidence

Run revision: `352498a83b535de4f19387e14886695a05f5009d`; task tree: `1235fb6303aa596895a651c2db11f50b9710fa6c`. Harbor 0.23.0, Codex 0.144.3, codebase-memory-mcp v0.10.8 fast mode, Linux ARM64 Docker, 1 CPU / 4 GiB, fresh trial state, serial execution, reset-aware indexing, and one fresh session per stage. Adoption is prompted by the shared instruction; it is not natural tool-choice behavior.

```sh
# Run from a separate checkout of the run revision above.
campaign_job=your-unique-codebase-memory-n1-job
PYTHONPATH=. CODEX_FORCE_AUTH_JSON=1 uv run harbor run \
  -c overlays/smoke.yaml -p evals --ek arm=codebase-memory-mcp \
  --plugin overlays.environment:StepIndexPlugin \
  --extra-instruction-path overlays/smoke-instruction.md \
  --mcp-config overlays/codebase-memory-mcp.mcp.json \
  -k 1 -n 1 -r 0 --jobs-dir "$PWD/evals/jobs" \
  --job-name "$campaign_job"

uv run python scripts/score_job.py "$PWD/evals/jobs/$campaign_job"
uv run python scripts/check_overlay_job.py "$PWD/evals/jobs/$campaign_job"
```

The full-job checks intentionally reject incomplete coverage/evidence. Per-trial inspection retains the valid observations and the failures. Native Harbor/ATIF/Codex traces remain local and Git-ignored; they are not bundled in the source release. A compact [machine-readable evidence summary](campaign-n1-data.json) includes per-stage metrics, BuildKit image-manifest digests tied to trial labels and the frozen revision, and SHA-256 hashes of the local evidence used. Hashes identify artifacts; they do not let a reader independently inspect unpublished traces.

To inspect valid trials even when the full-job gate rejects unsupported setups, use the
same audit functions per trial (after the job finishes):

```sh
uv run python - <<'PY'
import json
from pathlib import Path
import sys
sys.path.insert(0, 'scripts')
from check_overlay_job import check_setup, check_agent
job = Path('evals/jobs/suite25-n1-20260925-codebase-memory-mcp')
for path in sorted(job.glob('*/result.json')):
    result = json.loads(path.read_text())
    try:
        setup = check_setup(path.parent, result)
        for stage in result.get('step_results') or [result]:
            directory = path.parent
            if result.get('step_results'):
                directory = directory / 'steps' / stage['step_name']
            print(path.parent.name, check_agent(directory, stage, setup['arm']))
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(path.parent.name, 'REJECTED:', error)
PY
```

For the NestJS accounting-only check, use `check_agent(directory, stage, "baseline")`; the original codebase-memory-mcp adoption failure remains in the evidence summary.

## Limits

One repetition cannot estimate variance or establish a winner. Public upstream code and historical fixes may be familiar to the model. Static audit tasks enforce bounded answer contracts and sometimes exact source locations; they do not establish production application correctness. Tool transport success alone is not semantic usefulness. No task, integration, model setting, or scoring rule was changed during this run. Base-image digests and dependency locks are pinned, but Debian provisioning and the hosted model are not hermetic. Build records identify task images before runtime overlay installation; resolved runtime package inventories are retained in local setup logs.
