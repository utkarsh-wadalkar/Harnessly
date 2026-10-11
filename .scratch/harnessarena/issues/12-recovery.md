# 12: Recover crashes and enforce cancellation/cleanup

Status: planned
Dependencies: [11](11-leases.md)
Specification: [docs/specs/03-execution.md](../../../docs/specs/03-execution.md)

## Scope

Implement and validate the contract in the linked specification. Preserve public/personal separation, immutable evidence, approved limits and unknown metric values. No completion claim is valid without linked evidence.

## Acceptance criteria

- [ ] Recover expired ownership and clean orphan containers before a distinct infrastructure retry attempt.
- [ ] Separate infrastructure retries from task/harness/provider failure; preserve previous attempt evidence.
- [ ] Cancel pending/running work with bounded termination, partial artifacts and verifiable cleanup.

## Given / When / Then scenarios

- Given worker death, when lease expires, then orphan cleanup precedes new attempt.
- Given task failure, when recovery runs, then no silent retry inflates success.
- Given cancellation or timeout, when termination completes, then correct terminal classification and partial logs remain.

## Required validation

Crash/restart integration with Docker/PostgreSQL; stale completion race; pending/running cancellation; timeout and idempotent cleanup tests.

## Validation commands

Run in the locked Python environment: `python -m pytest tests/runner/test_cancellation.py tests/integration/test_recovery.py`.
The named test modules are implementation targets; create them with meaningful acceptance tests before completing this ticket. Missing modules are not passing evidence.
For product workflows, add API/database integration and browser acceptance checks required by the linked specification. Record commands, actual outcomes and evidence paths; mocked provider responses establish contract handling only.

## Evidence and completion

- Implementation: pending.
- Automated checks: pending; record command, outcome and relevant report path.
- Live probe/artifacts where required: pending; blocked prerequisites do not count as passing.
- Review: pending; retain failed outcomes and limitations.

Mark complete only after every acceptance criterion and required scenario has evidence. Do not present fixtures, target configuration, installed packages or source pins as measured runtime success.

