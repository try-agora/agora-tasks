# Release validation

This release contains 25 tasks and 27 stages. Acceptance concerns task solvability,
verifier discrimination, isolation, and reproducible execution, independent of model scores.

## Checks

```sh
uv sync --locked
uv run python scripts/check.py
uv run python -m unittest discover -s scripts -p 'test_*.py'
uv run harbor run -p evals -a oracle --env docker --jobs-dir evals/jobs --job-name oracle
uv run python scripts/check_job.py evals/jobs/oracle --expected 1
uv run harbor run -p evals -a nop --env docker --jobs-dir evals/jobs --job-name nop
uv run python scripts/check_job.py evals/jobs/nop --expected 0
```

The default checker discovers the current task inventory. It requires unique known tasks,
completed job/trial timestamps, no infrastructure exceptions, exact declared step order,
finished step verification, and the expected reward for every stage. An explicit `--count`
allows a smaller historical or single-task control job; it does not claim full-suite coverage.
Repeated model trials use the separate scorer rather than this unique-task control checker.

## Engineering regressions

- A passing Harbor aggregate cannot conceal a missing or failed later step.
- Duplicate task records cannot substitute for missing tasks.
- Incomplete runs and invalid timestamps cannot pass release validation.
- Index failure prevents agent execution and its timer from starting.
- Workspace resets require a fresh step index; repeated steps and cross-trial lookup fail.
- Token accounting reconciles cumulative native usage without double-counting cache.
- Incorrect work scores zero; missing telemetry or infrastructure failures remain unscored.
- Explicitly listed non-code index exclusions are accepted; skipped source, truncated
  exclusion evidence, partial parses, and missing GitNexus FTS still fail readiness.

## Release execution record

Validated on **2026-09-25** from a separate clean Git clone with a newly created
virtual environment and `uv sync --locked`. Runtime: Python 3.12.12, Harbor 0.23.0,
Docker 29.5.2, Linux ARM64 containers on Colima. No model calls or credentials were used.

| Release check | Observed result |
| --- | --- |
| Task contracts, source witnesses, baseline/reference/mutation discrimination | 25 tasks, 27 stages, all 81 scenarios passed |
| Harness regression tests | 13 test methods passed, including negative cases |
| Native Docker Oracle | 25/25 tasks, 27/27 stages earned reward 1; zero infrastructure errors |
| Native Docker no-op | 25/25 tasks, 27/27 stages earned reward 0; zero infrastructure errors |
| Corrected codebase-memory-mcp startup on eShop | Reference passed; 1,582 nodes and 4,122 edges; intentional license exclusion accepted |
| Authored harness/overlay Python lint | Passed with Ruff 0.15.7 |
| Local documentation links and anchors | Passed |
| Git packaging | Frozen source bytes match the clean checkout; jobs, environments, and credentials excluded |

The task tree is Git object `1235fb6303aa596895a651c2db11f50b9710fa6c`.
The code and inventory guard are committed at `b34582c`; subsequent release-record
edits do not alter task or runtime code. Native control jobs are named `release-oracle`,
`release-nop`, and `release-cbm-eshop`. They remain local under the ignored
`build/release-bzwwl57j/repo/evals/jobs/` validation checkout. The table is a release
record, not a bundled raw trace archive; the commands above reproduce these controls.

Two packaging/environment issues were caught during preparation:

- Git's default text normalization changed CRLF upstream package files. Fixture and
  reference trees now preserve exact bytes through `.gitattributes`; the clean-clone
  source-integrity and Sphinx checks passed after this correction.
- The initial macOS temporary checkout was outside Colima's shared paths. Containers
  could run but verifier logs were invisible on the host. That attempt was stopped
  and retained as a host setup failure. The complete accepted runs used a shared
  checkout path and absolute job paths, without changing task contracts.

The original all-tool matrix covered ten synthetic tasks. This release reran the
specific eShop startup regression, not all 125 task/tool combinations. Optional
integration limits, including partial Sphinx parsing and Excalidraw exclusions, are
explicit in the [overlay compatibility record](../overlays/README.md#compatibility-and-readiness).

GitHub Actions runs the local suite and both Docker controls without model credentials.
Hosted CI cannot be verified until the repository is uploaded; local checks do not imply
that GitHub Actions has run. Raw model sessions and credentials are excluded from Git.

The [historical validation record](validation-history.md) preserves earlier diagnostics,
including the root-owned bytecode/reset failure and its regression fix. Historical
model experiments are separate from release acceptance.
