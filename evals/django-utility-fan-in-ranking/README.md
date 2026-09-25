# Django utility fan-in ranking

Prioritize ten shared helper functions by distinct-file caller fan-in across the
complete frozen Django Python source. The agent returns a compact ranked artifact,
not a prose survey or an exhaustive transcript. There are 250 explicit call
expressions and 131 helper/file pairs, including module-qualified calls, repeated
calls within a file, and an imported alias with a same-named wrapper nearby.

## Why this task

[Codebase-Memory's paper](https://arxiv.org/abs/2603.27277) specifically identifies
caller ranking and hub detection as graph-native strengths, while disclosing
weaker results on exhaustive line-level questions. This task tests ranking with
source-derived counts and no required tool. It does not treat a provider's degree
count as ground truth or promise that the pinned MCP version will win.

Unlike the HMAC impact task, this task has no transitive paths, dynamic receiver
bindings, or exact call-site output requirement. The question is an aggregate
prioritization across helpers, not one helper's upstream execution paths.

## Verification

The hidden verifier hashes protected source and the public catalog, resolves
imported names/module qualifiers, and performs an independent AST call census.
It checks defining helpers and fails closed on ambiguous bindings or parameter
shadowing. Its resolver is intentionally scoped to this immutable corpus, not a
general-purpose Python analyzer. Each run retains the source call witnesses in
`/logs/verifier/source-call-witnesses.json`; no reference artifact or MCP graph is
used to grade. Repeated sites count once per file. Incidental mentions and bare
callback/decorator references do not count, as the public contract specifies.

The reference solution is a witness. A mutation replaces a distinct-file count
with a larger call-site count and must fail. Complete correctness earns 1;
incorrect or missing work earns 0. Verifier/evidence failures leave no reward.
The frozen host-side scorer measures completion, tokens, and latency separately.

```bash
uv run harbor run -p evals/django-utility-fan-in-ranking -a oracle
CODEX_FORCE_AUTH_JSON=1 uv run harbor run -c overlays/baseline.yaml -p evals/django-utility-fan-in-ranking
```

## Provenance and limits

Native Harbor layout; the unchanged overlays remain independent. All inspected
source is under `/app/src`. The task reuses 863 byte-identical Django Python files
at `9ffd4eae2ce7a7100c98f681e2b6ab818df384a4` and pinned local runtime dependencies;
archive hashes, selection, and licenses are in `environment/SOURCES.json`.
The ranking is over the named helper catalog, not every symbol in Django. It is
source-level fan-in, not runtime traffic or proof of compatibility risk. Public
source may appear in training data, and efficient baseline scripts are allowed.

## Trace finding — GitNexus pilot, 2026-09-25

The first three GitNexus trials produced one pass, which made no MCP calls;
one failure used discovery only; the other failure (`__RHiC9CF`) made ten actual
symbol-context queries. This is not a demonstrated tool advantage.

That last trace contains an inspectable coverage limitation. The context for
`make_aware` returns three caller files, matching the three files with direct
bare-name calls. The independent source witnesses contain twelve additional
files with `timezone.make_aware` calls, for fifteen in total. This indicates a
module-qualified relationship gap in that returned result, not a wrong gold
count inferred from another provider's graph.

Some high-fan-in results also stop at thirty callers. The pinned
[GitNexus v1.6.9 context implementation](https://github.com/abhigyanpatwari/GitNexus/blob/v1.6.9/gitnexus/src/mcp/local/local-backend.ts)
uses `LIMIT 30` for incoming references. A context preview is therefore not an
exhaustive census; raw graph queries or independent source checks are needed.
The agent also received an ambiguous `slugify` result requiring disambiguation.
These observations do not establish whether another query strategy would have
recovered every missing relationship.

Raw evidence: `evals/jobs/overnight-django-utility-fan-in-ranking-gitnexus-n3-v1/`,
especially `agent/codex.txt` and `verifier/source-call-witnesses.json` in
`django-utility-fan-in-ranking__RHiC9CF/`. All three trials retain valid setup and
reconciled native/Harbor/ATIF/turn token totals. Other arms are evaluated separately.

## Complete exploratory pilot — 2026-09-25

Three fresh attempts per frozen arm, `openai/gpt-5.6-luna` at low effort.
All fifteen finished without infrastructure exceptions; setup boundaries and all
four token representations reconcile. Some task authoring/reference checks ran
alongside pilots, so timings are exploratory. No confirmation was selected:
**this cohort does not demonstrate an MCP advantage**.

| Arm | Correct / 3 | MCP-call trials / 3 | Mean total tokens | Mean agent seconds | Mean index seconds | Mean combined reward |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 2 | 0 | 138,269 | 56.00 | 0.61 | 0.60844 |
| CodeGraph | 2 | 2 | 157,995 | 57.10 | 3.80 | 0.60360 |
| GitNexus | 1 | 2 | 188,260 | 61.62 | 18.18 | 0.30151 |
| Graphify | 2 | 1 | 152,942 | 81.70 | 11.14 | 0.60226 |
| codebase-memory-mcp | 0 | 3 | 278,396 | 82.54 | 11.62 | 0 |

CodeGraph's `__L8irPzx` computed the correct ranking but wrote it outside the
required artifact path, a delivery failure. Its tool-using pass (`__uVcxZqw`)
received unrelated URL-resolution code and then used its own source scan; the
other pass made no MCP calls. Neither establishes useful graph assistance.
Both Graphify passes made no MCP call; its failed query returned unrelated helpers
and graph nodes. Baseline used ordinary shell/Python source analysis.

codebase-memory-mcp's first two attempts made wrong-argument or wrong-symbol path
queries after discovery; these were not connection failures. Its third attempt
(`__GMnfggD`) correctly retrieved the catalog's helper symbols, but then used an
incomplete source census and missed same-module calls. A symbol's incoming-edge
count is not automatically the distinct-file count required here. This result
does not show that a correctly constructed graph aggregation would fail.

All raw pilot jobs are retained as
`evals/jobs/overnight-django-utility-fan-in-ranking-<arm>-n3-v1/`, including the
unsuccessful work. No reward, task contract, or provider setting was changed after
seeing these results.
