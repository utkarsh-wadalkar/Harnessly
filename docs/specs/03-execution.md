# Spec 03: Controlled execution and recovery

## Adapter contract

Each adapter implements prepare(config), execute(task, model, budgets), collect_artifacts() and terminate(). It reports installed harness/adapter versions and exact model/provider details. OpenCode is probed first, then Aider against identical Qwen endpoint and fixture conditions; differing tools and prompts are disclosed.

## Isolation and evidence

Only curated pinned fixtures may run. Fresh containers are non-root, unprivileged, capability-dropped and bounded by CPU/memory/PIDs/disk/time. No Docker socket, host credentials, hidden grader or broad host mount is available. Default-deny egress allows only a credential-holding controlled model proxy where required. Protected grading runs independently after patch collection.

Manifests pin source SHA, task/grader versions, image digest, harness/adapter/model, sampling support, trial/attempt, prompt policy, network and effective budgets. Artifacts contain patch, bounded stdout/stderr, structured grade, source hashes, metrics and telemetry coverage. Killed runs are distinct from task failure.

## Durable ownership

PostgreSQL transactional claims produce lease expiry and monotonic fencing token. Claim, renew and finalize are idempotent and reject stale tokens. Worker requests are outbound; no inbound Docker access is exposed. Infrastructure retry creates a distinct attempt; task failures are not silently retried. Recovery cleans orphan resources before another attempt. Cancellation prevents new claims and requests termination of owned work while preserving partial logs.

The generated OpenAPI contract names these operations `POST /api/v1/workers/claim`, `POST /api/v1/attempts/{attempt_id}/heartbeat` (lease renewal), `POST /api/v1/attempts/{attempt_id}/progress`, `POST /api/v1/attempts/{attempt_id}/artifacts` and `POST /api/v1/attempts/{attempt_id}/complete` (finalization). `packages/contracts/generated/openapi.json` is authoritative; lifecycle terms such as renew/finalize are not alternative endpoint routes.

## Acceptance scenarios

- Given hostile fixture code, when it requests host secrets/socket or disallowed egress, then access is denied and an auditable policy outcome appears.
- Given expired lease A and new lease B, when A submits completion, then no terminal evidence can be overwritten.
- Given worker crash, when recovery runs, then orphan cleanup and a distinct retry attempt are recorded.
- Given timeout/cancel, when the container stops, then partial artifacts remain and cleanup is verifiable.
- Given forged agent test claims, when independent grading runs, then objective grader evidence determines the result.

## Required validation

Real isolation/egress/credential/grader-separation tests; passing and failing fixture tests; concurrent claim/finalize integration; stale fencing, retry, cancellation, crash and cleanup scenarios. Tests requiring unavailable Docker cannot count as passed.

