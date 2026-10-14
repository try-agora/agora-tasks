# What the suite measures

Twenty-five tasks cover code repair, repository comprehension, and cross-session reuse.
The original ten synthetic tasks isolate failures in
state lifetime, compatibility, stable data transformations, pricing boundaries,
protocol parsing, header safety, transaction atomicity, and cross-session reuse.
Fifteen additional tasks use pinned upstream source. Their READMEs distinguish executable
behavior checks from bounded static audits. Together these are selected engineering
scenarios, not a representative sample of all production work.

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
mean, so 0.5 means one step passed. Harbor can still average only executed steps;
the result checker and composite scorer additionally require every declared step.
Prior step verifier artifacts are not intended memory. Do not expose them through a tool.
The underlying source remains available in both steps: an unaided agent can re-derive it.
These are **re-learning efficiency controls**, not memory-required retention tests.
The email step even restates the normalization policy. A capable agent can solve both
steps from scratch, as the Luna run demonstrated. A fresh conversation does not mean a
fresh filesystem: state outside /app persists even in the no-tool arm.

Memory can help avoid rediscovery, reduce tokens/time, or prevent a repeated mistake.
It can also add retrieval overhead or propagate a bad conclusion. With baseline accuracy
already at 100%, these fixtures cannot currently demonstrate an accuracy gain. The
existing result is not evidence that memory was used or that a memory product works.

A stronger future retention task would introduce trial-specific policy or feedback in
step one, remove the original material before a later related request, and allow any
generic memory mechanism to retain it. A larger re-learning task could instead leave
the source accessible but make rediscovery materially expensive under a fixed budget.
Those are different task contracts, not changes to make silently after seeing scores.

## Completion and efficiency reward

`scripts/score_job.py` computes a host-side final score from saved Harbor trial records.
It does not rerun agents, edit raw rewards, or replace ATIF. Task verifiers continue to
emit portable behavioral correctness (0 or 1). The composite is a separate, explicitly
versioned **derived scorecard**, not a new value silently written into Harbor's
`verifier_result.rewards.reward` or console mean.

For a stage with total tokens T and agent execution seconds L:

```text
stage reward = correctness × (0.8 + 0.1 / (1 + T / 100000) + 0.1 / (1 + L / 120))
task reward  = mean(stage rewards), only if every required stage passed; otherwise 0
```

Thus correct work always outranks incorrect work, and faster/leaner successful work
scores higher. A failed stage cannot be offset by a fast successful stage. The report
keeps each stage's correctness, finished status, usage, timing, and reward visible.

- `finished`: every required stage produced a behavioral verdict without a recorded
  infrastructure exception; this is distinct from correct completion.
- `completed`: every required stage passed its behavioral tests.
- T is Harbor input tokens **including cached input**, plus output tokens. Cached
  tokens are shown separately but never added twice. This is token volume, not dollars.
- L is the recorded agent execution duration. It includes agent/tool waiting inside
  that phase, but excludes Docker builds, agent installation, and verifier execution.
  Multi-step totals sum the individual agent phases; they are not parallel job wall time.
- Missing stages, infrastructure exceptions, missing usage/timing, and invalid counts
  yield no composite score (`null`) and a nonzero scorer exit. Missing usage is never
  interpreted as a free, instantaneous run. Oracle/nop often have no token telemetry.

The 80/10/10 weights and round normalization scales are an explicit initial policy,
not validated benchmark thresholds or parameters calibrated to prove a tool advantage.
`--token-scale` and `--seconds-scale` change the scales; freeze them before paired
comparisons. Report raw dimensions alongside the composite, repeat latency measurements,
and compare the same model/runtime/hardware. This scoring version does not reconstruct
retry-attempt usage, so jobs with retries are not eligible for a composite score.

External memory-tool model calls are included only if the integration reports them in
Harbor's usage. Otherwise their cost is unmeasured, and the composite is not a complete
end-to-end efficiency comparison. Include capture work from the first stage as well as
later retrieval; reporting only a cheap second stage would hide memory's acquisition cost.

## Product capture→reuse

`scripts/check_reuse_job.py` audits the version 1 evidence tree without starting a
container or model. It fails closed on incomplete or mixed pins, reused principals,
cross-step calls, unsettled capture jobs, non-human acceptance, instruction changes,
duplicate cursor effects, failed verification, and missing semantic review. A receipt
requires `executor: "ported"` and `accept: "person"`. Other runs are labeled
`plumbing`; every verdict prints the acceptance policy.

A reuse event joins four records: a claim accepted by a person, a completed retrieval
by the second agent principal, the corresponding call-log row, and a later edit to a
repository file cited by the claim. An explicit claim identifier in the final message
or edit is reported as `cited`, but is not required. The checker writes `review.md`
with the claim, message context, and edited files. The event remains `pending-review`
until `review.json` names a reviewer, an `applies` verdict, and a time.

`scripts/score_reuse.py` emits the separate `capture-reuse-v1` scorecard. Each task and
arm cell reports its denominator and these raw dimensions:

- verified, pending-review, and absent reuse events;
- second-step tool calls, shell executions, and files read;
- first-plus-second-step agent tokens, second-step tokens, and product input plus
  output tokens;
- agent, capture, acceptance, and human-wait seconds; and
- the unchanged `completion-efficiency-v1` mean.

Tokens saved are the matched baseline mean for both steps minus the product-arm mean
for both steps and product-side usage. A `source: "fixture"` usage record contributes
zero and is labeled in its cell. Missing product usage yields a null product composite
and a nonzero exit; a missing matched baseline suppresses tokens saved. Protocol mode
requires the declared 12 unique one-trial jobs for two tasks, two arms, and three
attempts, and refuses retries rather than imputing them.

## Comparing tools

Hold task revision, agent version, model, budgets, network access, and repetitions fixed.
Include the no-tool control; plain-notes is an optional, separately labeled treatment.
Check actual observed tool activity and
service health before interpreting a tool arm. Record all runs, including invalid ones.
Count setup/capture costs and any model tokens consumed by the tool itself.

For reuse, compare correctness first, then per-step tokens, time, and actions from Harbor
artifacts. A higher second-step score does not alone prove retrieval, and a tool's name
appearing in a transcript does not prove it worked. Repeated paired runs are needed before
claiming a benefit. No model or tool ranking is published in this repository.

### Measurement protocol

Freeze these choices before a comparison; do not select settings after seeing rewards:

1. Freeze the revision, locks, host, model, runtime, timeouts, and shared instruction. Use the same settings across selected arms.
2. Declare the task subset; use fresh containers and conversations, serial execution, and no retries. Keep every attempt.
3. Run **three attempts per task** with unique job names. Check each saved job and inspect actual MCP results.
4. Report pass rate over valid verdicts and arithmetic mean tokens/time over valid attempts, with denominators. Show setup failures separately; never impute or replace missing results.

The existing smoke results are readiness evidence, not this repeated campaign. No full
paid comparison is required merely to validate provisioning. Keep raw Harbor/ATIF/native
traces local until reviewed; model service variability and caching still limit exact repeats.

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
