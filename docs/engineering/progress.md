# Implementation ledger — plan: docs/roadmap.md

Work is on `codex/harnessarena-foundation`. The runtime prohibits git commits; keep changes reviewable locally and use ticket evidence rather than commit-based completion. No pushes, merges, or external issue publication occur in this run.

## Preflight rulings

- Ruling: retain the existing checkout on the integration branch rather than creating agent worktrees — commits are prohibited and untracked planning files must remain available to collaborators — cost if wrong: less filesystem isolation; mitigate with explicit non-overlapping ownership and sequential implementation agents.
- Ruling: use native tools and persistent documentation for the subagent ledger/review packages — the skill's commit-range Bash helpers cannot capture uncommitted new files — cost if wrong: reviews may miss files; inventory tracked and untracked task-owned files explicitly.
- Ruling: validate locally on Python 3.13.3 and add CI for Python 3.11/3.13 — only 3.13 is installed — cost if wrong: 3.11 compatibility issues can remain until CI runs, and must not be claimed locally verified.

## Interface checks

| Producer → consumer | Shared interface | Decision |
| --- | --- | --- |
| 01 → all tickets | Glossary, contracts, specs | Use generated schemas; HTTP operations remain planned. |
| 02 → 03/06 | Host execution readiness | Fail closed; WSL inventory is not Docker daemon readiness. |
| 03 → 04 | Typed HTTP decisions | Pin source/checkpoint and prove CPU/device/cache before evaluation. |
| 04/13 → 14 | Evaluated selection and immutable evidence | LAYA stays gated by live evaluation; baseline is labeled. |
| 05 → 09 | Hosted Gemma extraction | Offline mocks cannot complete the live feasibility ticket. |
| 06/09 → 10 → 11/12 → 13 | Approval/manifest/lease/evidence | Dependencies remain as approved; no workflow is marked complete from a schema. |
| 13 → 15/17 → 18 | Public cohorts and repetitions | Public eligibility requires separate global runs and redaction. |

## Execution

- Task 01: in progress — docs and proposed contracts created; validation/review pending.
- Task 02: next — independently testable host preflight.
- Live integration evidence: none yet. WSL2 Ubuntu/docker-desktop distributions exist and are stopped; Docker CLI not on PATH or default install location. `.env` absent. No credential values searched or disclosed.
