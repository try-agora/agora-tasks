# Agora Tasks

**A reproducible evaluation suite for coding agents and code-navigation tools.**

25 self-contained Harbor tasks cover code repair, repository comprehension, and
cross-session reuse. Each task has a frozen workspace, an explicit contract,
a hidden verifier, a reference solution, and a plausible wrong solution that
must fail. Validation requires no model credentials or Agora installation.

**25 tasks · 27 scored stages · 81 verifier control scenarios**

## Review the engineering

Start with these three examples:

- [Django multi-parent update](evals/django-multi-parent-update/README.md): a real ORM
  repair with 15 SQLite behavior checks, including unrelated-row preservation,
  deeper inheritance, rollback, and set-based execution.
- [Cross-session framework reuse](evals/cross-session-framework-reuse/README.md):
  two fresh conversations with workspace resets and explicit persistent-state boundaries.
- [Alamofire deferred validation](evals/alamofire-deferred-validation-audit/README.md):
  a bounded source audit with protected source hashes and independently recorded witnesses.

The [methodology](docs/methodology.md) explains grading and isolation.
The [validation record](docs/validation.md) distinguishes local checks, container checks,
and hosted CI. The [job checker](scripts/check_job.py) verifies complete task/stage
coverage instead of trusting an aggregate reward. Its regression test covers a real
Harbor failure mode: a successful summary with a failed later stage.

The [codebase-memory-mcp campaign](docs/campaign-n1-report.md) applies these checks
to the completed n=1 pilot and specifies an n=3 follow-up with per-task pass rates
and mean usage. It reports setup failures, correctness, and actual tool adoption.

## Run without a model

