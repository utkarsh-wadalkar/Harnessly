# 02: Validate local runtime and provider gates

Status: planned
Dependencies: [01](01-planning.md)
Specification: [docs/specs/01-preflight.md](../../../docs/specs/01-preflight.md)

## Scope

Implement and validate the contract in the linked specification. Preserve public/personal separation, immutable evidence, approved limits and unknown metric values. No completion claim is valid without linked evidence.

## Acceptance criteria

- [ ] Record bounded secret-safe readiness results for Windows 11, WSL2, Docker Desktop/CLI, PostgreSQL and CPU/memory capability.
- [ ] Separate installed/configured/readable from engine-running and tested; never treat a missing CLI as a passing Docker probe.
- [ ] Block hosted calls until credentials, actual eligibility and effective usage/spend caps are verified.

## Given / When / Then scenarios

- Given no Docker CLI, when preflight executes, then Docker execution is blocked with the failed check recorded.
- Given WSL distributions are stopped, when inventory succeeds, then availability is recorded separately from active engine readiness.
- Given absent provider credentials, when preflight runs, then no inference call is made.

## Required validation

Unit-test readiness states and redaction; mock denied/unavailable dependencies; record real Docker CLI/engine and resource-limit smoke-test evidence.

## Validation commands

Run in the locked Python environment: `python -m pytest tests/runner/test_preflight.py`.
Additional check/probe: `python -m apps.worker.preflight`. Live probes fail closed without validated prerequisites.
For product workflows, add API/database integration and browser acceptance checks required by the linked specification. Record commands, actual outcomes and evidence paths; mocked provider responses establish contract handling only.

## Evidence and completion

- Implementation: pending.
- Automated checks: pending; record command, outcome and relevant report path.
- Live probe/artifacts where required: pending; blocked prerequisites do not count as passing.
- Review: pending; retain failed outcomes and limitations.

Mark complete only after every acceptance criterion and required scenario has evidence. Do not present fixtures, target configuration, installed packages or source pins as measured runtime success.

