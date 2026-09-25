# Apply checkout discounts exactly once

Trace a pricing regression across API, service, and serialization boundaries.

## Run

From the repository root (Docker must be running):

```sh
uv run harbor run -p evals/checkout-discount-once -a oracle --env docker --jobs-dir evals/jobs
```

This credential-free command checks the reference solution. See [running an agent](../../docs/running.md)
for model-backed trials and [tool integrations](../../overlays/README.md) for independent tool selection.

## Contract

Promo orders are exporting totals below the expected amount after a pricing refactor.
Fix the shared cause so both checkout(payload) and export_orders(payloads) apply the
discount exactly once, before tax. Serialization must only format the finalized total
to two decimal places and preserve the account. Direct serialize(order) callers must
also work. Preserve Decimal half-up rounding, non-promo totals, and input objects.
Supported promos and tax regions are defined in src/shop/pricing.py.


## Verification

The verifier executes hidden Python standard-library behavioral tests and writes
`/logs/verifier/reward.txt`, `checks.json`, and `checks.log`.
A completed check suite scores 1 only when all checks pass; incorrect or missing
implementations score 0. Setup failures and verifier crashes produce no score.
The mutation check rejects: A serializer re-applies a discount to already finalized totals.
Public smoke tests, when present, are development aids; editing them cannot change the hidden score.

## Layout

```text
checkout-discount-once/
├── README.md
├── task.toml
├── instruction.md
├── environment/                 # Dockerfile and frozen source
├── solution/                    # known-good implementation
└── tests/                       # hidden behavior checks and negative fixture
```

## Provenance and limits

Adapted from `agora-bench/evals/pilot-knowledge-relay` at commit
`7c1ba317267adf95dc13e043b73cca5daa43b48d`.
This is a synthetic, reduced fixture with rewritten contracts and stronger verifiers,
not a reproduction of a full upstream repository benchmark or its historical scores.
No task requires Agora or awards points for invoking a particular tool.
The fixture isolates this behavior; passing it is not evidence of general production readiness of the evaluated agent.
