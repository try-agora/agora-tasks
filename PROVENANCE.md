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
All fixtures are synthetic; there is no production data, user transcript, credential,
internal corpus snapshot, or copied third-party benchmark solution.
