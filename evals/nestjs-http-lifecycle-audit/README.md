# NestJS HTTP lifecycle audit

A policy-migration review across route discovery, registration, request-scoped
controllers, guards, interceptors, parameter pipes, Express response adaptation,
and exception filters. The artifact requires 17 exact source locations across
13 files and 12 integration decisions. Similar RPC and WebSocket implementations
remain in the full package snapshot, making transport disambiguation meaningful.

## Motivation

[CodeGraph's cross-language benchmark](https://github.com/colbymchenry/codegraph/blob/main/docs/benchmarks/codegraph-ab-matrix.md)
reports navigation benefits on route-to-handler framework questions, including
Nest-based applications. [Codebase Memory MCP's language benchmark](https://github.com/DeusData/codebase-memory-mcp/blob/main/docs/BENCHMARK.md)
includes Nest source for discovery, call tracing, and inheritance. This is a
separate, more explicit source-evidence task, not a reproduction of either
vendor's exact question, model, scoring, or claimed outcome.

## Contract and verification

The prompt defines the HTTP/Express scope and each required boundary, expression,
and decision. The hidden verifier checks a digest of every protected file and
then validates manually traced call-site witnesses against those exact bytes.
The reference artifact is separate from the grader's evidence. All locations
and decisions must be correct; a plausible mutation reverses custom-filter
scope precedence. No graph provider, runtime tool, or provider-specific output
is part of the contract. Baseline shell scripts are allowed.

This is a bounded **source audit**, not an executed HTTP integration suite or a
general-purpose TypeScript analyzer. Exact source lines are appropriate because
the snapshot is immutable and the task explicitly asks for review locations.
Malformed/missing answers or modified source fail; invalid grader evidence is
an infrastructure error. Token/latency accounting uses the existing scorer.

```bash
uv run harbor run -p evals/nestjs-http-lifecycle-audit -a oracle
CODEX_FORCE_AUTH_JSON=1 uv run harbor run -c overlays/baseline.yaml -p evals/nestjs-http-lifecycle-audit
```

## Provenance

Nest `v10.4.15`, commit `d0fb875e23e3e6baae8537efd41d54709acade0c`, MIT.
The 619-file snapshot includes all package source, excluding upstream tests,
plus license and root package/TypeScript configuration. Exact selection and
digest are in `environment/SOURCES.json`; imported bytes are unmodified.
No npm install is needed. Public-source training contamination is possible.

Before any model pilot, the prompt was refined to name both navigation endpoints
for every arm. This tests an explicit execution-path question rather than hiding
the entry point; source, answers, and grading were unchanged.

## Observed setup limitation — 2026-09-25

All three codebase-memory-mcp pilot attempts stopped before agent execution.
The index reported `indexed`, 4,033 nodes, 13,400 edges, and zero partial parses.
The frozen readiness check rejected `not_indexed_files_count: 1` because the
indexer deliberately skipped `LICENSE`. Its exclusion report also names three
external-interface directories. This is a harness/readiness limitation, not
three incorrect answers or evidence about the agent's navigation accuracy.
The license and overlay checks were not removed or modified to bypass it.

Initialization records are retained under
`evals/jobs/overnight-nestjs-http-lifecycle-audit-codebase-memory-mcp-n3-v1/`.

## Exploratory comparison — 2026-09-25

Three attempts per frozen overlay, `openai/gpt-5.6-luna` at low effort. Native
Oracle passed and no-op failed before model trials. This pilot shows a correctness
floor for the measured configuration, **not an MCP win**: no agent completed the
entire audit. The reference solution and source witnesses still pass unchanged.

| Arm | Correct / valid | MCP-call trials | Mean total tokens | Mean agent seconds | Mean index seconds | Mean combined reward |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 0 / 3 | 0 / 3 | 323,754 | 69.67 | 0.20 | 0 |
| CodeGraph | 0 / 3 | 2 / 3 | 445,254 | 72.58 | 1.85 | 0 |
| GitNexus | 0 / 3 | 3 / 3 | 493,049 | 83.35 | 8.73 | 0 |
| Graphify | 0 / 3 | 2 / 3 | 367,426 | 69.68 | 4.39 | 0 |
| codebase-memory-mcp | 0 / 0 | No agent ran | — | — | Not ready | Unscored |

All twelve completed agent trials reconcile native cumulative usage, Codex turn
usage, Harbor results, and ATIF totals. Indexing preceded agent timing. Tokens
include cached input once. These are exploratory timings: some local task
authoring/reference validation overlapped the pilot. Failed work receives zero
combined reward regardless of apparent efficiency; setup failures are separate.

Nine answers incorrectly gave POST's default status as 200 instead of 201, and
ten incorrectly used global-first custom-filter precedence. The pinned source
explicitly returns `HttpStatus.CREATED` for POST and reverses the context-created
filter list before first-match dispatch. Other errors confused declaration or
adjacent lines with the requested call expression, the HTTP and external
exception paths, or generic metadata copying with route-path discovery.

CodeGraph's two tool-using trials retrieved real HTTP routing, guard, and/or
exception-filter source; one even received the filter reversal expression.
Neither translated that evidence into a fully correct answer. Graphify's two
BFS queries returned relevant HTTP nodes, but only 158/1,013 and 161/1,028 nodes
fit the requested output budget; both agents then used shell source inspection.

GitNexus `__c3PApSL` retrieved the named routing/adapter definitions after an
invalid context call. `__enp764r` only made a trace call that could not resolve
`ExpressAdapter.reply`; `__VUAbAzU` only made a context call lacking `name`/`uid`.
Those two trials did not receive useful MCP evidence. Their error JSON arrived
inside completed tool results, so transport-completion counts alone would miss
the failures. No task or runtime was changed to make this cohort pass, and no
confirmation cohort was selected from it.

Raw native sessions, ATIF traces, artifacts, verifier output, and setup logs are
retained locally under `evals/jobs/overnight-nestjs-http-lifecycle-audit-<arm>-n3-v1/`.
