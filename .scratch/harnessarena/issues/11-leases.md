# 11: Add durable PostgreSQL fenced worker leases

Status: planned
Dependencies: [10](10-approval.md)
Specification: [docs/specs/03-execution.md](../../../docs/specs/03-execution.md)

## Scope

Implement and validate the contract in the linked specification. Preserve public/personal separation, immutable evidence, approved limits and unknown metric values. No completion claim is valid without linked evidence.

## Acceptance criteria

- [ ] Use PostgreSQL transactional claims with expiry and monotonic fencing tokens; no Redis.
- [ ] Support outbound worker claim/renew/finalize with scoped authentication and bounded polling.
- [ ] Require current fencing token for writes; ensure idempotent finalization and durable attempt history.

## Given / When / Then scenarios

- Given two concurrent workers, when claiming one run, then only one valid lease owns it.
- Given expired lease A replaced by B, when A renews/finalizes, then writes are rejected.
- Given a repeated valid finalize, when called, then evidence is not duplicated.

## Required validation

Real PostgreSQL concurrency/expiry/fencing tests; transaction rollback, renewal and idempotent finalize integration; worker credential scope checks.

## Validation commands

Run in the locked Python environment: `python -m pytest tests/integration/test_worker_leases.py`.
The named test modules are implementation targets; create them with meaningful acceptance tests before completing this ticket. Missing modules are not passing evidence.
For product workflows, add API/database integration and browser acceptance checks required by the linked specification. Record commands, actual outcomes and evidence paths; mocked provider responses establish contract handling only.

## Evidence and completion

- Implementation: pending.
- Automated checks: pending; record command, outcome and relevant report path.
- Live probe/artifacts where required: pending; blocked prerequisites do not count as passing.
- Review: pending; retain failed outcomes and limitations.

Mark complete only after every acceptance criterion and required scenario has evidence. Do not present fixtures, target configuration, installed packages or source pins as measured runtime success.

