# 15: Publish reviewed static global replay

Status: planned
Dependencies: [13](13-live-viewer.md)
Specification: [docs/specs/07-privacy-publication.md](../../../docs/specs/07-privacy-publication.md)

## Scope

Implement and validate the contract in the linked specification. Preserve public/personal separation, immutable evidence, approved limits and unknown metric values. No completion claim is valid without linked evidence.

## Acceptance criteria

- [ ] Create explicit immutable publication of selected controlled global artifacts after redaction review.
- [ ] Serve public recorded leaderboard/replay independently of local API with no tunnel.
- [ ] Exclude personal data/private runs; show capture date, provenance, missing coverage and limitations.

## Given / When / Then scenarios

- Given secret-bearing log, when publication requested, then redaction/review blocks unsafe export.
- Given personal run, when global publication requested, then it is rejected.
- Given local API down, when public replay loads, then recorded evidence remains inspectable without local requests.

## Required validation

Secret/identity/private-artifact fixtures; anonymous/owner checks; immutable publication/segregation integration; public build network/data inspection.

## Validation commands

Run in the locked Python environment: `python -m pytest tests/integration/test_publication.py`.
The named test modules are implementation targets; create them with meaningful acceptance tests before completing this ticket. Missing modules are not passing evidence.
For product workflows, add API/database integration and browser acceptance checks required by the linked specification. Record commands, actual outcomes and evidence paths; mocked provider responses establish contract handling only.

## Evidence and completion

- Implementation: pending.
- Automated checks: pending; record command, outcome and relevant report path.
- Live probe/artifacts where required: pending; blocked prerequisites do not count as passing.
- Review: pending; retain failed outcomes and limitations.

Mark complete only after every acceptance criterion and required scenario has evidence. Do not present fixtures, target configuration, installed packages or source pins as measured runtime success.

