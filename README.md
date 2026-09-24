# Agora Tasks

**A local Harbor dataset of ten tasks for reliable coding and cross-session knowledge reuse.**

Can an agent fix the shared cause of a bug, preserve an API contract, or reuse what it
learned in a previous session? This collection turns those questions into small,
inspectable tasks with frozen source, behavioral verifiers, and runnable reference
solutions.

The task and the tool under test are independent. Run the same task with a bare coding
agent, plain notes, or your own knowledge tool. No Agora installation is required.

**10 tasks · 12 scored stages · deterministic grading · no credentials for validation**

## Start here

```sh
uv sync --locked
uv run python scripts/check.py
uv run harbor run -p evals -a oracle --env docker --jobs-dir evals/jobs
```

Requires Python 3.12 or 3.13, uv, and Docker with Compose and Buildx. The first command installs the pinned
Harbor runtime. The second checks every verifier against a baseline, a correct solution,
and a plausible wrong solution. The third runs the complete local dataset in Docker
using supplied reference solutions, with no model API calls.

`evals/` is the dataset: its ten immediate subdirectories are Harbor tasks.
To select one task, use `-p evals/checkout-discount-once`.
To evaluate an agent, select it with `-a` and its model with `-m`;
see [running the dataset](docs/running.md). Everything stays on your machine unless
you explicitly choose to publish it or use a hosted model/tool.

For a quick code review, start with
[the checkout task](evals/checkout-discount-once/instruction.md),
[its behavioral verifier](evals/checkout-discount-once/tests/test_behavior.py), and
[its reference solution](evals/checkout-discount-once/solution/src/shop/serializer.py).
For the memory boundary, inspect
[cross-session framework reuse](evals/cross-session-framework-reuse/README.md).

## Tasks

| Task | Capability | Failure it distinguishes |
| --- | --- | --- |
| [Per-client rate limiting](evals/middleware-rate-limiting) | Framework extension and state lifetime | Counters reset per request or leak between application instances |
| [Optional authentication](evals/middleware-authentication) | Middleware composition and access checks | Case-sensitive headers, blank credentials, broken anonymous mode |
| [Notification API compatibility](evals/notification-api-compatibility) | Safe shared-API evolution | Existing callers break or valid empty metadata disappears |
| [Stable record deduplication](evals/stable-record-deduplication) | Unicode-aware data transformation | Wrong normalization, reordered data, or mutation of caller-owned records |
| [Checkout discounts](evals/checkout-discount-once) | Root-cause repair across callers | A discount is applied twice or only the API path is repaired |
| [Git remote normalization](evals/git-remote-normalization) | Protocol parsing and input validation | Explicit ports, IPv6, or SCP-style repository paths are misread |
| [Download filename encoding](evals/download-filename-encoding) | Safe protocol serialization | Quotes or Unicode are lost, or control characters enter a header |
| [Transactional buffer acknowledgement](evals/transactional-buffer-acknowledgement) | Durability and atomic mutation | Unacknowledged data is lost or partial deletes survive an error |
| [Cross-session framework reuse](evals/cross-session-framework-reuse) | Transfer repository conventions | A fresh session must re-learn the extension mechanism |
| [Cross-session deduplication reuse](evals/cross-session-deduplication-reuse) | Transfer a normalization lesson | The same Unicode mistake recurs on a different export field |

## Dataset layout

```text
agora-tasks/
├── README.md
├── evals/                       # local Harbor dataset
│   └── <task>/
│       ├── README.md
│       ├── task.toml
│       ├── instruction.md
│       ├── environment/          # pinned base image and frozen source
│       ├── solution/             # executable reference implementation
│       └── tests/                # hidden checks and a known-wrong variant
├── tools/                       # independent run-time tool instructions
└── docs/
```

Multi-step tasks place instructions, solutions, and tests under `steps/<name>/`.
Each directory runs independently with Harbor; no repository-specific runner or
parent-directory imports are required. The layout follows the
[Harbor cookbook](https://github.com/harbor-framework/harbor-cookbook).

## Evaluate the work, not the tool's name

Task instructions and scores stay fixed across tools. Agent, model, MCP configuration,
and optional adoption instructions are supplied at launch through Harbor.
[Tool configuration](tools/README.md) includes a plain-notes control and describes the
boundary for external integrations.

In the two reuse tasks, each step starts a fresh conversation and the source workspace
resets before step two. State outside the workspace can persist within the trial.
Correctness is graded per step; tokens, time, and observed tool activity belong in the
comparison, not in a tool-specific reward.

## Evidence and boundaries

See [validation results](docs/validation.md), [running and inspecting trials](docs/running.md),
and [evaluation methodology](docs/methodology.md).

These are synthetic, focused fixtures adapted from earlier internal evaluations.
[Provenance](PROVENANCE.md) records the source scenarios and reductions. Reference-solution
success proves the tasks are solvable; it is not an agent benchmark result or a claim
that any tool improves performance. Full-repository difficulty and adversarial verifier
security are outside this release's scope.

## Contributing

Keep each task self-contained and independent of the evaluated tool. Document the
behavioral contract, add a reference solution, and supply a plausible wrong implementation
that the verifier rejects. Run `uv run python scripts/check.py` and the Docker Oracle
trial before submitting a change. See [methodology](docs/methodology.md) for scoring
and experimental controls.

MIT licensed.
