# 06: Build one curated isolated grading fixture

Status: planned
Dependencies: [02](02-preflight.md)
Specification: [docs/specs/03-execution.md](../../../docs/specs/03-execution.md)

## Scope

Implement and validate the contract in the linked specification. Preserve public/personal separation, immutable evidence, approved limits and unknown metric values. No completion claim is valid without linked evidence.

## Acceptance criteria

- [ ] Pin fixture snapshot/base SHA and image digest with visible tests, protected grader and verified reference fix.
- [ ] Enforce non-root, dropped capabilities, no privileged mode/socket/secrets, bounded resources and default-deny egress.
- [ ] Separate coding agent from grader; collect normalized patch, source/artifact hashes, logs and structured objective grade.

## Given / When / Then scenarios

- Given malicious code requests host credentials/socket, when run, then access fails.
- Given an intentionally passing/failing patch, when grading runs, then objective expected outcomes are reproduced.
- Given denied egress or resource exhaustion, when observed, then outcome and cleanup are retained.

## Required validation

Real Docker passing/failing fixtures; network/host mount/secrets/grader access denial; CPU/memory/PIDs/disk/timeout limits and cleanup checks.

## Validation commands

Run in the locked Python environment: `python -m pytest tests/runner/test_isolation.py tests/runner/test_grading.py`.
The named test modules are implementation targets; create them with meaningful acceptance tests before completing this ticket. Missing modules are not passing evidence.
For product workflows, add API/database integration and browser acceptance checks required by the linked specification. Record commands, actual outcomes and evidence paths; mocked provider responses establish contract handling only.

## Evidence and completion

- Implementation: pending.
- Automated checks: pending; record command, outcome and relevant report path.
- Live probe/artifacts where required: pending; blocked prerequisites do not count as passing.
- Review: pending; retain failed outcomes and limitations.

Mark complete only after every acceptance criterion and required scenario has evidence. Do not present fixtures, target configuration, installed packages or source pins as measured runtime success.

