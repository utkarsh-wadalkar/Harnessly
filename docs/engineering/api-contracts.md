# API contract rules

Authoritative models: `packages/contracts/models.py`. Export `python -m scripts.export_contracts`; check drift with `--check`. Generated OpenAPI describes **planned** HTTP routes. JSON Schema covers wire shapes; Pydantic additionally enforces cross-field invariants. Workflow specs govern database/ownership checks that a schema cannot prove.

Generate frontend types with the pinned openapi-typescript 7.13.0 tool using `pnpm contracts:generate`; `pnpm contracts:check` fails on drift. The generator consumes OpenAPI rather than maintaining independent handwritten frontend schemas.

## Identity and access

Private interview/profile/experiment/recommendation resources are session-owned. Return 404 for another owner's resources. Secure HttpOnly SameSite cookies require CSRF tokens on browser mutations; local invite sessions are issued by the owner. Maintainer permission is additionally required for global plans and publication. Anonymous callers may read only verified public cohorts/redacted public artifacts. Validate worker bearer tokens and worker identity separately; never accept arbitrary endpoint URLs or Docker configuration from requests.

## Approvals and idempotency

Plan creation resolves catalog identifiers to immutable server-owned manifests. A canonical JSON hash binds the selected profile, suite/tasks, candidates (including effective sampling), effective budgets, trial counts, scope and execution conditions. Execution conditions contain the resolved prompt snapshot digest and policy version, one seed per trial (null for unsupported controls), network policy and normalization version. Attempt manifests copy these approved conditions and record the actual task prompt hash; policy edits require a fresh approval. Approvals bind that hash and expire after 30 minutes. Dispatch atomically validates approval, hash, expiry, ownership and allowances and reserves the entire maximum usage. Edits/invalidation require a new plan and approval. Requested attempts equal tasks × candidates × trials; retries require separate remaining reserves.

Required Idempotency-Key values are UUIDs, scoped to owner/worker plus operation and retained for 24 hours. Identical body replay returns the original response; changed body returns 409. Rate-limit responses return 429 and Retry-After. Lists use opaque cursors and limits 1–100. Errors include stable code, safe message and request ID; no stack traces, source content, credentials or internal paths.

## Worker leases

Claim one eligible attempt atomically with PostgreSQL row locking; return 204 when none is available. Initial lease is 60 seconds; heartbeat every 15 seconds. Progress sequence numbers increase monotonically. Heartbeat, progress, artifact submission and completion bind worker, attempt, lease and fencing token. Expired/stale/mismatched tokens return 409, including after reassignment. Cancellation is reported through heartbeat and experiment status; worker stops on lost lease or API disconnection before starting another inference call. Completion is atomic and idempotent. Workers never hold database credentials.

Separate run IDs from attempt IDs. Run detail may select a historical attempt; absent selection returns the latest attempt, never a synthetic merged attempt. Only infrastructure failure permits one retry, with a new attempt ID and separately enforced budgets. Benchmark task failures, timeouts, cancellations and exhausted allowances do not retry automatically.

## Evidence and publication

Known metrics require value, source, unit and artifact IDs. Unknown metrics require null and a missing reason. Provider-reported money is distinct from estimates, credits or token counts. Artifact IDs resolve through owner/published access checks to short-lived downloads; storage paths remain internal. Uploads are bounded and SHA-256 verified before completion. Publication requires global scope, verified configuration, grading evidence, comparable cohorts and passed redaction; personal runs cannot be relabeled as global.

Recommendations name both harness and model. All decision inputs/outputs are versioned; preference edits produce new recommendations over the same immutable evidence. Fallback engine labels and reasons are mandatory. Uncalibrated distributions, calibrated decision probabilities, metric dispersion and evidence coverage have distinct fields/labels.
