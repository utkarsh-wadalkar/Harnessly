# Spec 08: Release evidence and traceability

Release requires public GitHub, runnable documented demo/replay, Apache-2.0 for original code subject to dependency/model license review, third-party notices, README, CONTRIBUTING, architecture/ADRs, fixture pack, example non-personal profiles, reproduction instructions, limitations, contributor issues and CI evidence. Original work includes contracts/orchestration/adapters/evidence/decision design; adapted work must be attributed. Do not ship untested Agent Skills or decorative AI claims.

Organizer source: [challenge](https://www.mlh.com/events/hacktoberfest-hack-day-pune-x-fair/challenges/01a0d987-0c41-12ea-13ac-5b85755dc2f3). Its URL says Pune and the page text says Mumbai; document the discrepancy. Recorded deadline: October 11, 2026, 5 PM IST. Submission evidence must identify meaningful open-source engineering and real AI behavior, public repository/license and honest limits. Provider proof and model use must be recorded, not inferred from configuration.

## PRD traceability

| PRD section | Specification / decision | Tickets |
| --- | --- | --- |
| 1 Executive summary | 02 preferences; 04 central typed selection; ADR 004 | 01, 09, 14 |
| 2 Problem/users/jobs | 02, 05, 06 | 09, 13–14, 16–17 |
| 3 Goals/non-goals/metrics | 01–08; ten-task curated scope | 01–18 |
| 4 Product flow | 02 approval; 03 execution; 04 decision; 06 evidence | 09–14 |
| 5.1 Gemma interview | 01 provider gate; 02 | 05, 09 |
| 5.2 Decision/LAYA | 04; ADR 003–004 implements central selection role | 03–04, 14 |
| 5.3 Adapters/execution | 03; ADR 001–002 | 06–08, 10–13 |
| 5.4 Tasks/statistics | 05 | 16–17 |
| 5.5 Dashboard | 06 | 13–15 |
| 5.6 Auth/privacy/operations | 07 | 10–13, 15 |
| 6 Ranking contract | 04; explicit evidence/constraints remain authoritative | 04, 14 |
| 7 Data model | domain.md; 02–04, 07 | 09–12, 14–15 |
| 8 Architecture/API | architecture.md; ADR 001–003; /api/v1 | 02–03, 09–13, 15 |
| 9 Safety/fairness/reproducibility | 03, 05, 07 | 06–08, 10–12, 15–17 |
| 10 Delivery plan | roadmap.md; all specs | 01–18 |
| 11 Automated tests | each spec's required validation | 02–18 |
| 12 Open source/submission | 08 | 01, 15–18 |
| 13 Open questions | 01 probes; ADR 001–005; risks.md | 02–08, 16–18 |
| 14 References | source attribution/license review and probe evidence | 01, 03–05, 07–08, 18 |
| 15 Challenge verification and delivery status | 08; research/integrations.md; engineering/progress.md | 01, 05, 18 |

## Explicit PRD refinements

Amended PRD v1.1 records the refinements from the original §8 proposals: PostgreSQL leases, local Windows/WSL2 CPU execution, loopback CPU LAYA and local artifacts/static public replay replace Redis, remote worker, optional GPU and S3 assumptions. Next.js is a future frontend target. §5.2 now requires evidence-bound central candidate selection with a labeled deterministic fallback; §6 deterministic normalization/constraints/measurement authority remain intact. §3/§5.4 task range is concretized as ten tasks, four families, two languages and three trials per pair. Arbitrary repositories, public LAYA and API tunnels are excluded. Hosted model targets and free-tier eligibility require live evidence.

## Completion scenario

Given all dependent tickets have actual evidence, when release is reviewed, then required tests, model probes, repeated trials, privacy checks, license notices and public replay are linked. Given any missing prerequisite or synthetic fixture-only result, when submission materials are prepared, then limitations are explicit and no completed/live benchmark claim is made.

