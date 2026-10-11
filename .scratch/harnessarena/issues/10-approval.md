# 10: Freeze approved plans and run manifests

Status: planned
Dependencies: [06](06-safe-fixture.md), [09](09-profile-flow.md)
Specification: [docs/specs/02-preferences-approval.md](../../../docs/specs/02-preferences-approval.md)

## Scope

Implement and validate the contract in the linked specification. Preserve public/personal separation, immutable evidence, approved limits and unknown metric values. No completion claim is valid without linked evidence.

## Acceptance criteria

- [ ] Expose versioned /api/v1 schemas for plan/approval/dispatch and generated OpenAPI.
- [ ] Bind exact profile/task/candidate/model/image/conditions/trials/limits to plan digest and approval owner/expiry.
- [ ] Persist immutable manifests and idempotent atomic dispatch; require reapproval after any effective change.

## Given / When / Then scenarios

- Given edited budget/task/model/profile, when dispatch uses old approval, then it is rejected.
- Given expired or another user's approval, when submitted, then dispatch is denied.
- Given duplicate dispatch keys, when requests race, then one experiment is created.

## Required validation

API/DB migration integration; digest/immutability/expiry/owner tests; concurrent idempotency and prompt-injection configuration tests.

## Validation commands

Run in the locked Python environment: `python -m pytest tests/integration/test_approved_plans.py`.
The named test modules are implementation targets; create them with meaningful acceptance tests before completing this ticket. Missing modules are not passing evidence.
For product workflows, add API/database integration and browser acceptance checks required by the linked specification. Record commands, actual outcomes and evidence paths; mocked provider responses establish contract handling only.

## Evidence and completion

- Implementation: pending.
- Automated checks: pending; record command, outcome and relevant report path.
- Live probe/artifacts where required: pending; blocked prerequisites do not count as passing.
- Review: pending; retain failed outcomes and limitations.

Mark complete only after every acceptance criterion and required scenario has evidence. Do not present fixtures, target configuration, installed packages or source pins as measured runtime success.

