# Excalidraw render-invalidation audit

Trace element mutation through a scene observer, a React state update,
renderable-element memoization, a component effect, canvas painting, shape
caching, and animation-frame scheduling. Thirteen symbol locations and
twenty-three decisions separate these mechanisms. All arms receive the same
named endpoints; no tool is required or presumed superior.

## Source and hypothesis

[CodeGraph's dynamic-dispatch study](https://github.com/colbymchenry/codegraph/blob/main/docs/design/dynamic-dispatch-coverage-playbook.md)
specifically describes Excalidraw's scene observer as a graph-navigation use
case. Its [comparison matrix](https://github.com/colbymchenry/codegraph/blob/main/docs/benchmarks/codegraph-ab-matrix.md)
also includes this application. This task tests that advertised mechanism using
new source-backed questions, a frozen release, and the dataset's unchanged cheap
model/runtime. It is not a reproduction of the vendor's model, prompt, revision,
or reported savings.

Excalidraw v0.18.0 is pinned at
`817d8c553c3389650f8b4503984a6d4a5d2f0c11`. Exact source selection, digest, and
retained MIT license are documented in `environment/SOURCES.json`. No browser,
downloaded dependencies, generated graphs, or model-produced expected answers
are needed. Public source may be present in model training data.

The 416-file, 4.78 MB fixture retains selected production source and project
metadata byte-for-byte; it is not a complete browser-build distribution. The
MIT notice remains at `src/excalidraw/LICENSE` inside the environment.

## Verification and limits

The verifier checks protected source bytes and independently authored source
witnesses before comparing the artifact. It does not obtain answers from an
MCP or load the reference artifact as expected output. Answers identify files
and enclosing named symbols, not exact line numbers. Behavioral decisions are
required: merely finding the files is insufficient. A mutation falsely claims
that `informMutation=false` prevents an element version bump.

This is a bounded static audit, not a browser execution or graphics-performance
benchmark. The frame-scheduling scenario explicitly excludes test mode, flush,
cancel, recursion, and additional calls. Missing, malformed, duplicate-key,
oversized, or incorrect artifacts fail; verifier faults emit no agent score.
Native reward is binary correctness. The unchanged host scorer accounts for
tokens and agent latency; initial indexing is reported separately.

```bash
uv run harbor run -p evals/excalidraw-render-invalidation-audit -a oracle
CODEX_FORCE_AUTH_JSON=1 uv run harbor run -c overlays/baseline.yaml -p evals/excalidraw-render-invalidation-audit
```

Native Harbor layout. Task, reference, and verifier are independent of overlays
and of other dataset tasks.

## Comparison protocol — recorded before model trials

After reference/no-op/mutation controls pass, run three fresh trials per frozen
arm: CodeGraph, baseline, GitNexus, Graphify, and codebase-memory-mcp, serially in
that order. These are selection pilots. A candidate needs useful MCP evidence
and a better correctness-gated score than baseline; confirm it separately with
five fresh alternating pairs. Retain all failures, no-call attempts, and setup
errors. Do not pool pilots with confirmation or count discovery-only calls as
coding assistance. This selected small comparison cannot establish a general
tool ranking. No advantage has been established for this task.

## Validation — 2026-09-25

Native Harbor Oracle earned 1 and no-op earned 0 without infrastructure errors
(`excalidraw-render-oracle-v1`, `excalidraw-render-nop-v1`). The full dataset check
passed 78 verifier scenarios across 24 tasks, including the deliberate mutation.
Separate local execution of the pinned `throttleRAF` and scene methods confirmed
the first/third trailing-call sequence, snapshot dispatch, nonce refresh, and
duplicate-listener rejection, using mocked frame scheduling rather than a browser.

## Exploratory comparison — 2026-09-25

Three fresh attempts per frozen arm, using `openai/gpt-5.6-luna` at low effort.
All twelve completed agent trials had matching native, Codex-turn, Harbor, and
ATIF token totals; graph construction finished before the agent timer started.

| Arm | Correct / valid | Useful MCP trials | Mean total tokens | Mean agent seconds | Mean index seconds | Mean combined reward |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 2 / 3 | 0 / 3 | 320,032 | 68.12 | 0.38 | 0.59437 |
| CodeGraph | 2 / 3 | 0 / 3 | 374,893 | 72.65 | 2.69 | 0.58737 |
| GitNexus | 3 / 3 | 1 / 3 | 401,759 | 75.24 | 16.75 | 0.88229 |
| Graphify | 2 / 3 | 2 / 3 | 432,973 | 74.04 | 7.26 | 0.58629 |
| codebase-memory-mcp | 0 / 0 | No agent ran | — | — | Not ready | Unscored |

GitNexus is a **pilot candidate, not a confirmed MCP win**. Its correctness
advantage is one trial, it used more tokens and time on average, and two of its
three passes made no MCP calls. The useful passing trial (`__EBRhP7i`) listed
repositories and queried the rendering path. It received relevant definitions
and locations for `renderStaticScene`, `StaticCanvas`, and `Scene`, mixed with
unrelated paths; it then inspected source using shell commands. The returned
graph did not establish the entire observer-to-render chain. Useful navigation
and a pass occurring together do not establish a causal benefit.

CodeGraph made no MCP calls in any of its three trials. Its failed trial
(`__kdE8Kgz`) named `App.constructor` instead of `App.componentDidMount` for the
observer registration, and misclassified bound-text painting. The baseline
failure (`__pocwd4X`) reversed the React 17/18 throttling answers. No-call results
do not prove deliberate tool avoidance: the saved runtime logs do not expose
when the MCP catalog became available.

Graphify's passing `__n87GBrm` query returned useful mutation/scene locations and
edges among substantial noise. Its other useful-query trial (`__mQqj6Ap`) failed
only on whether a listener added during dispatch runs immediately. Subsequent
shell output included the decisive `Array.from(this.callbacks)` snapshot, but
the answer still treated dispatch as live iteration. Its remaining pass
(`__HoJiKHs`) made no MCP call.

All three codebase-memory-mcp attempts stopped at the unchanged readiness check.
Each reported an indexed graph with 4,485 nodes, 22,264 edges, and zero partial
parses, but 13 intentionally excluded files. Examples include the license and
TypeScript declaration files excluded by the provider's own patterns. The
frozen guard rejected `not_indexed_files_count`. These are setup failures, not
zero-score answers or evidence that the graph cannot support the audit. Readiness
criteria differ across providers; no exclusions or checks were changed to make
this arm pass.

Raw results, submitted artifacts, native sessions, and ATIF traces remain local
under `evals/jobs/overnight-excalidraw-render-invalidation-audit-<arm>-n3-v1/`.
Failures score zero; setup failures remain unscored. This pilot was selected for
fresh confirmation, but **no confirmation trials were started**: the user asked
to stop development after this case. The result must not be presented as an
independently reproduced advantage.
