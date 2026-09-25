# Sphinx prolog document titles

A symptom-led repair across RST preprocessing, role parsing, document titles,
and table-of-contents rendering. A shared substitution prolog splits role-based
headings from their underlines. The task requires a general fix while preserving
metadata, valid field lists, source positions, substitutions, and epilogs.

## Provenance and hypothesis

Uses [Sphinx PR 11445 / issue 11437](https://github.com/sphinx-doc/sphinx/pull/11445)
at the real pre-fix commit `71db08c05197545944949d5aa76cd340e7143627`.
This issue was studied previously as `sphinx-doc__sphinx-11445`; the older
exploratory comparison found lower navigation cost for CodeGraph and GitNexus.
That is a selection hypothesis, not a result for this task, model, or runner.

The full Sphinx package (170 Python files plus JavaScript, templates, translations,
and theme assets) is included. Twenty exactly pinned dependencies are vendored,
with optional native accelerators omitted so both host and Linux container use
the same pure-Python fallbacks. `environment/SOURCES.json` records upstream
commit/archive hash, dependency wheel URLs/hashes, licenses, selection rules, and
a digest of the exact vendored dependency tree. No wheel files, git history,
upstream tests, external services, or solve-time downloads are needed.

## Verification

Six checks exercise multiple roles, multi-word/escaped field names, line-source
preservation, plain headings, no-op behavior, epilogs, and an actual HTML build
of five independent documents. The build checks document titles, navigation
links, metadata, and expanded substitutions. The reference solution uses
Docutils' existing field grammar; equivalent repairs are accepted. A simpler
word-only pattern is a plausible mutation that fixes the visible demo but fails
the valid-field-list regression.

Native Harbor task reward is binary completion. The unchanged host-side scorer
can add correctness-gated token/latency weighting. No overlay or particular
navigation technique is required. Library exceptions during submitted behavior
fail the task; a harness/build failure is not evidence about MCP quality.

```bash
uv run harbor run -p evals/sphinx-prolog-document-titles -a oracle
CODEX_FORCE_AUTH_JSON=1 uv run harbor run -c overlays/baseline.yaml -p evals/sphinx-prolog-document-titles
```

This is a navigation-heavy small repair, not a large patch or the full upstream
SWE-bench test suite. The stricter field-list regression is documented in the
task contract. Public source and the upstream issue may occur in training data.
Task source is entirely under `/app/src`; optional MCP preparation remains in
the independent, frozen overlays.

## Observed setup limitation — 2026-09-25

All three codebase-memory-mcp pilot attempts in
`evals/jobs/overnight-sphinx-prolog-document-titles-codebase-memory-mcp-n3-v1/`
stopped before the agent ran. The index reports `status: indexed`, 6,112 nodes,
and 29,451 edges, but also one intentionally ignored SVG
(`sphinx/themes/scrolls/artwork/logo.svg`) and seven partially parsed non-Python
template/TeX files. The frozen overlay's strict readiness check rejects the
nonzero `not_indexed_files_count` first. These are **unscored setup failures**,
not three failed repairs or evidence that the coding agent cannot solve this task.
The logs are retained; no task assets or overlay checks were removed to bypass it.

## Exploratory comparison — 2026-09-25

Three attempts per frozen overlay, `openai/gpt-5.6-luna` at low effort. Native
Oracle passed and no-op failed before these trials. This is a candidate-selection
pilot, not an independently confirmed performance claim.

| Arm | Correct / valid | MCP-call trials | Mean total tokens | Mean agent seconds | Mean index seconds | Mean combined reward |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 1 / 3 | 0 / 3 | 363,528 | 91.60 | 1.10 | 0.29345 |
| CodeGraph | 0 / 3 | 3 / 3 | 417,294 | 79.72 | 3.07 | 0 |
| GitNexus | 2 / 3 | 3 / 3 | 454,818 | 100.47 | 19.29 | 0.58056 |
| Graphify | 1 / 3 | 2 / 3 | 339,225 | 87.19 | 21.66 | 0.29595 |
| codebase-memory-mcp | 0 / 0 | No agent ran | — | — | Not ready | Unscored |

All twelve completed agent trials reconcile native cumulative usage, Codex turn
usage, Harbor results, and ATIF totals. Successful graph construction preceded
the agent timer. Tokens include cached input once; task failures receive zero
combined reward. Some local reference checks overlapped early pilots, so timings
are exploratory. The three setup failures above remain in the raw evidence.

Trace inspection matters here:

- GitNexus `__6CqSHc9` passed after a query returned the RST parser/decorator and
  related definitions. Its other pass (`__iP4kLwQ`) only discovered the repository,
  made a context call missing a required argument, then requested folder context
  with no relationships. That pass is **not evidence of useful MCP navigation**.
  The failed `__ZHQaG6A` trial did locate `prepend_prolog` and its parser caller.
- CodeGraph's broad queries repeatedly prioritized Python-code parsing or
  Napoleon docstrings over the actual RST prolog implementation. The third trial
  retrieved the I/O module on a follow-up query, but all three repairs failed.
- Graphify's passing `__mGg4Cpb` query included the Sphinx parser amid a large,
  truncated graph traversal with dependency noise. Its other tool-using trial
  found the relevant RST utility module but failed. One failed trial made no MCP call.
- Incorrect patches variously split/repositioned original document content,
  mishandled valid leading fields, lost titles, or lost metadata. The real HTML
  checks and lower-level source-preservation checks cover different regressions.

Five fresh alternating GitNexus/baseline pairs were queued separately with the
same task and runtime. Their results must be reported independently of this
selection cohort. Raw local traces, artifacts, verifier logs, and initialization
records are under
`evals/jobs/overnight-sphinx-prolog-document-titles-<arm>-n3-v1/`.

## Fresh repeated comparison — 2026-09-25

Five separately queued alternating pairs completed on the same frozen task and
runtime, with fresh environments/conversations and no retries. These ten trials
are not pooled with the selection pilot. All ten have reconciled usage, valid
setup boundaries, and no infrastructure errors. No other task builds ran during
this confirmation batch.

| Arm | Correct / 5 | Useful MCP trials | Mean total tokens | Mean agent seconds | Mean index seconds | Mean combined reward |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 1 | — | 308,314 | 93.73 | 1.16 | 0.17841 |
| GitNexus | 2 | 4 | 448,239 | 101.37 | 18.28 | 0.35259 |

This is a **positive held-out observation on correctness-gated reward**, not a
general efficiency win: GitNexus used more tokens and took longer on average.
The sample is very small. Only one pair has differing correctness outcomes, so
the result is not statistically conclusive and does not prove causal MCP benefit.
It does reproduce the pilot's direction without reusing its trials.

| Pair | Baseline | GitNexus |
| --- | --- | --- |
| 1 | Fail: field handling and prolog placement | Pass; useful query and caller context |
| 2 | Pass | Pass; useful parser/prolog source after an invalid context call |
| 3 | Fail: prolog placement | Fail despite useful source locations |
| 4 | Fail: prolog placement | Fail: over-escaped field regex |
| 5 | Fail: over-escaped field regex | Fail; no MCP call |

The two GitNexus successes (`__cQQGQfj`, `__UPviokd`) used returned definitions
for `RSTParser.decorate` / `prepend_prolog`; the first also inspected the graph's
caller relationship. Both repairs were manually inspected and passed all six
checks, including real HTML builds. Later failures show that finding the correct
code did not reliably produce the correct repair. The no-call trial remains in
the arm's aggregate rather than being discarded.

An additional, unscored validity check ran the captured pair-3 baseline patch
through the pinned Docutils parser with `.. role:: agora_probe(emphasis)` in the
prolog and `:agora_probe:` in the heading. The reference repair rendered the role;
the captured patch produced an unknown-role error because it moved the definition
after its use. This confirms a behavioral consequence of the placement regression;
it was not added to the active verifier and did not change any reported score.

Raw local evidence: `evals/jobs/confirm-sphinx-prolog-r<1..5>-<arm>-v1/`, including
native sessions, ATIF trajectories, submitted source, and verifier reports.
