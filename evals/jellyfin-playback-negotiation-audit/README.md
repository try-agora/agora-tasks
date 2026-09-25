# Jellyfin playback negotiation audit

A cross-layer source audit in 1,632 frozen production-source/project files.
Seventeen source locations and fourteen policy decisions connect HTTP handling,
claims, dependency injection, dynamic providers, device adaptation, and the
video-stream builder. No particular MCP, command, or search strategy is required.

## Source and hypothesis

[CodeGraph's published matrix](https://github.com/colbymchenry/codegraph/blob/main/docs/benchmarks/codegraph-ab-matrix.md)
reports its largest navigation-time saving on Jellyfin. This task tests that
large-application navigation hypothesis using new, independently traced questions,
a pinned public release, and the existing Harbor comparison controls. It is not a
reproduction of the vendor's question set, model, revision, or timing result.

The fixture is Jellyfin tag `v10.10.7`, commit
`aefb9b2cffca3ccb7a95d89af0d9fb2040de6ed3`. All selected upstream files are
byte-identical. Exact selection, provenance, and source digest are in
`environment/SOURCES.json`. Upstream Jellyfin material remains under its **GPL
v2 license** and original notices, retained in `src/jellyfin/LICENSE`; the
dataset's root license does not replace those terms. No server binaries or
third-party package contents are bundled. Public source may be in model training.

## Verification

The hidden verifier checks an unchanged source digest and manually traced source
witnesses, then compares the submitted artifact with the source-backed contract.
Its expected witnesses are separate from the reference solution and never come
from an MCP graph. This is a bounded source audit, not a C# execution model or an
integration test of a live Jellyfin server. Missing, malformed, duplicate-key,
oversized, or incorrect artifacts fail; verifier faults do not emit an agent score.

The deliberate mutation treats the later auto-open selection as case-insensitive,
confusing it with the earlier source filter. The original source implements two
different comparisons. Correctness is binary; tokens and agent latency are scored
by the unchanged host-side scorer, with graph construction reported separately.

```bash
uv run harbor run -p evals/jellyfin-playback-negotiation-audit -a oracle
CODEX_FORCE_AUTH_JSON=1 uv run harbor run -c overlays/baseline.yaml -p evals/jellyfin-playback-negotiation-audit
```

Native Harbor files only. The task is independent of the optional overlays.

Before any model pilot, both navigation endpoints were named in the prompt for
every arm, matching the advertised execution-path question shape. Source,
answers, and grading were unchanged.

## Comparison protocol — recorded before model trials

Run three fresh trials for each frozen arm: CodeGraph, baseline, GitNexus,
Graphify, and codebase-memory-mcp, serially in that order. Keep the same cheap
model, low effort, extra instruction, task, and runtime for every arm. These
pilots select candidates, not winners. A candidate needs useful MCP evidence
and a better correctness-gated score than baseline; confirm it separately with
five fresh alternating pairs. Retain failed, no-call, and setup-error attempts.
Do not pool pilot and confirmation results or interpret discovery-only calls
as coding assistance. This small selected comparison cannot establish a general
tool ranking.

## Pilot audit caveat — 2026-09-25

While inspecting the first CodeGraph traces, the `video_candidate` wording was
found to be ambiguous: "constructs one candidate from a media source" can
reasonably mean the `BuildVideoItem` call in `GetOptimalVideoStream` (the current
gold witness) or the `new StreamInfo` allocation inside `BuildVideoItem` (the
submitted answers). A rejection on that key alone is not evidence of faulty
navigation or reasoning. All three CodeGraph attempts also had other mismatches.
The existing v1 cohort remains unchanged and retained; its results are provisional
and cannot support a headline win claim. Clarify/version this contract before
independent confirmation, rather than changing an active experiment's prompt.

## Retained v1 pilot evidence

Jobs: `evals/jobs/overnight-jellyfin-playback-negotiation-audit-<arm>-n3-v1/`.
The twelve agent trials have reconciled Harbor, ATIF, Codex-turn, and native
session usage. Initial graph construction finished before each agent timer.
Numbers below are descriptive only because of the ambiguous contract.

| Arm | Original reward 1 / agent trials | Useful MCP trials | Mean total tokens | Agent seconds | Index seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0/3 | — | 504,061 | 82.43 | 0.54 |
| CodeGraph | 0/3 | 3 | 697,280 | 90.93 | 6.47 |
| GitNexus | 0/3 | 2 | 655,017 | 82.46 | 27.49 |
| Graphify | 0/3 | 0 | 422,093 | 83.18 | 12.56 |

CodeGraph returned useful controller, provider-dispatch, and stream-builder
source, but answers also misidentified enclosing methods or policy behavior.
Two GitNexus queries returned useful definitions despite irrelevant process
headlines. Its third trial (`__KAygbxJ`) supplied a filesystem path as the repo
identifier and received only a repository-not-found error; its sole grading
mismatch was the ambiguous candidate question. This is neither a valid task
failure attribution nor evidence that an MCP helped solve it.

Two Graphify trials passed the source subdirectory as `project_path`, although
the shared runtime instruction explicitly identifies `/app` as the indexed root.
Both calls returned `graph.json not found` inside nominally completed tool
responses; the third trial made no MCP call. None counts as useful MCP evidence.
All three had additional artifact/policy errors. Lower tokens alone are not a win.

Some exploratory Jellyfin timings overlap lightweight fixture/control work for
later tasks. Do not treat these pilot latency differences as causal estimates.

All three codebase-memory-mcp attempts stopped before agent execution at the
unchanged index-readiness guard: one skip-listed license and one partially
parsed C# file (`SubtitleEditParser.cs`, lines 1–139). The index reported 20,455
nodes and 90,923 edges. These are setup errors, not correctness zeros. Other
arms have different readiness criteria, so this is not a fair navigation ranking.
No license was removed and no guard was bypassed to produce a completed run.

## Clarification — version 1.0.1

After every v1 attempt finished, the `video_candidate` row was changed to specify
the selector's call to the candidate builder, not the allocation inside it.
Only that prompt row and the task's metadata version changed; source, expected
answers, reference solution, and verifier are unchanged. For reproducing the
retained v1 cohort, restore the exact old row text: `Video builder constructs one
candidate from a media source.` and metadata version `1.0.0`.

Fresh v2 pilots will use the clarified prompt for all five arms in the same
three-trial order. They must pass reference/no-op/mutation controls first. Do not
rescore or pool the v1 artifacts as v2 results. Neither version has demonstrated
an MCP advantage yet.
