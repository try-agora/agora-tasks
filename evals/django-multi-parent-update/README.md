# Correct Django updates across multiple parent tables

A real-repository root-cause repair, adapted from the earlier
`agora-bench/evals/swb2-django-15563` case. The agent receives **863 upstream
Python files / 146,717 lines** rather than a reduced imitation of the ORM.
The task exercises the interaction between queryset updates, SQL compilation,
inherited model metadata, and follow-up updates of related tables.

## Run

From the dataset repository root:

```sh
uv run harbor run -p evals/django-multi-parent-update -a oracle --env docker --jobs-dir evals/jobs
CODEX_FORCE_AUTH_JSON=1 uv run harbor run -c overlays/baseline.yaml -p evals/django-multi-parent-update
```

The first command is a credential-free reference check; the second needs the
agent's normal authentication. Tool selection remains entirely outside the task,
through the repository's existing [overlays](../../overlays/README.md).
This directory can also be copied and run independently of this dataset.

## What is harder

The symptom crosses public ORM methods, model inheritance metadata, and the
database compiler. Independently allocated parent keys make a superficially
successful update corrupt an unrelated record. Deeper inheritance and a child
with its own primary key distinguish the shared repair from an immediate-parent
special case. A public SQLite reproduction is available to every arm.

The hidden verifier checks 15 database behaviors: independently keyed parents,
filtered and multi-table updates, expressions, deeper branches, independent child
keys, string parent keys, empty results, preserved ordinary updates, rollback,
and set-based execution. It never compares patches or requires an MCP call.
The query-count check enforces the requested bulk behavior, not model/tool
efficiency. Agent tokens and latency continue to use the unchanged host scorer.

`tests/mutation.json` contains an incomplete repair that checks only the first
inheritance hop. It repairs the simple reproduction but fails a deeper branch.
The existing `scripts/check.py` exercises untouched, reference, and mutated source
without downloading dependencies or calling a model.

## Native Harbor contract

```text
django-multi-parent-update/
├── instruction.md
├── task.toml
├── environment/
│   ├── Dockerfile
│   ├── SOURCES.json
│   └── workspace/          # upstream source, local dependencies, public repro
├── solution/
│   ├── solve.sh
│   └── src/                # reference repair; never in the task image
└── tests/
    ├── test.sh
    ├── test_behavior.py
    └── mutation.json
```

There is no custom agent, environment adapter, metric, manifest format, or
tool-specific task code. Harbor starts the pinned Python image; the agent edits
`/app/src/django`; `tests/test.sh` writes the ordinary binary
`/logs/verifier/reward.txt` plus `checks.json` and `checks.log`. All checks must
pass. The environment and verifier have no network access during execution;
SQLite uses a fresh in-memory database. Only the image's OS packages require
build-time network access. MCP installation and indexing remain overlay setup,
outside the measured agent phase.

## Provenance and scope

- Source: [Django](https://github.com/django/django/tree/9ffd4eae2ce7a7100c98f681e2b6ab818df384a4),
  pinned at `9ffd4eae2ce7a7100c98f681e2b6ab818df384a4`.
- Historical case: [Django PR #15563](https://github.com/django/django/pull/15563),
  also known as SWE-bench instance `django__django-15563`.
- Reference: the two library files changed by upstream commit
  `0b31e024873681e187b574fe1c4afe5e48aeeecf` (Simon Charette / Django contributors).
- Contents: the entire `django/**/*.py` library tree at the base commit, with
  exact source bytes. Non-Python resources, translations, upstream test suites,
  docs, repository history, and the future fix are excluded from the workspace.
  This is an ORM-capable source fixture, not a complete Django distribution.
- Runtime support: task-local asgiref 3.8.1 and sqlparse 0.5.3 Python sources.
  All three components retain their BSD-3-Clause license notices. Archive URLs,
  hashes, and the selection rule are recorded in `environment/SOURCES.json`.
- Grading: independent SQLite behavior/regression checks informed by the upstream
  issue. This is **not the official SWE-bench harness or an official SWE-bench
  score**. Unlike the older task's patch-export signal, Harbor's reward here
  grades execution directly.

## Benchmark interpretation

This case was selected before measuring the new arms because it contains a
real cross-module dependency problem at a substantially larger source scale.
The hypothesis is that indexed navigation can reduce investigation effort;
neither the task nor verifier guarantees an MCP win. Baseline retains the same
source, reproduction, shell, and tests. Do not select or drop this case based on
which arm wins. Report baseline and every configured MCP, including losses and
infrastructure failures, with repeated trials before drawing ranking conclusions.

This is a public 2022 issue: a model may already know the repair. Fresh behavioral
cases strengthen regression coverage but do not remove that contamination risk.
Treat it as a historical large-source repair stratum, not clean evidence of
unseen-code understanding or durable memory. Cold index time, agent time,
correctness, and tokens answer different questions and must remain distinguishable.
