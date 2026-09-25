# Alamofire deferred-validation audit

Follow a Swift HTTP request across creation, interceptor composition, task
dispatch, completion/metrics coordination, deferred validation, retry, and
response serialization. Eighteen symbol locations and twenty-three decisions
separate request preflight from response validation and closure registration
from execution. No navigation tool is required or presumed superior.

## Source and hypothesis

[CodeGraph's dispatch study](https://github.com/colbymchenry/codegraph/blob/main/docs/design/dynamic-dispatch-coverage-playbook.md)
uses Alamofire's cross-class closure collection as a concrete graph-navigation
example. This task tests that mechanism with new independently traced questions,
the unchanged Harbor runtime, and a pinned public release. It does not reproduce
the vendor's model, prompt, revision, forced-tool setting, or reported savings.

Alamofire 5.10.2 is pinned at `513364f870f6bfc468f9d2ff0a95caccc10044c5`.
The fixture contains every tracked Swift file, including public tests and
examples, plus the MIT license. Selection, transformations, and source digest
are recorded in `environment/SOURCES.json`. Original copyright notices remain
intact; the dataset's license does not replace upstream terms. Public source
may be present in model training data.

All 93 fixture files (1.66 MB) are byte-identical to the pinned checkout.

## Verification and limits

The standard-library verifier checks protected source bytes and independent
source witnesses, then checks the submitted artifact. It does not read an MCP
graph or load the oracle artifact as expected output. Locations identify files
and named members, not line numbers. A mutation incorrectly claims that retry
reset removes the registered validators. Malformed, duplicate-key, oversized,
missing, or incorrect artifacts fail; verifier faults produce no agent score.

This is a bounded static audit, not an executed Swift/URLSession integration
test or live network benchmark. Its macOS and FoundationNetworking questions
explicitly distinguish conditional compilation branches. No compiler, server,
credentials, or external package download is required. Correctness is binary;
the unchanged host scorer handles tokens and agent latency, with indexing
reported separately. Native Harbor layout; task and overlays are independent.

```bash
uv run harbor run -p evals/alamofire-deferred-validation-audit -a oracle
CODEX_FORCE_AUTH_JSON=1 uv run harbor run -c overlays/baseline.yaml -p evals/alamofire-deferred-validation-audit
```

## Comparison protocol — recorded before model trials

After reference/no-op/mutation controls pass, run three fresh trials per frozen
arm: baseline, CodeGraph, GitNexus, Graphify, and codebase-memory-mcp, serially in
that order. Keep model, effort, runtime, and extra instruction unchanged. Pilots
select candidates, not winners. A candidate needs useful MCP evidence and a
better correctness-gated score than baseline; confirm it with five separate
fresh alternating pairs. Retain failures, no-call trials, and setup errors.
Do not pool selection pilots with confirmation or call discovery-only results
coding assistance. No advantage has been established for this task.

## Validation — 2026-09-25

Native Harbor Oracle earned 1 and no-op earned 0 without infrastructure errors
(`alamofire-validation-oracle-v2`, `alamofire-validation-nop-v2`). These refreshed
controls include the strict integer-list check finalized before model trials.
The complete
dataset check passed 81 verifier scenarios across 25 tasks, including this
task's incorrect retry-reset mutation. The task was validated before model runs.
