# 05: Verify hosted Gemma interview feasibility

Status: planned
Dependencies: [01](01-planning.md)
Specification: [docs/specs/01-preflight.md](../../../docs/specs/01-preflight.md)

## Scope

Implement and validate the contract in the linked specification. Preserve public/personal separation, immutable evidence, approved limits and unknown metric values. No completion claim is valid without linked evidence.

## Acceptance criteria

- [ ] Verify Google AI Studio gemma-4-26b-a4b-it support, account credentials, terms/license and eligible quota before calls.
- [ ] Execute a non-personal structured interview/extraction fixture within verified caps.
- [ ] Record exact model/provider, request outcome, usage source, latency and cost only when observed/verifiable.

## Given / When / Then scenarios

- Given missing credentials or unknown free-tier eligibility, when a call is proposed, then no unverified call occurs.
- Given authorized configuration, when extraction runs, then required profile fields and evidence spans validate.
- Given provider refusal/unavailability, when the probe completes, then the failed outcome is recorded without fake usage.

## Required validation

Mock invalid/unavailable provider and extraction-schema errors; capture one real authorized fixture response and license/eligibility evidence without secrets.

## Validation commands

Run in the locked Python environment: `python -m pytest tests/integration/test_gemma_client.py`.
Additional check/probe: `python -m prototypes.gemma.probe --output .local/gemma-probe.json`. Live probes fail closed without validated prerequisites.
For product workflows, add API/database integration and browser acceptance checks required by the linked specification. Record commands, actual outcomes and evidence paths; mocked provider responses establish contract handling only.

## Evidence and completion

- Implementation: pending.
- Automated checks: pending; record command, outcome and relevant report path.
- Live probe/artifacts where required: pending; blocked prerequisites do not count as passing.
- Review: pending; retain failed outcomes and limitations.

Mark complete only after every acceptance criterion and required scenario has evidence. Do not present fixtures, target configuration, installed packages or source pins as measured runtime success.

