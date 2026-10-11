# 01: Planning contracts and traceability

Status: planned
Dependencies: None
Specification: [docs/specs/08-release-traceability.md](../../../docs/specs/08-release-traceability.md)

## Scope

Implement and validate the contract in the linked specification. Preserve public/personal separation, immutable evidence, approved limits and unknown metric values. No completion claim is valid without linked evidence.

## Acceptance criteria

- [ ] Read amended PRD v1.1 and record accepted architecture refinements without silently rewriting requirements.
- [ ] Provide shared glossary, domain invariants, architecture, ADRs, risks, roadmap and section-level PRD traceability.
- [ ] Create all 18 dependency-ordered local tickets with scenarios, validation requirements and honest status.

## Given / When / Then scenarios

- Given the PRD, when documentation is reviewed, then every numbered section and requirement subsection maps to a spec and ticket.
- Given original architecture suggestions, when accepted decisions differ, then the override and tradeoff are explicit.

## Required validation

Check links, dependency order, consistent model/endpoint names and absence of fabricated implementation or benchmark claims.

## Validation commands

Run in the locked Python environment: `python -m pytest tests/integration/test_contracts.py tests/integration/test_planning_package.py`.
Additional check/probe: `python -m scripts.export_contracts --check; python -m scripts.validate_project; pnpm contracts:check`. Live probes fail closed without validated prerequisites.
For product workflows, add API/database integration and browser acceptance checks required by the linked specification. Record commands, actual outcomes and evidence paths; mocked provider responses establish contract handling only.

## Evidence and completion

- Implementation: pending.
- Automated checks: pending; record command, outcome and relevant report path.
- Live probe/artifacts where required: pending; blocked prerequisites do not count as passing.
- Review: pending; retain failed outcomes and limitations.

Mark complete only after every acceptance criterion and required scenario has evidence. Do not present fixtures, target configuration, installed packages or source pins as measured runtime success.

