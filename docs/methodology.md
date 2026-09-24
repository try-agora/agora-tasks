# What the suite measures

Ten controlled coding tasks isolate failures that matter in ordinary software work:
state lifetime, compatibility, stable data transformations, pricing boundaries,
protocol parsing, header safety, transaction atomicity, and cross-session reuse.
They are synthetic fixtures, not a representative sample of all production engineering.

## Task, agent, and tool are separate

The task supplies a frozen source tree, a behavioral contract, hidden checks, and a
reference implementation. The Harbor run supplies the agent, model, and optional tools.
Scoring observes resulting behavior rather than tool mentions, call counts, chosen
helpers, or similarity to the reference code. The middleware tasks explicitly require
registration because extending the framework through its documented API is the capability.

The tool-free task image contains no Agora wheel, memory store, privileged integration
hook, or vendor onboarding. A task works when copied out of this repository.

## Cross-session boundaries

Two tasks have two steps. The first teaches a repository convention through real work.
The second starts a fresh conversation after /app is reset to the original fixture.
Only state outside /app persists within the container. /memory is available to an optional
tool, and each trial starts in a fresh environment. An external service must implement
equivalent per-trial namespace and reset isolation.

Each step scores independently; both run even if the first fails. The aggregate is their
mean, so 0.5 means one step passed. This avoids treating a skipped second step as success.
Prior step verifier artifacts are not intended memory. Do not expose them through a tool.
The underlying source remains available in both steps: an unaided agent can re-derive it.
That is necessary for a meaningful correctness baseline.

## Comparing tools

Hold task revision, agent version, model, budgets, network access, and repetitions fixed.
Include both no-tool and plain-notes controls. Check actual observed tool activity and
service health before interpreting a tool arm. Record all runs, including invalid ones.
Count setup/capture costs and any model tokens consumed by the tool itself.

For reuse, compare correctness first, then per-step tokens, time, and actions from Harbor
artifacts. A higher second-step score does not alone prove retrieval, and a tool's name
appearing in a transcript does not prove it worked. Repeated paired runs are needed before
claiming a benefit. No model or tool ranking is published in this repository.

## Verifier scope

Hidden tests are uploaded at verification time and made inaccessible to the unprivileged
agent after execution; reference solutions are only uploaded
for Oracle runs. Grading uses Python's standard library, deterministic cases, and regression
checks against multiple callers or inputs. Bytecode writes are disabled so verification
does not leave privileged files in the next session's workspace.
Candidate syntax/import errors are failed work;
verifier crashes yield no score. Verifiers never trust agent-edited public smoke tests.

The agent runs as an unprivileged user, and verification runs as root without network.
These shared-container checks are designed for cooperative coding-agent evaluation,
not as a security boundary against a deliberately malicious candidate program. Use a
separate verifier environment and review artifacts before adversarial use.

## Reproducibility limits

Task source and the Python base-image digest are fixed. Harbor and its Python dependencies
are locked. OS utilities installed during Docker build come from Debian repositories;
rebuilding later can resolve newer packages. Keep the built image digest with a published
campaign. Agent runtime installation, model sampling, and hosted tool responses can also
change. Reference-solution checks establish task solvability, not model performance.
