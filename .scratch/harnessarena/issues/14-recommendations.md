# 14: Select candidates using evaluated LAYA and real metrics

Status: planned
Dependencies: [04](04-laya-eval.md), [13](13-live-viewer.md)
Specification: [docs/specs/04-decision.md](../../../docs/specs/04-decision.md)

## Scope

Implement and validate the contract in the linked specification. Preserve public/personal separation, immutable evidence, approved limits and unknown metric values. No completion claim is valid without linked evidence.

## Acceptance criteria

- [ ] Preprocess confirmed preferences and real comparable metrics deterministically; apply constraints, polarity, ranges and missing-data rules. Missing positively weighted evidence yields insufficient evidence; never redistribute weights.
- [ ] Use LAYA finite pairwise A/B/equivalent/insufficient outputs across at most eight eligible candidates: at most 28 unordered pairs and 56 calls including reversed checks.
- [ ] Show source-linked rationale, partial orders/cycles and labeled baseline fallback; confidence requires passing calibration evidence.

## Given / When / Then scenarios

- Given explicit constraint or failed grading, when LAYA favors candidate, then authoritative exclusion/outcome remains.
- Given cyclic/swap-inconsistent or unavailable LAYA output, when displayed, then partial/uncertain/fallback is labeled.
- Given preference edit with adequate coverage, when reranked, then stored observations remain unchanged.

## Required validation

Weight/constraint/tie/polarity/missing/monotonicity tests; malformed/timeout/cycle/swap mocks; comparison-cap checks; provenance E2E with actual evaluated service.

## Validation commands

Run in the locked Python environment: `python -m pytest tests/integration/test_recommendations.py`.
The named test modules are implementation targets; create them with meaningful acceptance tests before completing this ticket. Missing modules are not passing evidence.
For product workflows, add API/database integration and browser acceptance checks required by the linked specification. Record commands, actual outcomes and evidence paths; mocked provider responses establish contract handling only.

## Evidence and completion

- Implementation: pending.
- Automated checks: pending; record command, outcome and relevant report path.
- Live probe/artifacts where required: pending; blocked prerequisites do not count as passing.
- Review: pending; retain failed outcomes and limitations.

Mark complete only after every acceptance criterion and required scenario has evidence. Do not present fixtures, target configuration, installed packages or source pins as measured runtime success.

