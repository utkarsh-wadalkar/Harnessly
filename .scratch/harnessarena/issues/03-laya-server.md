# 03: Probe official CPU LAYA service

Status: planned
Dependencies: [02](02-preflight.md)
Specification: [docs/specs/01-preflight.md](../../../docs/specs/01-preflight.md)

## Scope

Implement and validate the contract in the linked specification. Preserve public/personal separation, immutable evidence, approved limits and unknown metric values. No completion claim is valid without linked evidence.

## Acceptance criteria

- [ ] Pin official laya-serve source and a CPU-compatible typed-decision checkpoint with hashes; cache the model.
- [ ] Bind only 127.0.0.1:8001, with at most 2 CPUs/4 GiB and no GPU or public exposure.
- [ ] Capture startup/readiness, versions/device/resource observations and a valid finite-choice fixture response; retain failure evidence.

## Given / When / Then scenarios

- Given no usable Docker/runtime, when startup is requested, then the ticket stays blocked rather than claiming a service.
- Given a valid CPU runtime, when a typed fixture runs, then response labels satisfy schema and resource caps.
- Given load failure, when recommendation integration requests LAYA, then a labeled fallback is possible.

## Required validation

Run official service smoke test, invalid-label/timeout fixtures, loopback binding inspection and actual CPU/memory limit checks. Source pins alone are not runtime validation.

## Validation commands

Run in the locked Python environment: `python -m pytest tests/integration/test_laya_client.py`.
Additional check/probe: `python -m prototypes.laya.probe --output .local/laya-probe.json`. Live probes fail closed without validated prerequisites.
For product workflows, add API/database integration and browser acceptance checks required by the linked specification. Record commands, actual outcomes and evidence paths; mocked provider responses establish contract handling only.

## Evidence and completion

- Implementation: pending.
- Automated checks: pending; record command, outcome and relevant report path.
- Live probe/artifacts where required: pending; blocked prerequisites do not count as passing.
- Review: pending; retain failed outcomes and limitations.

Mark complete only after every acceptance criterion and required scenario has evidence. Do not present fixtures, target configuration, installed packages or source pins as measured runtime success.

