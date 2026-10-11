# Contributing

Start with [AGENTS.md](AGENTS.md), the [roadmap](docs/roadmap.md), and one unblocked local ticket. The repository is in feasibility development; improve evidence and tests without presenting planned workflows as completed features.

Run the README's validation commands in an isolated environment. Changes to contracts require regenerated OpenAPI/JSON Schema and drift validation. Use Given/When/Then acceptance scenarios and test public workflow or adapter behavior. Live integrations need separate evidence recorded without credentials, private source or personal profiles.

Open small reviews explaining resulting behavior, acceptance evidence and limits. Preserve existing state and interfaces unless a specification or ADR changes them. New harnesses need the same adapter contract tests, pinned provenance, budget controls and an independently graded fixture. New tasks need a failing clean snapshot and verified reference fix.

Original contributions use Apache-2.0; include attribution for adapted code and verify upstream licenses. Report security concerns privately to the repository owner instead of publishing secrets, exploitable host configuration or unredacted traces. No public arbitrary-repository execution is supported.
