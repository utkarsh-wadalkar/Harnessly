# 04: Evaluate LAYA typed decisions and calibration

Status: planned
Dependencies: [03](03-laya-server.md)
Specification: [docs/specs/04-decision.md](../../../docs/specs/04-decision.md)

## Scope

Implement and validate the contract in the linked specification. Preserve public/personal separation, immutable evidence, approved limits and unknown metric values. No completion claim is valid without linked evidence.

## Acceptance criteria

- [ ] Create/freeze 120 manually labeled cases with disjoint 40 development/40 calibration/40 test splits.
- [ ] Evaluate frozen threshold on held-out cases; report accuracy, accepted coverage, swap consistency, raw denominators and uncertainty.
- [ ] Require ≥90% accepted accuracy, ≥50% coverage and ≥95% swap consistency; suppress confidence claims until calibration evidence exists.

## Given / When / Then scenarios

- Given held-out labels, when tuning is requested, then test cases remain unavailable for development tuning.
- Given abstention, when metrics calculate, then it reduces coverage while staying out of accepted accuracy.
- Given a failed gate, when LAYA is enabled, then central selection remains gated and fallback is labeled.

## Required validation

Test split integrity, metric denominators and exact gate boundaries; run reproducible live held-out evaluation with error/cycle/swap analysis.

## Validation commands

Run in the locked Python environment: `python -m pytest tests/integration/test_laya_evaluation.py`.
The named test modules are implementation targets; create them with meaningful acceptance tests before completing this ticket. Missing modules are not passing evidence.
For product workflows, add API/database integration and browser acceptance checks required by the linked specification. Record commands, actual outcomes and evidence paths; mocked provider responses establish contract handling only.

## Evidence and completion

- Implementation: pending.
- Automated checks: pending; record command, outcome and relevant report path.
- Live probe/artifacts where required: pending; blocked prerequisites do not count as passing.
- Review: pending; retain failed outcomes and limitations.

Mark complete only after every acceptance criterion and required scenario has evidence. Do not present fixtures, target configuration, installed packages or source pins as measured runtime success.

