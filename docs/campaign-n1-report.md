# codebase-memory-mcp pilot (n=1 results; n=3 protocol)

**Observed run: n=1 per task.** The saved results below are one run, not an n=3 average. The next comparison protocol is n=3; its aggregation is specified below.

## Results

| Measure | Observed mean (n=1) |
| --- | ---: |
| Tasks passed / incorrect / setup rejected | 14 / 4 / 7 of 25 |
| Executed stages with reconciled token usage | 20 / 27 planned |
| Stages with MCP adoption / calls | 19 / 20; 82 calls |
| Input / cached input / output tokens | 5,469,182 / 4,711,936 / 47,526 |
| Agent time / whole-job time | 25.77 / 46.95 minutes |
| Harbor cost estimate | $0.3027 |
| Full-suite composite | unavailable; setup failures remain unscored |

Input includes cached tokens. Cost is Harbor’s price estimate, not a subscription charge or remaining credit balance. No retries ran.

| Task | Result | Mean tokens (n=1) | Mean agent seconds (n=1) | Mean index seconds (n=1) | MCP calls |
| --- | --- | ---: | ---: | ---: | ---: |
| alamofire-deferred-validation-audit | setup | — | — | — | 0 |
| checkout-discount-once | pass | 235,019 | 57.9 | 6.9 | 11 |
| cross-session-deduplication-reuse | pass | 420,677 | 116.9 | 13.4 | 6 |
| cross-session-framework-reuse | pass | 476,521 | 146.2 | 13.4 | 15 |
| django-hmac-impact-inventory | fail | 375,822 | 106.0 | 12.0 | 3 |
| django-lookup-hierarchy-audit | fail | 324,618 | 98.4 | 11.8 | 3 |
| django-multi-parent-update | pass | 612,327 | 111.0 | 11.4 | 3 |
| django-query-execution-map | fail | 438,282 | 111.1 | 11.8 | 2 |
| django-upsert-column-mapping | pass | 376,080 | 73.8 | 12.1 | 3 |
| django-utility-fan-in-ranking | pass | 203,743 | 87.9 | 11.8 | 2 |
| download-filename-encoding | pass | 161,124 | 48.1 | 6.7 | 3 |
| eshop-order-lifecycle-audit | pass | 402,755 | 94.4 | 7.2 | 2 |
| excalidraw-render-invalidation-audit | setup | — | — | — | 0 |
| git-remote-normalization | pass | 230,282 | 79.8 | 6.9 | 4 |
| jellyfin-playback-negotiation-audit | setup | — | — | — | 0 |
| leveldb-read-cache-audit | setup | — | — | — | 0 |
| leveldb-write-path-audit | setup | — | — | — | 0 |
| middleware-authentication | pass | 192,419 | 89.7 | 6.8 | 7 |
| middleware-rate-limiting | pass | 211,740 | 60.0 | 7.4 | 5 |
| nestjs-http-lifecycle-audit | fail; unused MCP | 172,806 | 66.3 | 7.9 | 0 |
| notification-api-compatibility | pass | 230,572 | 51.2 | 6.7 | 5 |
| sphinx-extension-event-routing | setup | — | — | — | 0 |
| sphinx-prolog-document-titles | setup | — | — | — | 0 |
| stable-record-deduplication | pass | 201,998 | 62.5 | 6.7 | 4 |
| transactional-buffer-acknowledgement | pass | 249,923 | 85.2 | 7.2 | 4 |

## Setup and trace review

| Task | Finding |
| --- | --- |
| Alamofire | 18 partially parsed files |
| Excalidraw | 13 excluded files; exclusion list truncated |
| Jellyfin | 1 partially parsed file |
| LevelDB read and write | 29 partially parsed files each |
| Sphinx event and title | 7 partially parsed files each |
| NestJS | No MCP calls; answer failed POST status and filter-order checks |

- Download and notification tasks passed after source and caller retrieval through MCP.
- Django fan-in passed using a shell AST scan; graph calls provided orientation only.
- Django query search returned no matches; lookup results omitted 17 required classes.
- HMAC paths had missing hops. Cross-session tasks passed both stages; this confirms reset handling, not retained-memory benefit.

## Comparison protocol

| Setting | n=3 protocol |
| --- | --- |
| Scope | codebase-memory-mcp only; same 25 tasks and frozen revision |
| Attempts | 3 independent attempts per task (`-k 3 -n 1 -r 0`); fresh sessions, no retries |
| Model | Luna, low reasoning; same runtime and shared adoption instruction |
| Correctness | Mean pass rate over valid binary verdicts; report denominator and setup failures separately |
| Efficiency | Arithmetic mean tokens and agent time over valid attempts; show each valid-attempt count |
| Failure policy | Retain all failures; never impute missing values or selectively rerun |

Keep the baseline separate. CodeGraph was cancelled; GitNexus and Graphify were not run.

## Provenance

| Item | Value |
| --- | --- |
| Task revision | `352498a83b535de4f19387e14886695a05f5009d` |
| Model/runtime | `openai/gpt-5.6-luna`; Codex 0.144.3; Harbor 0.23.0 |
| Integration | codebase-memory-mcp v0.10.8, fast mode |
| Environment | Linux ARM64; 1 CPU, 4 GiB; reset-aware indexing |
| Run duration | 46.95 minutes |

The [evidence data](campaign-n1-data.json) contains per-stage measurements, image digests, and hashes for the local native records. Raw traces remain local. The [protocol record](campaign-n1.md) documents the scope change.
