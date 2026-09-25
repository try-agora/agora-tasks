# Provenance

The source scenarios come from the locally developed agora-bench repository at commit
`7c1ba317267adf95dc13e043b73cca5daa43b48d`. Each task records its source family in task.toml.
This collection rewrites task boundaries, environment packaging, reference solutions,
and behavioral verifiers. Historical benchmark results do not transfer to these tasks.

| Source family | Tasks | Adaptation |
| --- | --- | --- |
| pilot-comprehension-floor | middleware-rate-limiting, middleware-authentication, cross-session-framework-reuse | Frozen synthetic middleware framework; explicit state lifetime, optional auth, and logging contracts |
| pilot-rework-floor | stable-record-deduplication, cross-session-deduplication-reuse | Frozen synthetic record library; Unicode normalization, stability, identity, and mutation checks |
| pilot-bwcompat-floor | notification-api-compatibility | Synthetic API evolution with exact legacy payload compatibility |
| pilot-knowledge-relay | checkout-discount-once | Convert a diagnosis exercise into a repair task; decimal pricing and checks across API and batch callers |
| chain1 | git-remote-normalization | New minimal Python fixture inspired by the remote/port parsing scenario; no upstream repository code copied |
| pilot-rework2 | download-filename-encoding | New minimal Python fixture for header encoding; not the original Werkzeug task or code |
| chain2 | transactional-buffer-acknowledgement | New minimal SQLite fixture for acknowledgement atomicity; not the original disk-buffer implementation |

The directory presentation follows the public
[Harbor cookbook](https://github.com/harbor-framework/harbor-cookbook)
inspected at commit `e093c9a`. No cookbook task code is copied.
The original ten fixtures are synthetic and contain no production data, user
transcript, credential, or internal corpus snapshot. The upstream expansion below
has separate source and reference-solution attribution.

## Upstream-source expansion

The ten tasks above are synthetic. The fifteen tasks below contain third-party
source; they do **not** inherit the repository's MIT license. Original copyright
and license notices are preserved alongside the source. Each linked manifest
records exact revisions, selection rules, hashes where available, and transformations.
Task READMEs distinguish source subsets from complete upstream distributions.

| Upstream | Tasks | Source and notices |
| --- | --- | --- |
| Django | multi-parent update, upsert column mapping, query execution map, HMAC impact inventory, lookup hierarchy audit, utility fan-in ranking | Each `django-*` task has `environment/SOURCES.json`; Django `9ffd4eae2ce7a7100c98f681e2b6ab818df384a4`, `workspace/src/LICENSE-Django`; asgiref/sqlparse notices under `workspace/vendor/` (BSD-3-Clause) |
| Sphinx | prolog document titles, extension event routing | [Manifest](evals/sphinx-prolog-document-titles/environment/SOURCES.json); Sphinx `71db08c05197545944949d5aa76cd340e7143627`, `workspace/src/LICENSE-Sphinx` (BSD); twenty vendored dependencies retain their separate licenses under `workspace/vendor/*.dist-info/` |
| NestJS | HTTP lifecycle audit | [Manifest](evals/nestjs-http-lifecycle-audit/environment/SOURCES.json); `workspace/src/LICENSE` (MIT) |
| LevelDB | write-path audit, read-cache audit | [Manifest](evals/leveldb-write-path-audit/environment/SOURCES.json); `workspace/src/leveldb/LICENSE` and `AUTHORS` (BSD-3-Clause) |
| eShopOnWeb | order lifecycle audit | [Manifest](evals/eshop-order-lifecycle-audit/environment/SOURCES.json); `workspace/src/eshop/LICENSE` (MIT) |
| Jellyfin | playback negotiation audit | [Manifest](evals/jellyfin-playback-negotiation-audit/environment/SOURCES.json); `workspace/src/jellyfin/LICENSE` (GPL v2) and original source notices |
| Excalidraw | render invalidation audit | [Manifest](evals/excalidraw-render-invalidation-audit/environment/SOURCES.json); `workspace/src/excalidraw/LICENSE` (MIT) |
| Alamofire | deferred validation audit | [Manifest](evals/alamofire-deferred-validation-audit/environment/SOURCES.json); `workspace/src/alamofire/LICENSE` (MIT) and original source headers |

The Django multi-parent reference contains upstream repaired library files; its
[README](evals/django-multi-parent-update/README.md#provenance-and-scope) credits
the upstream commit and author. The upsert reference adapts the upstream repair,
as documented in its [README](evals/django-upsert-column-mapping/README.md#source-and-hypothesis).
The Sphinx repair adapts the public issue using Docutils' field grammar. These are
attributed reference solutions, not claims that the upstream fixes were authored here.
Independent behavior checks and task packaging are the evaluation contribution.
None of these adaptations is an official SWE-bench harness or score.

Source-audit expected artifacts are bounded, task-authored witnesses checked against
pinned source; they are not exported tool graphs. Public code and historical fixes
may have appeared in training data. Historical tool experiments do not transfer to
new task versions or establish uncontaminated reasoning.
