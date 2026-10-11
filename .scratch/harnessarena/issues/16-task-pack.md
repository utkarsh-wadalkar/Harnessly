# 16: Validate ten-task curated global pack

Status: planned
Dependencies: [06](06-safe-fixture.md)
Specification: [docs/specs/05-benchmarks.md](../../../docs/specs/05-benchmarks.md)

## Scope

Implement and validate the contract in the linked specification. Preserve public/personal separation, immutable evidence, approved limits and unknown metric values. No completion claim is valid without linked evidence.

## Acceptance criteria

- [ ] Create ten pinned TypeScript/Python tasks spanning all four bug/feature/test/refactor families.
- [ ] Provide metadata, setup, visible tests, protected graders and maintainer-verified reference fixes.
- [ ] Document distribution, contamination/overfitting risks and curated-only intake boundaries.

## Given / When / Then scenarios

- Given any reference fix, when grading runs, then acceptance passes.
- Given intentionally failing patch, when grading runs, then rejection is objective.
- Given unpinned or arbitrary task, when global intake is requested, then it is refused.

## Required validation

Run every reference fix and failing fixture; manifest/hash validation; protected-grader access and family/language coverage checks.

## Validation commands

Run in the locked Python environment: `python -m pytest tests/runner/test_curated_pack.py`.
The named test modules are implementation targets; create them with meaningful acceptance tests before completing this ticket. Missing modules are not passing evidence.
For product workflows, add API/database integration and browser acceptance checks required by the linked specification. Record commands, actual outcomes and evidence paths; mocked provider responses establish contract handling only.

## Evidence and completion

- Implementation: pending.
- Automated checks: pending; record command, outcome and relevant report path.
- Live probe/artifacts where required: pending; blocked prerequisites do not count as passing.
- Review: pending; retain failed outcomes and limitations.

Mark complete only after every acceptance criterion and required scenario has evidence. Do not present fixtures, target configuration, installed packages or source pins as measured runtime success.

