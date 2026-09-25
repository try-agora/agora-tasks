# Single-pass 25-task campaign: codebase-memory-mcp

Protocol fixed before launch on 2026-09-25. This run checks the full suite and
produces a descriptive engineering report; one observation per task/arm does
not establish statistical superiority.

- Source: release commit `352498a83b535de4f19387e14886695a05f5009d`, isolated checkout.
- Original scope: all 25 tasks / 27 stages, once per arm (125 attempts / 135 stages).
- Original serial order: baseline, CodeGraph, GitNexus, Graphify, codebase-memory-mcp.
- Model/runtime: `openai/gpt-5.6-luna`, low effort, Codex 0.144.3, Harbor 0.23.0.
- Controls: existing locked dependencies and task contracts; shared adoption instruction;
  fresh containers/sessions, reset-aware step indexing; 1 CPU / 4 GiB per trial.
- Budget: one attempt (`-k 1`), one concurrent trial (`-n 1`), no retries (`-r 0`).
  Stop for provider quota/authentication errors instead of repeatedly spending on failures.
- Evidence: native Harbor jobs `evals/jobs/suite25-n1-20260925-<arm>/`;
  raw sessions remain local and Git-ignored.
- Analysis: correctness and coverage first; separately report setup failures, adoption,
  token reconciliation, agent time, indexing/setup time, and the frozen derived score.
  Compare efficiency on matched valid tasks, including failures in completion totals.
  Inspect representative successful/failed tool traces; transport success is not useful use.
- Known unsupported combinations: codebase-memory-mcp's pinned fast mode rejects
  Sphinx partial parses and Excalidraw's source exclusions. Preserve those outcomes;
  do not alter the integration or silently rerun after seeing this campaign.

The user explicitly selected one repetition for this campaign, replacing the
five-repetition recommendation in the general methodology. No winner-selection
reruns, mid-campaign task edits, or extra repetitions are planned.

## Scope amendment

After the baseline completed at 13:50:31 UTC on 2026-09-25, the user narrowed
the campaign to **codebase-memory-mcp only**. The serial runner was stopped;
CodeGraph's first trial was cancelled and its incomplete evidence retained.
GitNexus and Graphify were not launched. This changes scope, not task contracts,
model settings, retry policy, or scoring.

The active deliverable is 25 codebase-memory-mcp attempts (27 planned stages),
with an engineering analysis of correctness, setup coverage, usage accounting,
and actual tool adoption. The completed baseline is retained as prior context;
the cancelled CodeGraph job is excluded from comparative results. No further
other-arm runs are authorized by this campaign's current scope.
