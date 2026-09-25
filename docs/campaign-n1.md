# Campaign record and next protocol

## Completed pilot

| Setting | Observed run |
| --- | --- |
| Scope | codebase-memory-mcp, 25 tasks / 27 stages |
| Repetitions | n=1 per task |
| Model | Luna, low reasoning; Codex 0.144.3; Harbor 0.23.0 |
| Controls | Frozen task revision, shared instructions, fresh sessions, serial execution, no retries |
| Outcome | 14 pass, 4 fail, 7 setup rejections |

The baseline completed before scope narrowed. CodeGraph was cancelled after its first task; GitNexus and Graphify were not run. See the [pilot report](campaign-n1-report.md) and [machine-readable data](campaign-n1-data.json).

## Next comparison

- Run codebase-memory-mcp only, on the same frozen 25-task suite.
- Use **n=3 independent attempts per task**, fresh sessions, serial execution, no retries.
- Report per-task pass rate over valid verdicts; average tokens and agent time over valid attempts, with denominators.
- Preserve setup, correctness, and adoption failures; do not impute missing values or combine the earlier baseline.
