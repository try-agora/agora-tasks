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

Validation is in progress. Final clean-snapshot checks will be recorded here before release.

GitHub Actions runs the local suite and both Docker controls without model credentials.
Hosted CI cannot be verified until the repository is uploaded; local checks do not imply
that GitHub Actions has run. Raw model sessions and credentials are excluded from Git.

The [historical validation record](validation-history.md) preserves earlier diagnostics,
including the root-owned bytecode/reset failure and its regression fix. Historical
model experiments are separate from release acceptance.
