# LevelDB point-read cache audit

Trace a read through mutable and immutable memtables, overlapping table files,
two different caches, filter callbacks, and block decoding. The practical
question is whether `fill_cache=false` disables caching, cache population, or
only one specific admission path. Sixteen source locations and eighteen
behavior decisions distinguish these mechanisms without modifying LevelDB.

## Motivation and scope

[CodeGraph's published navigation matrix](https://github.com/colbymchenry/codegraph/blob/main/docs/benchmarks/codegraph-ab-matrix.md)
includes a LevelDB comparison; graph-oriented MCPs also advertise cross-file
call and dependency navigation. This is a new, bounded read/cache audit of that
kind of workload, not a reproduction of the vendor's prompt, model, or result.
It is distinct from the dataset's write/WAL/publication audit. No tool is
required or presumed superior; ordinary source search is a valid solution.

The task retains the full selected C/C++ source tree, including upstream tests,
so similarly named iterator, compaction, and point-read paths must be separated.
The source fixture is pinned before any model trial. The questions and hidden
source witnesses were derived from the implementation, not an MCP graph.

## Verification

The standard-library verifier checks all protected source bytes, exact artifact
keys and types, sixteen independently located source expressions, and eighteen
manually traced decisions. Source-witness failures are verifier errors, not
agent failures. The reference artifact is not grader input. A mutation incorrectly
treats `fill_cache=false` as disabling existing block-cache hits.

This is a static source audit, not a live storage-performance, crash-recovery,
or full C++ integration benchmark. The verifier does not compile LevelDB or
claim whole-program analysis. Complete correctness earns native reward 1;
incorrect work earns 0. The existing host-side efficiency scorer and independent
overlays are unchanged. Initial indexing is not part of agent timing.

```bash
uv run harbor run -p evals/leveldb-read-cache-audit -a oracle
CODEX_FORCE_AUTH_JSON=1 uv run harbor run -c overlays/baseline.yaml -p evals/leveldb-read-cache-audit
```

## Provenance

LevelDB 1.23, commit `99b3c03b3284f5886f9ef9a4ef703d57373e61be`, under BSD-3-Clause.
`environment/SOURCES.json` records the exact selection and digest. All 135
fixture files are byte-identical to the independently self-contained write-path
task's fixture; neither task depends on its sibling at runtime. Copyright,
license, and author notices remain intact. This is a source subset, not a
complete CMake distribution. Public source may occur in model training data.

## Validation — 2026-09-25

Native Harbor Oracle passed and no-op failed without infrastructure exceptions
(`leveldb-read-cache-oracle-v1`, `leveldb-read-cache-nop-v1`). The complete local
dataset check passed all 75 verifier scenarios across 23 tasks, including this
task's incorrect cache-policy mutation. The task contract and frozen runtime
remain the same for every arm; no benchmark advantage has been established yet.

## Comparison protocol — recorded before model trials

Run three fresh trials for each frozen arm: GitNexus, baseline, Graphify,
codebase-memory-mcp, and CodeGraph, serially in that order. Keep the same cheap
model, low effort, extra instruction, task, and runtime for every arm. These
pilots select candidates, not winners. A candidate needs useful MCP evidence
and a better correctness-gated score than baseline; confirm it separately with
five fresh alternating pairs. Retain failed, no-call, and setup-error attempts.
Do not pool pilot and confirmation results or interpret discovery-only calls
as coding assistance. This small selected comparison cannot establish a general
tool ranking.

## Pre-pilot refinement — 2026-09-25

Version 1.1.0 asks for the containing file/member, not exact line numbers. Earlier
audits on other tasks showed that line transcription could dominate otherwise
correct source reasoning. This change was finalized before any model trial on
this task; all arms receive the same contract. Source, policy questions, source
witnesses, binary correctness, and runtime are unchanged. No previous model
results exist for this task to rescore or select from.

The revised contract passed local reference/no-op/mutation checks and native
Harbor Oracle 1 / no-op 0 without infrastructure errors:
`leveldb-read-cache-audit-oracle-symbol-v2` and
`leveldb-read-cache-audit-nop-symbol-v2`. No model trial had started.

## Exploratory comparison — contract 1.1.0

Three attempts per frozen arm, with the same cheap model and low effort. The
first pilot's job suffix `n3-v1` is a cohort label; all its model trials use the
pre-pilot symbol-only contract 1.1.0. All twelve completed agent trials reconcile
native cumulative usage, Codex-turn usage, Harbor, and ATIF totals. Initial graph
construction finished before each agent timer.

| Arm | Correct / valid | MCP-call trials | Mean total tokens | Agent seconds | Index seconds | Mean combined reward |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | 2/3 | 0 | 195,617 | 54.45 | 0.32 | 0.60716 |
| CodeGraph | 1/3 | 3 | 285,484 | 55.26 | 1.88 | 0.29663 |
| GitNexus | 1/3 | 1 | 225,066 | 57.77 | 28.00 | 0.29898 |
| Graphify | 1/3 | 1 | 174,657 | 44.05 | 1.86 | 0.30678 |
| codebase-memory-mcp | 0/0 | No agent ran | — | — | Not ready | Unscored |

No arm qualifies as a confirmation candidate. Baseline's higher completion rate
outweighs Graphify's lower average tokens/time under correctness-first scoring.
The three codebase-memory-mcp attempts stopped at the frozen readiness guard:
two intentionally skipped notices (`LICENSE`, `AUTHORS`) and 29 partially parsed
C/C++ files; each index reported 2,839 nodes and 11,340 edges. These are unscored
setup failures, not failed answers. The guard and source were not altered.

Manual trace review:

- CodeGraph's passing `__kT7Rk7K` used four relevant explorations whose returned
  source together contained all sixteen location witnesses. Another trial still
  confused the overlap-enumeration caller with its callback. The final trial
  located the right members but incorrectly answered level-zero ordering and
  external-buffer cacheability. Its queries omitted the sort/comparator body
  even when naming `ForEachOverlapping`, while returning the explicit
  `data != buf` / `cachable = false` branch. Missing evidence and misreading
  supplied evidence are different failure modes; neither is repaired by counting
  a completed MCP call as success.
- GitNexus's pass and one failure made no MCP call. The other failure only listed
  the repository and made a context request without the required name/UID.
  None provides useful MCP-navigation evidence.
- Graphify's one tool-using trial received a relevant but noisy DFS inventory,
  with 222 of 301 nodes shown, then confused the enumeration caller with its
  callback. Its passing trial made no MCP call, as did its other failure.
- Most failures are wrong containing-member choices, not incorrect cache policy.
  Eleven of twelve agent trials answered every policy decision correctly; the
  CodeGraph trial described above is the exception. No line-number transcription
  is involved in this contract.

Raw local evidence: `evals/jobs/overnight-leveldb-read-cache-audit-<arm>-n3-v1/`.
