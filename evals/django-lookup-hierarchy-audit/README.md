# Django lookup hierarchy audit

A read-only API-migration review across the complete frozen Django Python source.
Find all 66 strict core Lookup descendants, preserve each class's ordered direct
bases, and identify the effective owners of two extension hooks. Multiple
inheritance, mixins, inherited methods, unregistered classes, similarly named
transforms, and out-of-scope contrib classes distinguish this from text search.

## Motivation

[codebase-memory-mcp's benchmark](https://github.com/DeusData/codebase-memory-mcp/blob/main/docs/BENCHMARK.md)
includes inheritance analysis (Q11), including Django. Its
[paper](https://arxiv.org/abs/2603.27277) describes structural retrieval advantages
and accuracy limits. This task tests that capability with exact source/runtime
truth, rather than accepting a tool's own graph as the answer. It does not assume
an MCP wins and does not require tool use.

## Contract and verification

The task uses only native Harbor files. No overlay, model, runner, or scoring
change is needed. All inspected source is within `/app/src`, indexed by every
frozen overlay. The hidden verifier checks source integrity, imports a clean copy
of the pinned source without agent-created bytecode, enumerates class definitions
in every scoped module, and uses Python's actual MRO and source declarations to
derive the inventory. The oracle JSON is a witness, not a grading input.

Complete and correct work earns 1; missing, malformed, incomplete, or incorrect
work earns 0. Infrastructure/evidence failures emit no reward. The existing
host-side scorer separately applies the correctness-first efficiency formula.
The mutation fixture assigns a plausible but wrong inherited method owner.

## Run

```bash
uv run harbor run -p evals/django-lookup-hierarchy-audit -a oracle
CODEX_FORCE_AUTH_JSON=1 uv run harbor run -c overlays/baseline.yaml -p evals/django-lookup-hierarchy-audit
```

## Provenance and limits

`environment/SOURCES.json` records exact upstream archives, hashes, licenses,
and the Python-only selection. Django is pinned at
`9ffd4eae2ce7a7100c98f681e2b6ab818df384a4` (863 Python files; 146,717 lines).
All imported source bytes and empty files are preserved. Source is public and
may appear in model training data. This is a structural audit, not a behavioral
proof that a proposed API change is compatible. Runtime introspection is a valid
baseline strategy; graph access is optional. Building requires network access;
solving and verification require none.

## Local exploratory comparison — 2026-09-25

Three fresh trials per arm, Codex 0.144.3 / `openai/gpt-5.6-luna`, low reasoning,
using the unchanged locked overlays and shared adoption instruction. All 15 trials
finished without infrastructure errors. Values are means across **all** trials,
including failed work and non-adoption; tokens include cached input once.

| Arm | Correct | Trials using MCP | Tokens | Agent seconds | Index seconds | Derived reward |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 3/3 | 0/3 | 225,931 | 92.186 | 0.331 | 0.88943 |
| CodeGraph | 2/3 | 1/3 | 125,811 | 63.902 | 3.364 | 0.60250 |
| GitNexus | 2/3 | 0/3 | 208,494 | 92.000 | 17.507 | 0.59479 |
| Graphify | 3/3 | 0/3 | 139,614 | 63.755 | 11.032 | 0.90742 |
| codebase-memory-mcp | 3/3 | 1/3 | 167,453 | 89.958 | 12.287 | 0.89844 |

**No demonstrated arm-level MCP advantage.** Graphify never used the MCP.
codebase-memory-mcp's MCP-using trial took 293,693 tokens and 98.085 seconds;
its better mean came from no-call trials. Its lookup search did not actually
filter to classes, and the agent finished using a separate source-analysis script.
CodeGraph's one MCP-using success took 193,264 tokens and 71.425 seconds and returned
useful lookup source, but its arm's completion rate was below baseline. Its failed,
no-call trial omitted 17 JSON lookup descendants. GitNexus's no-call failure used
module-prefixed class identifiers and omitted method suffixes from the required
owner identifiers. These are task/adoption outcomes, not connection failures.

Index construction preceded the agent in every trial. Harbor, ATIF, native
cumulative usage, and the completed-turn usage reconciled. Index time is reported
separately and excluded from the agent-time score. Model trials were serialized,
but local authoring/control checks overlapped parts of this exploratory campaign;
these are not isolated performance-confirmation measurements or significant
population estimates.

Raw local jobs: `evals/jobs/overnight-django-lookup-hierarchy-audit-<arm>-n3-v1/`.
Each retains verifier evidence, output artifacts, ATIF, native sessions, and setup
phase logs. Raw jobs are not automatically published with the dataset.
