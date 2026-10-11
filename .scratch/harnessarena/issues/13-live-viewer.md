# 13: Deliver local live experiment inspection

Status: planned
Dependencies: [08](08-aider.md), [12](12-recovery.md)
Specification: [docs/specs/06-dashboard.md](../../../docs/specs/06-dashboard.md)

## Scope

Implement and validate the contract in the linked specification. Preserve public/personal separation, immutable evidence, approved limits and unknown metric values. No completion claim is valid without linked evidence.

## Acceptance criteria

- [ ] Provide future Next.js local views of experiment status, timeline, patch, logs, grades and manifest downloads.
- [ ] Link each result to immutable run/configuration/metric/grading evidence and show unknown coverage.
- [ ] Support scoped expiring quota-limited invited-judge sessions; distinguish live/unavailable/recorded states.

## Given / When / Then scenarios

- Given completed run, when opening score, then configuration and grading evidence are reachable.
- Given missing metrics or unavailable worker, when rendered, then truthful unknown/unavailable states appear.
- Given exhausted/expired judge session, when dispatch is requested, then calls are denied.

## Required validation

Live status/cancel/download E2E; quota/expiry/private authorization; keyboard/mobile/high-contrast and loading/empty/error checks.

## Validation commands

Run in the locked Python environment: `python -m pytest tests/integration/test_comparison_evidence.py`.
The named test modules are implementation targets; create them with meaningful acceptance tests before completing this ticket. Missing modules are not passing evidence.
For product workflows, add API/database integration and browser acceptance checks required by the linked specification. Record commands, actual outcomes and evidence paths; mocked provider responses establish contract handling only.

## Evidence and completion

- Implementation: pending.
- Automated checks: pending; record command, outcome and relevant report path.
- Live probe/artifacts where required: pending; blocked prerequisites do not count as passing.
- Review: pending; retain failed outcomes and limitations.

Mark complete only after every acceptance criterion and required scenario has evidence. Do not present fixtures, target configuration, installed packages or source pins as measured runtime success.

