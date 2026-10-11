# HarnessArena engineering instructions

Use [GLOSSARY.md](GLOSSARY.md) for domain terms. Before changing behavior, read its ticket under [.scratch/harnessarena/issues](.scratch/harnessarena/issues/01-planning.md) and linked spec. Before changing a public interface, read [API contract rules](docs/engineering/api-contracts.md). Before changing execution or inference, read [architecture](docs/architecture.md) and [risks](docs/risks.md).

## Work sequence

1. Find the next ticket whose dependencies are complete in [roadmap](docs/roadmap.md); preserve unrelated changes.
2. Implement one observable acceptance scenario at a time with Matt Pocock's `implement-spec`, `tdd`, then `code-review` workflow. Write a failing behavior test through the agreed workflow/adapter interface, implement to green, and retain red/green evidence.
3. Run the ticket's checks and validate every acceptance criterion. Review both specification compliance and engineering quality. Record commands/results and blockers in [progress](docs/engineering/progress.md).
4. Update the ticket only after its evidence passes. Live prerequisites require live evidence; mocks validate handling, not integration feasibility.

## Invariants

- Recommendations specify both harness and model. LAYA consumes confirmed preferences and actual measurements; deterministic preprocessing enforces constraints. Label baseline/fallback decisions with their cause and keep uncalibrated probabilities separate from reliability claims.
- Unknown metrics stay null with a missing reason. Every measured value references evidence. Preference changes create recommendations, leaving benchmark evidence immutable.
- Keep personal and verified global cohorts separate. Public artifacts require redaction and explicit maintainer publication.
- Bind dispatch to an approved immutable plan and enforce request/token/resource allowances. Worker writes require current lease fencing tokens.
- Curated task containers run separately from LAYA/grader/control modules, without host secrets, privileged access or Docker sockets. The trusted worker alone controls Docker.
- Live inference requires credentials and verified allowance/eligibility. Provider tokens remain in ignored local configuration; reports contain presence flags and safe error codes only.

## Ownership and tools

Generate public schemas from `packages/contracts/models.py`; `python -m scripts.export_contracts --check` detects drift. Generated HTTP operations are design contracts until workflow tickets implement them. Read [dependency policy](docs/engineering/dependencies.md) when updating versions or image/checkpoint pins.

Use scoped subagents for independent work with explicit file ownership; choose cheaper models for bounded mechanical tasks. Avoid duplicate reviews/tests. This repository's runtime prohibits git commits. Do not commit, push, publish external issues or submit a challenge unless a later governing instruction permits that operation.

When a task actually needs Utkarsh's personal history, first read `D:\ALL Programming\obsidian_mem\chatgpt-to-obsidian\utkarsh-vault\AGENTS.md`; project requirements alone do not require that vault.
