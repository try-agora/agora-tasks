# LevelDB write-path audit

Follow a public Put through batching, virtual calls, WAL writes, POSIX sync,
WriteBatch callbacks, a templated skiplist, and reader-visible sequence state.
The output identifies 15 precise source boundaries and 12 policy/durability facts.
It distinguishes Flush from Sync and synchronous versus asynchronous batch leaders.

## Motivation

[CodeGraph's cross-language benchmark](https://github.com/colbymchenry/codegraph/blob/main/docs/benchmarks/codegraph-ab-matrix.md)
includes LevelDB as a C++ call-flow workload and reports reduced source reads.
This independent task adds deterministic call-site and behavioral-policy grading.
It does not import the vendor's result, assume its model or code revision, or
require a graph tool. Normal baseline source analysis remains permitted.

## Verification

All source bytes are integrity-checked. Manually traced call-site witnesses and
decision evidence are checked against the pinned source, separately from the
reference artifact and from all provider graphs. A plausible mutation incorrectly
treats POSIX Flush as a durable sync. All answers must be correct for reward 1;
failed answers receive 0, while broken grading evidence emits no reward. Existing
token and latency scoring is unchanged.

This is a source-audit task, not a storage stress test or an executed proof of
crash consistency. It fixes the normal write and POSIX paths, explicitly naming
the conditional sync macros. The complete upstream C/C++ source selection includes
public tests as ordinary context, not the hidden artifact verifier.

```bash
uv run harbor run -p evals/leveldb-write-path-audit -a oracle
CODEX_FORCE_AUTH_JSON=1 uv run harbor run -c overlays/baseline.yaml -p evals/leveldb-write-path-audit
```

## Provenance

LevelDB 1.23, commit `99b3c03b3284f5886f9ef9a4ef703d57373e61be`, BSD-3-Clause.
135 files are imported byte-for-byte. License and authors are included; selection
and digest are recorded in `environment/SOURCES.json`. This intentionally does
not include build-system templates or third-party submodules: compilation is not
part of the audit. Public-source training contamination is possible.

Before any model pilot, the prompt was refined to name the write/read navigation
endpoints for every arm. Intermediate relationships and policy decisions still
require source evidence; source, answers, and grading were unchanged.

## Observed setup limitation — 2026-09-25

All three codebase-memory-mcp pilot attempts stopped before the agent ran.
The index reported `indexed`, 2,839 nodes, and 11,340 edges, but the frozen
readiness check rejected two intentionally skipped files (`leveldb/LICENSE`
and `leveldb/AUTHORS`). It also reported 29 partially parsed source files,
including production C/C++ and upstream tests. The first rejected field was
`not_indexed_files_count`; these attempts have no agent score or token usage.

This does not establish that the resulting graph could not answer the audit.
Readiness signals/checks differ across the frozen providers, so these setup
failures are not an apples-to-apples navigation-accuracy comparison. No license,
source constructs, or overlay checks were removed to make this arm run. Logs
are retained under
`evals/jobs/overnight-leveldb-write-path-audit-codebase-memory-mcp-n3-v1/`.

## Exploratory comparison — 2026-09-25

Three attempts per frozen overlay, `openai/gpt-5.6-luna` at low effort. Native
Oracle passed and no-op failed before model trials. This is candidate selection,
not an independently confirmed advantage or a general provider ranking.

| Arm | Correct / valid | MCP-call trials | Mean total tokens | Mean agent seconds | Mean index seconds | Mean combined reward |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 0 / 3 | 0 / 3 | 337,086 | 71.72 | 0.34 | 0 |
| CodeGraph | 1 / 3 | 3 / 3 | 300,390 | 61.27 | 2.10 | 0.29487 |
| GitNexus | 2 / 3 | 3 / 3 | 406,270 | 77.75 | 26.45 | 0.58961 |
| Graphify | 1 / 3 | 0 / 3 | 359,196 | 71.09 | 1.87 | 0.29334 |
| codebase-memory-mcp | 0 / 0 | No agent ran | — | — | Not ready | Unscored |

The interpretation is deliberately narrow: **all twelve completed agent trials
got the twelve policy decisions right**. Completion differences arose from the
explicit source-location contract. Baseline failed on the batch callback, a
method declaration instead of its delegate call, or adjacent memtable lines.
One baseline trace even displayed the correct numbered delegate call in its
final check but left the declaration line in its artifact. These are audit
precision failures, not evidence that baseline misunderstood write durability.

CodeGraph's passing `__khcKGDo` run received a call-flow prefix and useful
`WritableFile.Sync` implementation locations, including the requested POSIX
implementation. It then inspected source in the shell. The other runs also used
relevant MCP navigation; they failed on nested-class qualification/read-sequence
location, or an extra `src/` path prefix plus a wrong memtable-index line.
Static graph paths are navigation hints, not proof of the active runtime path.

GitNexus's passing `__BDqydr9` run queried the write path and retrieved `Write`,
`BuildBatchGroup`, and `MemTableInserter` definitions. Its other pass (`__phxZj7Q`)
only fetched repository metadata/tool listings and is not evidence of useful
MCP navigation. The failed `__BeuxTkF` run did make a relevant coding query after
an invalid context call; it missed the sync-fence line. All three Graphify runs
made no MCP calls, so its passing answer cannot be attributed to Graphify.

Native cumulative usage, Codex turn usage, Harbor results, and ATIF totals agree
for every completed agent trial. Initial indexing preceded the agent timer.
Tokens include cached input once; failed answers score zero. The setup failures
above remain unscored. Raw evidence is retained locally under
`evals/jobs/overnight-leveldb-write-path-audit-<arm>-n3-v1/`.

GitNexus was selected by the correctness-first pilot result for five fresh,
alternating baseline/GitNexus pairs, without changing the task or runtime.
Those jobs use `confirm-leveldb-write-r<1..5>-<arm>-v1` and must be reported
separately from the selection pilot.

## Fresh confirmation — 2026-09-25

Five alternating baseline/GitNexus pairs completed without retries or
infrastructure errors. Task, model, overlays, and scoring were unchanged.

| Arm | Correct / valid | Useful MCP trials | Mean total tokens | Mean agent seconds | Mean index seconds | Mean combined reward |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 4 / 5 | 0 / 5 | 331,270 | 66.44 | 0.17 | 0.71111 |
| GitNexus | 2 / 5 | 2 / 5 | 362,787 | 70.99 | 27.55 | 0.35449 |

The pilot advantage did not reproduce. Baseline also used fewer tokens and less
agent time on average. All ten trials answered every policy question correctly;
the completion differences again concern the source-location contract.

Manual trace and artifact review found:

- Baseline passed pairs 1, 2, 4, and 5. Its pair-3 failure selected the wrong
  owning methods for the batch-key append, callback invocation, and entry insert.
- GitNexus pair 1 received only `Symbol not found` and selected the callback's
  implementation instead of its invocation in `WriteBatch::Iterate`.
- GitNexus pair 2 received relevant source, including the write and batch
  implementations. Every symbol, line, and policy answer was correct, but all
  file paths incorrectly included `src/`. This is a format-only failure, not
  evidence of failed navigation.
- GitNexus pair 3 received useful `Put` source and relationships. Its only
  mismatch was `Node::SetNext` instead of the required fully qualified
  `SkipList::Node::SetNext`; the file and line were correct.
- Both GitNexus passes (pairs 4 and 5) made one `trace` call that returned
  `Source symbol 'DBImpl::Put' not found`, then solved the task with shell
  inspection. Neither pass is evidence of successful MCP assistance.

The declared contract was not relaxed or rescored after seeing these results.
All ten native/turn/Harbor/ATIF token totals reconcile, and indexing finished
before agent execution. Raw results, artifacts, native sessions, and ATIF traces
remain local under `evals/jobs/confirm-leveldb-write-r<1..5>-<arm>-v1/`.