Requires Python 3.12 or 3.13, [uv](https://docs.astral.sh/uv/), and Docker with
Compose and Buildx. Initial dependency installation and image builds need network access.
Task execution and verification need no external services.

```sh
uv sync --locked
uv run python scripts/check.py
uv run python -m unittest discover -s scripts -p 'test_*.py'
uv run harbor run -p evals -a oracle --env docker --jobs-dir evals/jobs --job-name oracle
uv run python scripts/check_job.py evals/jobs/oracle --expected 1
uv run harbor run -p evals -a nop --env docker --jobs-dir evals/jobs --job-name nop
uv run python scripts/check_job.py evals/jobs/nop --expected 0
```

`check.py` tests every stage against untouched, correct, and deliberately incorrect
work. Docker runs also exercise solution scripts, hidden-test upload, user permissions,
workspace resets, and artifact collection. The checker defaults to all current tasks;
use `--count 1` when checking a single-task job. Use fresh job names for repeated runs.

For a shorter first look, select `-p evals/checkout-discount-once` in the Harbor
commands and add `--count 1` to the checker. Each task can also be copied out and run
independently with the pinned Harbor runtime.

## Task inventory

The original ten tasks use focused synthetic Python fixtures. Fifteen further tasks
use pinned upstream source from Django, Sphinx, NestJS, LevelDB, eShopOnWeb, Jellyfin,
Excalidraw, and Alamofire. Source-audit fixtures are intentionally scoped snapshots,
not necessarily complete buildable upstream distributions.

| Task | Engineering contract |
| --- | --- |
| [alamofire-deferred-validation-audit](evals/alamofire-deferred-validation-audit/README.md) | Trace request setup, deferred validation callbacks, completion barriers, retry, and response serialization. |
| [checkout-discount-once](evals/checkout-discount-once/README.md) | Trace a pricing regression across API, service, and serialization boundaries. |
| [cross-session-deduplication-reuse](evals/cross-session-deduplication-reuse/README.md) | Transfer a normalization lesson to a second export field after source reset. |
| [cross-session-framework-reuse](evals/cross-session-framework-reuse/README.md) | Learn a middleware framework, then apply that knowledge after a clean workspace reset. |
| [django-hmac-impact-inventory](evals/django-hmac-impact-inventory/README.md) | Inventory direct callers and shortest upstream impact paths for a shared Django signing helper. |
| [django-lookup-hierarchy-audit](evals/django-lookup-hierarchy-audit/README.md) | Inventory core Lookup descendants, ordered bases, and effective hook owners before an ORM API migration. |
| [django-multi-parent-update](evals/django-multi-parent-update/README.md) | Repair bulk updates across multiple inherited database tables without corrupting unrelated rows. |
| [django-query-execution-map](evals/django-query-execution-map/README.md) | Map lazy ORM evaluation, dynamic compiler dispatch, and the SQLite execution boundary using source-linked facts. |
| [django-upsert-column-mapping](evals/django-upsert-column-mapping/README.md) | Repair custom-column handling across bulk-upsert validation, insert compilation, and backend SQL generation. |
| [django-utility-fan-in-ranking](evals/django-utility-fan-in-ranking/README.md) | Rank shared utilities by distinct-file direct-caller fan-in, resolving aliases and rejecting incidental text matches. |
| [download-filename-encoding](evals/download-filename-encoding/README.md) | Preserve Unicode filenames and quoted parameters while rejecting header injection. |
| [eshop-order-lifecycle-audit](evals/eshop-order-lifecycle-audit/README.md) | Audit checkout ordering, snapshot semantics, DI/mediator boundaries, and customer predicates in eShopOnWeb. |
| [excalidraw-render-invalidation-audit](evals/excalidraw-render-invalidation-audit/README.md) | Trace element mutations across scene observers, React rendering, two caches, and animation-frame scheduling. |
| [git-remote-normalization](evals/git-remote-normalization/README.md) | Parse URL and SCP-style remotes while preserving identity and validating malformed input. |
| [jellyfin-playback-negotiation-audit](evals/jellyfin-playback-negotiation-audit/README.md) | Trace playback requests across user selection, dependency injection, media providers, bitrate policy, and stream negotiation. |
| [leveldb-read-cache-audit](evals/leveldb-read-cache-audit/README.md) | Trace point reads across memtables, overlapping files, table and block caches, filters, and callbacks. |
| [leveldb-write-path-audit](evals/leveldb-write-path-audit/README.md) | Trace write batching, WAL durability, callback dispatch, and reader-visible sequence publication in LevelDB. |
| [middleware-authentication](evals/middleware-authentication/README.md) | Add a security boundary while preserving opt-in behavior and middleware composition. |
| [middleware-rate-limiting](evals/middleware-rate-limiting/README.md) | Extend an unfamiliar middleware pipeline without breaking state lifetime or routing. |
| [nestjs-http-lifecycle-audit](evals/nestjs-http-lifecycle-audit/README.md) | Trace HTTP routing, request policy, response adaptation, and exception boundaries in pinned NestJS source. |
| [notification-api-compatibility](evals/notification-api-compatibility/README.md) | Evolve a shared API without changing legacy payloads or breaking sibling callers. |
| [sphinx-extension-event-routing](evals/sphinx-extension-event-routing/README.md) | Audit configured extension dependencies, callback registration, and priority-stable event dispatch. |
| [sphinx-prolog-document-titles](evals/sphinx-prolog-document-titles/README.md) | Repair role-based title loss across Sphinx's RST preprocessing, parser, and navigation pipeline. |
| [stable-record-deduplication](evals/stable-record-deduplication/README.md) | Preserve data identity and ordering while normalizing duplicate keys. |
| [transactional-buffer-acknowledgement](evals/transactional-buffer-acknowledgement/README.md) | Release acknowledged records without losing unacknowledged data or violating atomicity. |

## Architecture

```text
evals/<task>/
  task.toml             # native Harbor contract
  instruction.md        # agent-visible request
  environment/          # pinned image, frozen source, source provenance
  solution/             # reference implementation, Oracle-only upload
  tests/                # hidden verifier and incorrect-solution control
  steps/<name>/         # per-step contracts in the two reuse tasks

overlays/               # independent tool installation, indexing, MCP configs
scripts/                # local checks, saved-job validation, offline scoring
docs/                   # methodology, running instructions, validation record
```

Tasks never import overlays. Agents run unprivileged; verifiers run without network.
Reference solutions and hidden tests are excluded from task images. Multi-step overlays
rebuild indexes after reset and before agent timing. Missing telemetry and infrastructure
errors remain unscored; cached tokens are counted once. Dependencies and source revisions
are pinned, while remaining build-time inputs are documented explicitly.

## Optional agent and tool runs

For an existing Codex login:

```sh
CODEX_FORCE_AUTH_JSON=1 uv run harbor run -c overlays/baseline.yaml \
  -p evals/checkout-discount-once --job-name agent-smoke
```

This consumes model usage. See [running instructions](docs/running.md) for authentication
and network policy, and [runtime overlays](overlays/README.md) for the four MCP integrations.
Overlay compatibility is separate from task correctness; the current support limits are
listed there. Model runs are not required to review or validate this project.

[Historical experiments](results.md) retain the original results and limitations.
They are not release acceptance criteria or a claim that any tool wins.

## Contributing and scope

Keep tasks independent. Specify the observable contract, preserve upstream attribution,
add a correct reference and a plausible incorrect control, then run local checks and
both Docker controls. Never change a published task contract silently after observing
agent results. Record a task version change when its grading contract changes.

These verifiers target cooperative coding-agent evaluation. They do not isolate
malicious candidate code from the verifier inside the shared container. Public upstream
code can also occur in model training data; this suite does not establish uncontaminated
reasoning or general tool superiority.

Original harness and task-authoring code is [MIT licensed](LICENSE). Vendored upstream
source, dependencies, and adapted upstream fixes retain their own licenses and notices;
see [provenance and attribution](PROVENANCE.md).
