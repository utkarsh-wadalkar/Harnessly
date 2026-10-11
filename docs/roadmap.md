# Dependency-ordered roadmap

All tickets start **planned**. A ticket becomes complete only with its acceptance evidence and required tests linked. Preflight implementation is being handled separately; live Docker/WSL/provider-dependent work remains gated by actual prerequisite validation.

| Ticket | Deliverable | Dependencies |
| --- | --- | --- |
| 01 | Planning contracts and traceability | — |
| 02 | Windows/Docker/provider preflight | 01 |
| 03 | Local CPU LAYA service probe | 02 |
| 04 | LAYA evaluation and confidence gates | 03 |
| 05 | Hosted Gemma feasibility probe | 01 |
| 06 | Safe curated fixture and grading boundary | 02 |
| 07 | OpenCode same-model adapter probe | 06 |
| 08 | Aider same-model adapter probe | 07 |
| 09 | Interview and confirmed profile flow | 05 |
| 10 | Immutable approval and manifest contract | 06, 09 |
| 11 | PostgreSQL fenced leases | 10 |
| 12 | Recovery, cancellation and cleanup | 11 |
| 13 | Local live experiment viewer | 08, 12 |
| 14 | Evidence-bound LAYA recommendations | 04, 13 |
| 15 | Reviewed public replay publication | 13 |
| 16 | Ten-task curated pack | 06 |
| 17 | Repeated trials and uncertainty | 13, 16 |
| 18 | Release and challenge evidence | 14, 15, 17 |

Tickets are local Markdown files under [.scratch/harnessarena/issues](../.scratch/harnessarena/issues/01-planning.md). The critical path is feasibility → safe execution → approved durable runs → evidence viewer → evaluated recommendations and public replay → release. UI work uses labeled fixtures until live evidence is available; fixture data cannot be presented as benchmark results.

The MVP has no Redis, GPU, arbitrary repository intake, public LAYA deployment, live API tunnel or guaranteed free inference. Future enhancements require new decisions and cannot weaken the approved-plan or privacy boundaries.

