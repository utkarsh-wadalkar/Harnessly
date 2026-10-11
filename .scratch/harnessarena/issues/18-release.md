# 18: Release reproducible public project and challenge evidence

Status: planned
Dependencies: [14](14-recommendations.md), [15](15-public-publish.md), [17](17-repeats.md)
Specification: [docs/specs/08-release-traceability.md](../../../docs/specs/08-release-traceability.md)

## Scope

Implement and validate the contract in the linked specification. Preserve public/personal separation, immutable evidence, approved limits and unknown metric values. No completion claim is valid without linked evidence.

## Acceptance criteria

- [ ] Publish documented runnable project/replay with README, CONTRIBUTING, architecture/ADRs, examples, fixture pack, reproduction and contributor issues.
- [ ] Complete Apache-2.0 original-code license/dependency/model review and attribution/third-party notices.
- [ ] Link CI/tests, actual AI/model probes, calibration, repeated-run and privacy evidence; document source discrepancy/deadline and unresolved limits.

## Given / When / Then scenarios

- Given missing live probe or benchmark evidence, when preparing submission, then materials explicitly disclose the gap.
- Given release audit, when checking claims, then each score and model-use claim links to actual evidence.
- Given adapted code/dependencies, when license audit runs, then compatible notices and attribution exist.

## Required validation

Clean-environment reproduction; required unit/integration/runner/E2E suite; public replay inspection, secret/license audit and complete release evidence checklist.

## Validation commands

Run in the locked Python environment: `python -m pytest tests/integration/test_release_reproduction.py`.
The named test modules are implementation targets; create them with meaningful acceptance tests before completing this ticket. Missing modules are not passing evidence.
For product workflows, add API/database integration and browser acceptance checks required by the linked specification. Record commands, actual outcomes and evidence paths; mocked provider responses establish contract handling only.

## Evidence and completion

- Implementation: pending.
- Automated checks: pending; record command, outcome and relevant report path.
- Live probe/artifacts where required: pending; blocked prerequisites do not count as passing.
- Review: pending; retain failed outcomes and limitations.

Mark complete only after every acceptance criterion and required scenario has evidence. Do not present fixtures, target configuration, installed packages or source pins as measured runtime success.

