# Map Django queryset execution through SQLite

A read-only code-navigation task over **863 pinned Django Python files**.
The agent audits four operations in a small runnable application and submits
source-linked execution paths, cache facts, and concrete dispatch bindings.
It does not repair code or need an MCP to pass.

## Run

From the dataset repository root:

```sh
uv run harbor run -p evals/django-query-execution-map -a oracle --env docker --jobs-dir evals/jobs
CODEX_FORCE_AUTH_JSON=1 uv run harbor run -c overlays/baseline.yaml -p evals/django-query-execution-map
```

Use the existing [overlays](../../overlays/README.md) to select a coding MCP.
The task also works when copied out of the dataset: its image, source,
dependencies, verifier, and reference solution are self-contained.

## Capability and contract

Normal iteration, cached iteration, flat-value iteration, and `exists()` are
not interchangeable execution paths. The audit distinguishes active calls from
earlier compiler/cursor setup, concrete dispatch from similarly named methods,
and lazy evaluation from a populated result cache. The relevant source spans
seven modules among the full library tree.

The deliverable is `/app/src/execution-path.json`, containing:

- Per-operation SELECT count and result-cache state.
- The active Django Python stack entering SQLite's cursor wrapper, with source
  paths, qualified symbols, and caller lines.
- Compiler selection, selected compiler class, backend cursor creation, and the
  final driver call, including their defining modules.

The schema is an ordinary task output, not an extension to Harbor's task format.
There are no task-specific agent adapters, injected tools, or host-side graders.
The reference solution writes the artifact; it does not modify Django.

## Verification

`tests/test.sh` emits native binary `reward.txt` and diagnostic `checks.json`
and `checks.log`. All required facts must be correct. The verifier first checks
the source, dependencies, and scenario against a frozen digest. It then runs
the unchanged SQLite scenario and observes its actual call stacks, SELECTs,
and cache state. Four off-stack dispatch sites are independently grounded in
the pinned source. No model-generated reference prose or LLM judge is used.

Multiline call expressions accept any physical line in the expression; JSON
object order and whitespace do not matter. The public `sqlite3`, `sqlite3.dbapi2`,
and `_sqlite3` exports of the identical driver method are accepted by object
identity, not preferred spelling. The reference artifact uses an alias so the
normal Oracle gate protects this behavior. Wrong symbols, inactive frames,
missing frames, fabricated source locations, wrong cache behavior, modified
source, malformed output, and missing output do not pass. Trusted scenario
or verifier-evidence failures produce no reward rather than an agent failure.
The output is size-bounded and duplicate JSON keys are rejected.

`tests/mutation.json` supplies a plausible wrong report that reuses the normal
model path for flat-value iteration. The existing `scripts/check.py` checks
untouched, reference, and mutated work without credentials or model calls.

## Provenance and isolation

The source and local dependencies are byte-identical to the frozen fixture used
by `django-multi-parent-update`; no files or changes are imported from its
solution. Each task owns a full copy so neither depends on its sibling at run
time. Django is pinned to `9ffd4eae2ce7a7100c98f681e2b6ab818df384a4`;
asgiref 3.8.1 and sqlparse 0.5.3 are task-local. Archive URLs, hashes, licenses,
and the selection rule are in `environment/SOURCES.json`.

Both the application scenario (`/app/src/scenario.py`) and Django live under
the common `/app/src` source root so every existing overlay can index them.
Task version 1.1.0 relocates the scenario into that shared scope; it does not
change the ORM operations, required facts, or reward. Do not pool it with
version 1.0.0 pilots that indexed different entry-script coverage.
Version 1.1.1 corrects driver-alias false negatives in the verifier. When
rechecking earlier saved answers, retain their original results and label the
new verdicts as verifier replays, not fresh model trials.

This is the entire upstream Python library tree, not a complete Django
distribution: translations, non-Python resources, upstream tests, repository
history, and later fixes are omitted. `scenario.py` is a synthetic application
running the real ORM against an isolated in-memory SQLite database. Execution
needs no network; OS installation during image build does. MCP installation
and indexing are performed solely by the unchanged external overlays before
agent timing.

## Benchmark interpretation

The design follows the execution-path questions in earlier provider research
and vendor navigation benchmarks. It isolates navigation and dispatch reasoning
from patch-writing ability. It is not a reproduction of a vendor's published
score, and a public framework may be familiar to the model.

The hypothesis is that graph navigation can reduce investigation effort. Shell
search, source inspection, and instrumentation remain valid baseline strategies;
tools are optional and neither call counts nor MCP names affect correctness.
An observed stack is deliberately more precise than a generic architecture
summary, so a static graph alone may be insufficient.

Keep this task regardless of which arm wins. Compare every arm on the same
frozen task version, disclose actual MCP adoption, and report correctness before
token/latency efficiency. The existing host scorer remains unchanged; cold index
time is separate from agent latency. Do not treat one task or a small pilot as a
general MCP ranking or proof of durable memory.
