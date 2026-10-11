# 08: Probe Aider under comparable conditions

Status: planned
Dependencies: [07](07-opencode.md)
Specification: [docs/specs/03-execution.md](../../../docs/specs/03-execution.md)

## Scope

Implement and validate the contract in the linked specification. Preserve public/personal separation, immutable evidence, approved limits and unknown metric values. No completion claim is valid without linked evidence.

## Acceptance criteria

- [ ] Implement/validate the same adapter contract for pinned Aider version.
- [ ] Use the identical hosted Qwen3-Coder-30B-A3B-Instruct endpoint and same fixture/budget conditions as OpenCode.
- [ ] Record differing prompts/tools/approval capabilities and mark noncomparable conditions explicitly.

## Given / When / Then scenarios

- Given OpenCode fixture conditions, when Aider runs, then shared model and fixture identities match.
- Given capability differences, when results compare, then differences are visible rather than claiming full equality.
- Given provider or harness failure, when collected, then classification and partial artifacts remain distinct.

## Required validation

Contract mocks; real Aider fixture run/grade; cross-adapter manifest comparison and capability-difference checks.

## Validation commands

Run in the locked Python environment: `python -m pytest tests/integration/test_aider_adapter.py`.
The named test modules are implementation targets; create them with meaningful acceptance tests before completing this ticket. Missing modules are not passing evidence.
For product workflows, add API/database integration and browser acceptance checks required by the linked specification. Record commands, actual outcomes and evidence paths; mocked provider responses establish contract handling only.

## Evidence and completion

- Implementation: pending.
- Automated checks: pending; record command, outcome and relevant report path.
- Live probe/artifacts where required: pending; blocked prerequisites do not count as passing.
- Review: pending; retain failed outcomes and limitations.

Mark complete only after every acceptance criterion and required scenario has evidence. Do not present fixtures, target configuration, installed packages or source pins as measured runtime success.

