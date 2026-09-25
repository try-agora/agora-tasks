# Reuse normalization knowledge across sessions

Transfer a normalization lesson to a second export field after source reset.

## Run

From the repository root (Docker must be running):

```sh
uv run harbor run -p evals/cross-session-deduplication-reuse -a oracle --env docker --jobs-dir evals/jobs
```

This credential-free command checks the reference solution. See [running an agent](../../docs/running.md)
for model-backed trials and [tool integrations](../../overlays/README.md) for independent tool selection.

## Contract

- **accounts:** Implement dedup_accounts(records: list[dict]) in src/recordkit/by_account.py.
- **emails:** The source workspace has been restored to its original baseline.

Each step starts a fresh agent conversation. Before step two, `/app` is restored from
the original fixture. Source edits and workspace notes disappear; state outside
`/app` survives inside this trial. `/memory` is reserved for optional tool state.
Do not enable trajectory resumption when measuring cross-session reuse.
Both steps always run; each receives a binary score and the trial reports their mean.
This is a re-learning efficiency control: memory is optional, and correctness alone
does not establish retention. The second step remains solvable from its instruction
and the baseline source. Compare no-tool, plain-notes, and memory-tool arms with the
[completion/efficiency score](../../docs/methodology.md#completion-and-efficiency-reward).

## Verification

The verifier executes hidden Python standard-library behavioral tests and writes
`/logs/verifier/reward.txt`, `checks.json`, and `checks.log`.
A completed check suite scores 1 only when all checks pass; incorrect or missing
implementations score 0. Setup failures and verifier crashes produce no score.
The **accounts** mutation check rejects: Unicode-incorrect normalization.
The **emails** mutation check rejects: Repeating the same normalization mistake on a new field.
Public smoke tests, when present, are development aids; editing them cannot change the hidden score.

## Layout

```text
cross-session-deduplication-reuse/
├── README.md
├── task.toml
├── environment/                 # Dockerfile, reset, and frozen source
├── tests/
│   └── helpers.py               # shared behavioral grading/output
└── steps/
    ├── accounts/
    │   ├── instruction.md
    │   ├── tests/               # test.sh, test_behavior.py, mutation.json
    │   └── solution/            # solve.sh and reference source
    └── emails/
        ├── instruction.md
        ├── tests/
        ├── solution/
        └── workdir/
            └── setup.sh        # restore /app before the fresh conversation
```

## Provenance and limits

Adapted from `agora-bench/evals/pilot-rework-floor` at commit
`7c1ba317267adf95dc13e043b73cca5daa43b48d`.
This is a synthetic, reduced fixture with rewritten contracts and stronger verifiers,
not a reproduction of a full upstream repository benchmark or its historical scores.
No task requires Agora or awards points for invoking a particular tool.
Correctness alone does not prove memory was used. Compare tokens, time, and observed tool activity across matched trials; see the methodology.
