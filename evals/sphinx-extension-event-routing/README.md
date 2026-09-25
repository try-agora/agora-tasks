# Sphinx extension event routing

Audit the event dispatch registry of a configured framework application. Four
explicit extensions bring transitive extension dependencies; Sphinx also installs
default extensions and environment collectors. The artifact inventories 39
listener registrations across nine events, including an event with no listeners,
same-priority ordering, nested callbacks, and bound collector methods.

## Motivation

[CodeGraph](https://github.com/colbymchenry/codegraph) advertises navigation across
framework dispatch boundaries; [GitNexus](https://github.com/abhigyanpatwari/GitNexus)
advertises dependency and execution-flow analysis. This task tests the registration
side of that claim: source presence does not imply a listener is installed, and a
registered callback can be a no-op for the selected builder. No MCP is required
or presumed superior. Runtime inspection is an equally valid baseline strategy.

## Contract and verification

The public profile fixes builder, configuration, extension order, observation
point, and requested events. The hidden verifier checks all protected bytes,
starts the real pinned Sphinx application from a clean source/dependency copy,
then derives source identities and priority-stable order from the actual event
registry. It does not use a provider graph or the oracle answer as truth.
Agent-created bytecode and shadow modules are excluded from the clean copy.

The reference artifact is a witness. A mutation omits an EPUB callback because
the selected builder is HTML; that is plausible but incorrect because the
callback remains registered. Complete correctness earns 1, incorrect work 0;
evidence/verifier errors leave no reward. The existing efficiency scorer is
unchanged. Native Harbor layout and independent overlays are preserved.

```bash
uv run harbor run -p evals/sphinx-extension-event-routing -a oracle
CODEX_FORCE_AUTH_JSON=1 uv run harbor run -c overlays/baseline.yaml -p evals/sphinx-extension-event-routing
```

## Provenance and limits

Sphinx commit `71db08c05197545944949d5aa76cd340e7143627`, its complete package
resources, and twenty pinned dependencies are self-contained. Exact archives,
wheel hashes, licenses, selection rules, and vendor digest are recorded in
`environment/SOURCES.json`. Optional native accelerators are excluded; both
host and Linux use pure-Python fallbacks. There is no network-dependent mapping
or document build in verification.

This measures registration and ordering for one precise configuration, not the
runtime behavior of every callback or every possible extension. Source is public
and may appear in training data. It is a new framework-registration audit, not a
reworded instance of the separate document-title repair.

## Observed setup limitation — 2026-09-25

All three codebase-memory-mcp pilot attempts stopped before agent execution.
The index reported `indexed`, 6,117 nodes, and 29,565 edges, but the frozen
overlay's readiness check rejected `not_indexed_files_count: 1`: the intentionally
ignored `sphinx/themes/scrolls/artwork/logo.svg`. Seven non-Python template/TeX
files also reported partial parsing. These are unscored setup failures, not
failed answers. Source assets and overlay checks were left unchanged.

The three attempts and their initialization logs remain under
`evals/jobs/overnight-sphinx-extension-event-routing-codebase-memory-mcp-n3-v1/`.

## Exploratory comparison — 2026-09-25

Three attempts per frozen overlay, `openai/gpt-5.6-luna` at low effort. Native
Oracle passed and no-op failed before the model runs. All twelve completed agent
trials reconcile native cumulative usage, Codex turn usage, Harbor results, and
ATIF totals; initial indexing finished before agent timing. The setup failures
above are retained separately, not converted to zero-reward agent attempts.

| Arm | Correct / valid | MCP-call trials | Mean total tokens | Mean agent seconds | Mean index seconds | Mean combined reward |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 3 / 3 | 0 / 3 | 191,668 | 92.08 | 0.95 | 0.89132 |
| CodeGraph | 3 / 3 | 1 / 3 | 210,238 | 97.84 | 2.98 | 0.88900 |
| GitNexus | 1 / 3 | 1 / 3 | 173,801 | 89.30 | 17.68 | 0.29547 |
| Graphify | 3 / 3 | 0 / 3 | 102,292 | 74.64 | 21.27 | 0.91139 |
| codebase-memory-mcp | 0 / 0 | No agent ran | — | — | Not ready | Unscored |

This task does **not demonstrate MCP benefit** in this pilot. All three Graphify
trials used no MCP calls; their faster, cheaper runtime-inspection solutions
cannot be attributed to Graphify. CodeGraph matched baseline correctness with
higher mean tokens and agent time. Only `__MuTtTya` used its MCP: the query
returned relevant HTML, EPUB, autodoc, and Napoleon registration source before
the agent inspected the live registry. That run used 314,438 tokens and 103.29
agent seconds; the other two CodeGraph runs made no MCP calls.

GitNexus's passing `__Z7u7aRn` run queried event registration and retrieved
`EventManager.connect`, `Sphinx.connect`, collector enablement, and autodoc setup.
Its two failures made no MCP calls: one invented `.py` paths for package
`__init__.py` files, and the other misordered the `missing-reference` listeners.
These are source-identity and dispatch-order errors under the explicit contract.
The successful agents used real runtime introspection to finish the inventory;
the task deliberately permits that strategy for every arm.

These are small selection pilots, not a leaderboard or independent confirmation.
No confirmation cohort was selected from this result. Total tokens include
cached input once; failures receive zero combined reward. Raw local sessions,
ATIF traces, verifier evidence, and setup logs remain under
`evals/jobs/overnight-sphinx-extension-event-routing-<arm>-n3-v1/`.
