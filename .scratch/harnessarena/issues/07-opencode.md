# 07: Probe OpenCode on shared Qwen model

Status: planned
Dependencies: [06](06-safe-fixture.md)
Specification: [docs/specs/03-execution.md](../../../docs/specs/03-execution.md)

## Scope

Implement and validate the contract in the linked specification. Preserve public/personal separation, immutable evidence, approved limits and unknown metric values. No completion claim is valid without linked evidence.

## Acceptance criteria

- [ ] Implement/validate prepare, execute, collect_artifacts and terminate contract for pinned OpenCode version.
- [ ] Use hosted Qwen3-Coder-30B-A3B-Instruct with verified provider gate and explicit prompt/tool/sampling/budget conditions.
- [ ] Run the safe fixture and record patch, trace, usage coverage, grader results and capability limitations.

## Given / When / Then scenarios

- Given a pinned fixture and authorized endpoint, when OpenCode runs, then model/version/conditions match its manifest.
- Given timeout or provider failure, when execution stops, then partial evidence and termination outcome remain.
- Given unsupported sampling/seed controls, when comparison is planned, then limitations are disclosed.

## Required validation

Adapter contract mocks plus real isolated fixture probe and independent grading; verify credential boundary and termination.

## Validation commands

Run in the locked Python environment: `python -m pytest tests/integration/test_opencode_adapter.py`.
The named test modules are implementation targets; create them with meaningful acceptance tests before completing this ticket. Missing modules are not passing evidence.
For product workflows, add API/database integration and browser acceptance checks required by the linked specification. Record commands, actual outcomes and evidence paths; mocked provider responses establish contract handling only.

## Evidence and completion

- Implementation: pending.
- Automated checks: pending; record command, outcome and relevant report path.
- Live probe/artifacts where required: pending; blocked prerequisites do not count as passing.
- Review: pending; retain failed outcomes and limitations.

Mark complete only after every acceptance criterion and required scenario has evidence. Do not present fixtures, target configuration, installed packages or source pins as measured runtime success.

