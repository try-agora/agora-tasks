# Django upsert column mapping

A real ORM repair spanning public field-name validation, insert-query state,
SQL compilation, and backend conflict handling. The source contains the original
custom-column bug: inserts use physical columns while upsert clauses receive
model field names. The agent must preserve both new and existing records.

## Source and hypothesis

This is an adaptation of [Django issue 34171 / PR 16315](https://github.com/django/django/pull/16315),
also studied as `django__django-16315` in the earlier SWE-bench research. It uses
the earlier frozen Django commit `9ffd4eae2ce7a7100c98f681e2b6ab818df384a4`, where
the same defect is present, rather than claiming to reproduce the exact SWE-bench
instance. The oracle adapts the upstream field-resolution/compiler repair.

[CodeGraph](https://github.com/colbymchenry/codegraph) and
[GitNexus](https://github.com/abhigyanpatwari/GitNexus) advertise cross-module
navigation and impact analysis. This task measures that hypothesis on observable
database behavior, without requiring an MCP or rewarding tool use.

## Verification

Twelve independent SQLite checks cover mixed insert/update batches, compound
targets, custom primary keys and `pk`, foreign-key targets and updates, reserved
column names, rollback, bound hostile-looking data, bulk query count, empty work,
ordinary/ignored inserts, validation, and default field names. No patch-similarity
check is used. A deliberately partial fix maps update columns but leaves conflict
targets wrong; it must fail. Task reward is binary correctness; the existing
host-side scorer handles tokens and latency separately.

Native Harbor layout, frozen tool-independent environment, no production access.
All source, including the public reproduction, is in `/app/src`. Source archive
URLs, hashes, selection rules, and licenses are in `environment/SOURCES.json`.
The full Python-source fixture contains 863 Django files, plus pinned local
runtime dependencies. It does not include upstream tests or distribution assets.

```bash
uv run harbor run -p evals/django-upsert-column-mapping -a oracle
CODEX_FORCE_AUTH_JSON=1 uv run harbor run -c overlays/baseline.yaml -p evals/django-upsert-column-mapping
```

This is not a PostgreSQL/MySQL integration benchmark. SQLite exercises the shared
ORM route and concrete SQL behavior; backend-specific differences outside this
contract remain untested. Public source may be present in model training data.

## Exploratory comparison — 2026-09-25

Three fresh trials per frozen overlay, `openai/gpt-5.6-luna` at low effort.
These are selection pilots, not independent confirmation or a leaderboard.
Native Oracle passed and no-op failed before model trials.

| Arm | Correct / 3 | MCP-call trials / 3 | Mean total tokens | Mean agent seconds | Mean index seconds | Mean combined reward |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 0 | 0 | 282,793 | 62.34 | 0.38 | 0 |
| CodeGraph | 2 | 2 | 399,384 | 66.58 | 3.53 | 0.59347 |
| GitNexus | 0 | 2 | 307,701 | 65.63 | 17.80 | 0 |
| Graphify | 1 | 3 | 364,378 | 62.43 | 11.45 | 0.29563 |
| codebase-memory-mcp | 0 | 3 | 429,542 | 79.90 | 11.32 | 0 |

CodeGraph's successful `__UNscBfr` trial made four exploration calls returning
the public API, compiler, conflict-operation implementations, and insert-query
relationships. Its other successful trial (`__WWsp5eS`) made no MCP calls and
is **not evidence of MCP benefit**. The failed CodeGraph trial did use relevant
source. Graphify's three trials used source-graph queries; only `__2WDXb9j`
passed. GitNexus had one useful coding query, one discovery-only trial, and one
no-call trial. All codebase-memory-mcp trials retrieved relevant source; two also
made invalid `search_code` calls (`pattern` missing), not connection failures.

The recurring failed requirement was the explicit `pk` alias with a custom
physical primary-key column. One GitNexus patch also regressed ordinary/ignored
inserts. All 15 trials completed without infrastructure exceptions. Native
cumulative usage, Codex turn usage, Harbor results, and ATIF totals reconcile;
indexing finished before agent timing. Total tokens include cached input once.
These pilots ran serially, but local task authoring/reference checks overlapped
some runs, so their timings remain exploratory. Five new alternating CodeGraph/
baseline pairs were queued separately, without changing the task or runtime.

Raw local evidence is retained under
`evals/jobs/overnight-django-upsert-column-mapping-<arm>-n3-v1/`, including
`result.json`, verifier output, native sessions, ATIF trajectories, and setup
logs. Raw sessions are ignored by Git and are not publication-ready artifacts.

## Independent confirmation — 2026-09-25

Five new alternating pairs, with no task, model, overlay, or prompt changes.
These results are separate from the selection pilots above.

| Arm | Correct / 5 | MCP-call trials / 5 | Mean total tokens | Mean agent seconds | Mean combined reward |
| --- | ---: | ---: | ---: | ---: | ---: |
| Baseline | 2 | 0 | 290,758 | 69.33 | 0.35455 |
| CodeGraph | 2 | 4 | 512,629 | 85.59 | 0.35154 |

**The pilot advantage did not replicate.** Correctness tied and baseline was
more efficient. Both CodeGraph passes (`__LGuudCX`, `__FKnPDWE`) used relevant
API/compiler/backend evidence. One failed trial (`__dKt9T3a`) received the
batching helper, then unrelated compiler sections despite naming insert symbols;
another (`__XprPgGt`) received relevant source but still missed the `pk` alias.
The remaining failure (`__sfrohBU`) made no MCP calls. All three baseline
failures also missed `pk`. The saved successful patches are genuine source
repairs, not verifier modifications; non-SQLite backend behavior remains outside
the executed contract.

All ten attempts finished without infrastructure exceptions. Setup boundaries
and native/Codex/Harbor/ATIF token totals reconcile. Raw jobs are
`evals/jobs/confirm-upsert-r<1..5>-<baseline|codegraph>-v1/`. No selective reruns,
pilot pooling, or benchmark-win claim is made.
