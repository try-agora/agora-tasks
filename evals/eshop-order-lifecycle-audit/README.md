# eShopOnWeb order lifecycle audit

Trace an application lifecycle across checkout, basket/order aggregates, service
interfaces, dependency registration, mediator handlers, specifications, and read
projections. Eighteen source witnesses across thirteen files and fifteen decisions
distinguish saved basket prices from catalog snapshots, list filtering from detail
selection, and explicit application sequencing from assumed database guarantees.

## Source and hypothesis

[CodeGraph's matrix](https://github.com/colbymchenry/codegraph/blob/main/docs/benchmarks/codegraph-ab-matrix.md)
reports navigation savings for its `aspnet-eshop` case; its
[dispatch coverage notes](https://github.com/colbymchenry/codegraph/blob/main/docs/design/dynamic-dispatch-coverage-playbook.md)
identify the application as eShopOnWeb. This task tests the same application/flow
family with newly traced questions, not the vendor's undisclosed prompts or model.
Both baseline and MCP arms receive the same named navigation endpoints.

The [archived reference application](https://github.com/dotnet-architecture/eShopOnWeb)
is pinned at `4da8212117e87d808d4bbc7da6286fd2147ce606`. The 280-file fixture includes
all production C# and Razor source, project files, and root package/solution
metadata. It excludes tests, downloaded dependencies, static third-party assets,
and deployment configuration. MIT license and original source notices are retained.
Nineteen files have only CRLF/final-newline normalization; no source logic changes.
`environment/SOURCES.json` records exact selection and the resulting digest.

## Verification and limits

The hidden standard-library verifier validates source integrity and independently
authored source witnesses, then checks the artifact. It never grades against an
MCP graph or reads the reference artifact as expected output. A mutation adds a
buyer filter to the description of the detail specification, confusing it with
the list specification; it must fail. Missing, malformed, duplicate-key, oversized,
and incorrect artifacts fail. Verifier faults do not produce an agent score.

This is a bounded static audit, not an executed ASP.NET/EF integration test or a
claim about every deployment's authorization/transaction behavior. No service is
started and no live target is tested. Public source may be in model training.
Task reward is binary correctness; the unchanged host scorer accounts for tokens
and agent latency, with graph initialization reported separately.

```bash
uv run harbor run -p evals/eshop-order-lifecycle-audit -a oracle
CODEX_FORCE_AUTH_JSON=1 uv run harbor run -c overlays/baseline.yaml -p evals/eshop-order-lifecycle-audit
```

Native Harbor structure; task, verifier, and reference solution are self-contained
and independent of optional overlays. No external package download is needed to
solve or grade the source audit.

## Comparison protocol — recorded before model trials

Run three fresh trials for each frozen arm: baseline, CodeGraph, GitNexus,
codebase-memory-mcp, and Graphify, serially in that order. Keep the same cheap
model, low effort, extra instruction, task, and runtime for every arm. These
pilots select candidates, not winners. A candidate needs useful MCP evidence
and a better correctness-gated score than baseline; confirm it separately with
five fresh alternating pairs. Retain failed, no-call, and setup-error attempts.
Do not pool pilot and confirmation results or interpret discovery-only calls
as coding assistance. This small selected comparison cannot establish a general
tool ranking.

## Pre-pilot refinement — 2026-09-25

Version 1.1.0 asks for the containing file/member, not exact line numbers. Earlier
audits on other tasks showed that line transcription could dominate otherwise
correct source reasoning. This change was finalized before any model trial on
this task; all arms receive the same contract. Source, policy questions, source
witnesses, binary correctness, and runtime are unchanged. No previous model
results exist for this task to rescore or select from.

The revised contract passed local reference/no-op/mutation checks and native
Harbor Oracle 1 / no-op 0 without infrastructure errors:
`eshop-order-lifecycle-audit-oracle-symbol-v2` and
`eshop-order-lifecycle-audit-nop-symbol-v2`. No model trial had started.

## Observed setup limitation — 2026-09-25

All three codebase-memory-mcp pilot attempts stopped before agent execution at
the frozen readiness guard. The engine reported 1,582 nodes, 4,122 edges, and
zero partially parsed files; the sole rejected item was intentionally skip-listed
`eshop/LICENSE`. These are unscored overlay-setup errors, not failed navigation
attempts or evidence that the engine cannot handle this C# fixture. The license
and guard were retained unchanged. Other arms use different readiness criteria,
so this arm cannot be ranked on task quality from these attempts.

## Exploratory comparison — contract 1.1.0

Three attempts per frozen arm with `openai/gpt-5.6-luna`, low effort. All twelve
completed agent trials reconcile native cumulative usage, Codex-turn usage,
Harbor, and ATIF totals; initial indexing ended before agent execution. The
three setup errors above are retained but unscored. Job suffix `n3-v1` identifies
this first pilot cohort, not the earlier unrun task contract 1.0.0.

| Arm | Correct / valid | MCP-call trials | Mean total tokens | Agent seconds | Index seconds | Mean combined reward |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | 2/3 | 0 | 212,160 | 59.54 | 0.53 | 0.59881 |
| CodeGraph | 1/3 | 2 | 254,737 | 58.43 | 1.07 | 0.29935 |
| GitNexus | 1/3 | 3 | 394,812 | 72.44 | 6.04 | 0.29280 |
| Graphify | 2/3 | 1 | 176,658 | 56.26 | 1.43 | 0.60062 |
| codebase-memory-mcp | 0/0 | No agent ran | — | — | Not ready | Unscored |

All twelve agent trials answered every policy decision correctly. Failures were
source-navigation/identity errors, not evidence that the agents misunderstood
checkout policy. The first baseline also chose a similarly named specification
that is not used by `GetMyOrdersHandler`. Other failures either named the guard's
caller or inferred `GuardExtensions` from its filename instead of reading the
actual declaring class, `BasketGuards`.

CodeGraph's passing `__2PqetWz` trial used three relevant explorations, including
mediator/interface links and the actual `BasketGuards` declaration. Its tool-using
failure retrieved useful application code but not that guard; its other failure
made no MCP call. GitNexus's passing query located relevant application symbols;
one failure used a similar query and the other only retrieved limited checkout
class context. Both failed trials also made invalid context calls. A completed
tool response is therefore not automatically a successful navigation step.

Graphify `__qiXcyu7` passed after one `/app` BFS query returned a noisy 199-node
inventory containing relevant handler, service, and entity locations. It did not
return the guard declaration or the specific customer specification; source
inspection was still necessary. Its other pass and its failure made no MCP call.
Thus the aggregate's small efficiency difference is not established MCP benefit.

Graphify is selected only as a follow-up candidate: it ties correctness, has the
highest pilot combined score, and includes one useful tool-using success. Five
fresh alternating Graphify/baseline pairs were queued after the existing work,
with baseline first in odd pairs and Graphify first in even pairs. No settings or
task content change. Retain all results and do not pool them with this selection
pilot; three attempts and one useful MCP trace cannot establish a reliable win.

Raw local evidence: `evals/jobs/overnight-eshop-order-lifecycle-audit-<arm>-n3-v1/`.
