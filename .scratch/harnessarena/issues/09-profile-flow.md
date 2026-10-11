# 09: Deliver editable confirmed preference profiles

Status: planned
Dependencies: [05](05-gemma-probe.md)
Specification: [docs/specs/02-preferences-approval.md](../../../docs/specs/02-preferences-approval.md)

## Scope

Implement and validate the contract in the linked specification. Preserve public/personal separation, immutable evidence, approved limits and unknown metric values. No completion claim is valid without linked evidence.

## Acceptance criteria

- [ ] Integrate Gemma adaptive interview and structured extraction with evidence spans and provenance.
- [ ] Support edits for answers/weights/constraints, finite normalized weights and review of high-impact inferred constraints.
- [ ] Version confirmed profiles; keep personal answers out of global prompts and logs/exports.

## Given / When / Then scenarios

- Given ambiguous must-have privacy intent, when inferred, then explicit constraint review is required.
- Given edits after confirmation, when saved, then a new version appears.
- Given invalid weights, when confirmed, then validation rejects them.

## Required validation

Extraction and normalization unit tests; endpoint mocks; edit/version/owner-access integration and interview-to-confirmation E2E.

## Validation commands

Run in the locked Python environment: `python -m pytest tests/integration/test_profile_workflow.py`.
The named test modules are implementation targets; create them with meaningful acceptance tests before completing this ticket. Missing modules are not passing evidence.
For product workflows, add API/database integration and browser acceptance checks required by the linked specification. Record commands, actual outcomes and evidence paths; mocked provider responses establish contract handling only.

## Evidence and completion

- Implementation: pending.
- Automated checks: pending; record command, outcome and relevant report path.
- Live probe/artifacts where required: pending; blocked prerequisites do not count as passing.
- Review: pending; retain failed outcomes and limitations.

Mark complete only after every acceptance criterion and required scenario has evidence. Do not present fixtures, target configuration, installed packages or source pins as measured runtime success.

