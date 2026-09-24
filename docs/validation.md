# Validation record

Validated locally on 2026-09-24 with Harbor 0.23.0, Docker 29.5.2, and Linux ARM64
containers on Colima. This is reference-solution and verifier validation, not a
model-performance report.

## Results

| Check | Result |
| --- | --- |
| Native local-dataset discovery | 10 tasks resolved from evals/ |
| Task configuration and structure | 10 task configurations parsed |
| Reference implementations against hidden verifiers | 12/12 stages pass |
| Untouched fixtures against hidden verifiers | 12/12 correctly rejected |
| Plausible wrong implementations against hidden verifiers | 12/12 correctly rejected |
| Harbor/Docker reference solutions | All 10 tasks, including all 12 stages, pass after the correction below |
| False-green job-result regression | Pass |
| Python lint and formatting | Pass |
| Formatting behavior check | Python ASTs unchanged for all 77 task Python files |

The eight single-step tasks passed in the `oracle-validation` job. Both multi-step tasks
passed in the subsequent `oracle-relay-validation` job:

| Multi-step task | First stage | Second stage |
| --- | --- | --- |
| cross-session-framework-reuse | rate-limit: 1 | authenticate: 1 |
| cross-session-deduplication-reuse | accounts: 1 | emails: 1 |

## Failure found and corrected

The first container run exposed a real isolation issue: verification ran Python with
`-I`, which ignores environment flags. It created root-owned bytecode caches inside
the agent-owned source tree. The next session could not remove those caches during reset.
The verifier now uses `python -I -B`, explicitly disabling bytecode writes.
Only the two affected multi-step trials were rerun.

Harbor's aggregate output reported a reward of 1 even though those second-step setups
had failed. The repository's result checker therefore requires every expected stage,
rejects step-level exceptions and missing scores, and checks each stage's reward.
`scripts/test_check_job.py` retains a regression for that false-green summary.

Initial attempts also exposed missing host prerequisites: writable Harbor build cache
and Docker Buildx. Those attempts are infrastructure failures and are excluded from
the passing results.

## Inspect or reproduce

Local run artifacts are retained under `evals/jobs/oracle-validation/` and
`evals/jobs/oracle-relay-validation/`, including the initial failed stages. Jobs are
Git-ignored and are not part of the shareable dataset. The corrected relay evidence can
be checked without launching anything:

```sh
uv run python scripts/check_job.py evals/jobs/oracle-relay-validation --expected 1 --count 2
```

For a future full validation:

```sh
uv run python scripts/check.py
uv run python scripts/test_check_job.py
uv run harbor run -p evals -a oracle --env docker --jobs-dir evals/jobs --job-name oracle
uv run python scripts/check_job.py evals/jobs/oracle --expected 1
```

The CI workflow repeats source checks and Oracle trials, and additionally runs a Harbor
no-op agent. That workflow has been authored but has not run on GitHub; the repository
is local only. No paid model inference, model-backed agent trial, or vendor-tool campaign
was performed. Token savings, comparative tool benefits, and full-repository performance
remain unmeasured.
