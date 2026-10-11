# HarnessArena — Product Requirements Document

**Version:** 1.1 (local-first MVP)  
**Date:** 2026-10-11  
**Status:** Architecture specified; feasibility implementation in progress  
**License goal:** Apache-2.0 for original project code, subject to dependency/license review

## 1. Executive Summary

HarnessArena is an open-source platform that recommends AI coding-agent harness/model combinations using **both reproducible coding-task benchmarks and developer-specific preferences**. Gemma 4 structures confirmed developer preferences; isolated local Docker benchmarks supply measured evidence; the CPU-only LAYA typed-decision engine consumes both sources and makes preference-aware selections. HarnessArena validates constraints and normalizes measurements before LAYA, orchestrates comparisons, and attaches evidence-backed explanations. An explicitly labeled deterministic fallback remains available. A separate verified public leaderboard and experiment/replay dashboard make the evidence inspectable.

**One-liner:** Don't just benchmark AI coding agents. Discover the one that works best for you.

## 2. Problem and Target Users

Existing agent leaderboards optimize aggregate benchmark performance. Developers differ substantially in priorities: reliability, speed, cost, autonomy, approval controls, privacy, preferred language/framework, and task type. They need a reproducible way to test alternative harnesses under comparable conditions and get explainable personalized recommendations.

**Primary users:** Individual software developers choosing a coding harness.  
**Secondary users:** Maintainers building/testing agent harnesses; AI engineering teams choosing defaults.

### Jobs to be done
1. Understand what matters to me through a conversation rather than a tedious form.
2. Compare harnesses on identical realistic tasks with verifiable measurements.
3. Run an additional workload suited to my coding tasks, with clear boundaries between public and personalized results.
4. Receive an explainable, constraint-aware recommendation and credible alternatives.
5. Reproduce benchmark runs using pinned versions, snapshots and recorded configurations.

## 3. Goals, Non-Goals, and Success Criteria

### Goals (MVP)
- Gemma 4 preference-chat interview, with explicit confirmation/editing of the structured profile.
- Two supported harness adapters and one shared open-weight coding model for initial fair comparison.
- 10–20 curated software engineering tasks with fixed initial repository revisions and machine-checkable grading.
- Docker-based isolated runs, robust timeout/resource limits, and audit-friendly metrics/artifacts.
- Global leaderboard plus developer-specific recommendations and trace inspection.
- LAYA as the central personalized typed-decision engine with a measured evaluation gate and an explicitly labeled deterministic fallback; it never creates benchmark measurements.
- Public GitHub repository, runnable demo, integration tests, documentation, and a compatible open-source license.

### Non-goals (MVP)
- Training new foundation models; universal support for every coding harness; arbitrary browser/computer control; auto-purchasing APIs; guarantee of cost-free cloud inference; claiming statistical significance from a tiny task suite; treating AI-judged output alone as test success.

### Acceptance metrics
- Demo completes a preference interview, confirms profile, dispatches at least two harnesses on the same task, grades outcomes, and shows a personalized ranking.
- 100% of displayed benchmark scores link to run IDs, metrics, configuration, and grading artifacts.
- 100% of recorded run requests include task version, harness version, model identifier, runner image digest and effective budgets.
- Benchmarks run with a configured per-run timeout and CPU/memory/network controls; a killed run is marked separately from task failure.
- Unit tests cover weight normalization, constraints, ties, missing data, score polarity, and recommendation explanations.
- At least three independent repeated trials per harness-task pair in the standard MVP comparison; present confidence intervals or dispersion, not unsupported precision.

## 4. Product Flow

1. **Discover:** Developer visits public leaderboard or chooses “Find my harness.”
2. **Interview:** Gemma 4 asks adaptive questions on goals, dominant tasks, correctness vs speed vs cost, autonomy, approvals, privacy, budget, environment and languages.
3. **Confirm profile:** Extract structured preferences with evidence spans and confidence; user reviews/edit weights, constraints, and permitted benchmark spend. The user must explicitly approve the resulting evaluation plan.
4. **Plan:** Select a fixed global benchmark subset and optional task-matched personal benchmark subset. Estimate time/usage based on configured caps, not invented API pricing.
5. **Execute:** Enqueue controlled tasks. Runner starts clean isolated containers, checks out pinned code, invokes the harness adapter with a fixed model, records execution logs and traces, applies time/resource/token budgets, collects code patch.
6. **Grade:** Apply deterministic tests and patch validity checks, independent from the agent under test; report task solved, build/test results, elapsed time, provider usage/cost when verifiable, tool call counts, approval events, and policy violations.
7. **Decide:** Hard-filter candidate harness/model combinations breaking confirmed must-have constraints; normalize verified measurements. LAYA consumes these measurements and preferences to choose between eligible combinations. HarnessArena orchestrates pairwise decisions, validates consistency, and reports uncertainty or a clearly labeled deterministic fallback when necessary.
8. **Explain:** Show personalized top pick, runner-up, reason/tradeoffs, sample size, confidence/coverage, and replay trace. Allow preference adjustments and reranking without rerunning when metric coverage is adequate.

## 5. Requirements

### 5.1 Gemma 4 preference interview (P0)
- Gemma 4 open-weight model is a first-class hosted integration through Google AI Studio/Gemini API, initially `gemma-4-26b-a4b-it`. A dedicated provider adapter permits additional endpoints later; OpenAI compatibility is not presumed for the native Google API. Model ID and provider provenance are recorded. No local GPU is required.
- Interview uses structured extraction and adaptive follow-up only for ambiguous/high-impact preferences.
- Developer preferences: reliability, speed, monetary cost, token efficiency, autonomy, human review/control, privacy/local-first, language/framework/task distribution, hardware/OS, budget and maximum acceptable time.
- Store numeric weights in [0,1] summing to 1 for soft criteria; store hard constraints separately. User can override all weights and edit answers.
- No preference data leaks into public benchmark prompts or GitHub repositories. Prompt injection in imported code must not change benchmark configuration.
- Display model source and version; confirm license compliance of any model endpoints used.

### 5.2 Decision system / LAYA (P0)
- LAYA is a typed-decision model for finite-choice classification, scoring, and yes/no judgments, not a generative chatbot or direct measurement source.
- Primary application: choose and rank eligible harness/model combinations using BOTH confirmed preferences and real benchmark evidence; return a primary choice, alternatives, typed tradeoff decisions, confidence information, and supporting evidence.
- Deterministic preprocessing enforces constraints, benchmark integrity, and versioned metric normalization. HarnessArena orchestrates pairwise finite choices (A, B, equivalent fit, insufficient evidence) and checks reversed-order consistency and cycles. Explanations reference measured facts and typed reason labels. LAYA probabilities remain distinct from calibrated recommendation confidence and benchmark uncertainty.
- Provide an audited no-LAYA weighted baseline and a feature flag. Unavailable, unreliable, or uncertain LAYA results produce an **explicitly labeled deterministic fallback**, retaining the failure/uncertainty reason. Missing positively weighted evidence produces insufficient evidence rather than an invented recommendation.
- Validate `laya-typed-decisions` on 120 manually labeled cases split into 40 development, 40 calibration, and 40 held-out cases. Include preferences plus benchmark facts, negation, missing data, ties, candidate-order swaps, and cycles. Release gates: at least 90% accuracy among accepted held-out decisions, 50% coverage, and 95% order-swap consistency. Report counts and uncertainty; these are engineering gates, not significance claims.
- Run the official `laya-serve` HTTP server in a separate Docker Desktop CPU container; expose only `127.0.0.1:8001`, use `/v1/systemone`, preload only `typed-decisions`, persist its pinned model cache, and enforce resource/HTTP limits and health checks. Benchmark containers cannot reach LAYA.
- Cite the source of each rank component: benchmark metric, user preference, or inferred classification.

### 5.3 Harness adapters & benchmark execution (P0)
- Define an original adapter contract: `prepare(config)`, `execute(task, model, budgets)`, `collect_artifacts()`, `terminate()`; must report installed harness commit/version and model/provider details.
- Initial adapter candidates are OpenCode and Aider, tested against the same hosted open-weight coding checkpoint (initial candidate: Qwen3-Coder-30B-A3B-Instruct), provider endpoint, task, and effective budgets. Final support requires live feasibility evidence; tool differences and unsupported controls are disclosed.
- Fix task fixture version, base commit, hidden grader, model version, sampling parameters where supported, prompt policy, max attempts, wall time, memory/CPU, network policy, and token budgets.
- Execute only maintainer-curated fixtures on the owner's Windows 11 PC using Docker Desktop's WSL2/Linux backend. Isolate repository code: no task-container Docker socket, host secrets, or privileged mode; drop capabilities, use non-root UID, bound disk/CPU/memory/PIDs, default-deny egress except an attempt-scoped model gateway, and clean up every run. Arbitrary repository submissions require a later stronger isolation design.
- Worker handles timeout, cancellation, partial logs, retries only for infrastructure errors, and crash recovery. A retry has a distinct attempt ID.
- Gradings execute independently of the agent; preserve failing and passing tests, structured JSON summary, normalized patch, logs and source hashes.
- Official leaderboards accept only verified pinned runs from controlled fixtures. Personal runs are tagged and never silently mixed into global rankings.

### 5.4 Benchmark tasks and statistical treatment (P0)
- Initial pack: 10–20 curated tasks spanning bug fixes, feature implementation, tests and refactoring, primarily TypeScript/Python. Each task includes repository snapshot, setup steps, objective acceptance tests, tags, difficulty, and a valid reference fix verified by maintainers.
- Separate visible development feedback from hidden grading tests to reduce benchmark overfitting.
- Standard comparison uses identical fixtures and at least 3 attempts per harness-task pairing; report both raw counts and aggregated success with uncertainty. Small N is prominently disclosed.
- Keep harness-vs-model as separate factors. Default fair comparison fixes the model; optional factorial runs compare (harness, model) combinations.
- Latency and token costs depend on provider/region/cache; identify metric sources and missing coverage, never infer fake costs.

### 5.5 Dashboard (P0)
- Public: filterable leaderboard with harness, model, task suite, success rate, uncertainty, median elapsed time, observed tokens and monetary costs, date and provenance.
- Personal: interactive weights, hard constraints, primary tasks, ranked recommendation, tradeoff explanations, recommendation confidence and compare view.
- Experiments: job status, run details, tool call timeline, code diffs, stdout/stderr, test grading and downloadable machine-readable manifests.
- Accessibility: keyboard navigation, mobile-readable tables, high contrast, readable charts, and loading/empty/error states.

### 5.6 Auth, privacy and operations (P1)
- Anonymous global leaderboard; authenticated users save private preferences and experiments. Guest session support can be added first.
- Store only necessary personal data; redact API credentials, private source content, secrets and identifiable data from public traces.
- Encrypt provider tokens at rest if BYOK exists later; for MVP, allow admin-configured server providers with spend limits.
- Rate limits, queue quotas, admin cancellation, retention windows and abuse controls.

## 6. Ranking Contract

For harness `h`, user `u`, and criterion `k`:

`baseline_fit(h,u) = Σ_k weight(u,k) × normalized_metric(h,k)`

The formula is the audited baseline/fallback, not the primary selection algorithm. LAYA selects among eligible **harness/model combinations** using confirmed preferences and verified normalized evidence. Only compute the baseline after enforcing hard constraints. Define score direction (`lower is better` for latency/cost; `higher is better` for solved tasks/control adherence), versioned reference ranges, missing-value policy, and task-family relevance. Metrics with no valid evidence are **unknown**, not zero or median. Require coverage of every positively weighted criterion; do not silently redistribute missing weights. Preference changes create a new recommendation without mutating benchmark results.

**Critical policy:** LAYA cannot override an explicit hard constraint or a measured failing test. If the preferred harness is more expensive or slower, surface that tradeoff visibly.

## 7. Data Model (proposed)

- `users`: id, timestamps.
- `developer_profiles`: user_id, version, preferences JSON, constraints JSON, confirmation status, model/extraction provenance.
- `harnesses`: id, repo, commit/version, adapter version, supported features.
- `models`: identifier, provider, weight/license metadata, context capacity where verifiable.
- `task_suites` / `tasks`: suite version, repo/base SHA, image digest, public metadata, private grader location, tags.
- `experiments`: user, suite, comparison set, selected profile version, requested budget, status.
- `runs`: experiment, harness, model, task, seed/attempt, container digest, status, timestamps, configuration manifest.
- `run_metrics`: task_pass, tests_total/passed, latency, token input/output, provider_cost_observed, telemetry quality.
- `run_artifacts`: SHA-256, object storage reference, redaction status, visibility.
- `recommendations`: profile version, candidate set, constraints evaluation, score breakdown, evidence references, model/decision versions.
- `audit_events`: benchmark dispatch, approval, cancellation, publishing, admin actions.

## 8. Technical Architecture

### Components
- **Web:** Next.js + TypeScript + Tailwind + accessible component library + Recharts.
- **API:** Local FastAPI + Pydantic v2 + PostgreSQL + Alembic, alongside local LAYA.
- **Queue:** PostgreSQL durable job leases, outbound API polling, heartbeats, fencing tokens, and idempotent completion; no Redis requirement.
- **Inference:** Hosted Gemma 4 via Google AI Studio; CPU-only official LAYA HTTP server in a private Docker container. Provider credentials remain outside task containers.
- **Runner:** Trusted local Python worker controlling Docker Desktop on Windows 11/WSL2. Future remote workers implement the same outbound HTTP protocol; no remote worker or GPU is required for MVP.
- **Storage:** Persistent local artifact adapter first, with an S3-compatible adapter seam for later hosting.
- **Observability:** OpenTelemetry, structured logging, basic metrics and health endpoints.
- **Deployment:** Local frontend/API/database/worker/LAYA first; optional DigitalOcean hosting for sanitized public replay and frontend. Judges see a local live demo plus public results/recording. LAYA is never public. No paid cloud infrastructure or API tunnel is required.
- **Contracts:** Versioned `/api/v1` OpenAPI and JSON Schema, generated from Pydantic; approval binds an immutable plan hash. Worker claim/heartbeat/progress/artifact/completion contracts reject stale fencing tokens. Task containers never access the database.
- **Spend:** Verified free-tier inference is allowed under request/token quotas; unverified eligibility fails closed. Paid calls require explicitly configured caps and approval. Monetary metrics remain unknown without verifiable evidence.

### API candidates
- `POST /api/interviews`, `POST /api/interviews/{id}/messages`, `POST /api/profiles/{id}/confirm`
- `GET /api/harnesses`, `GET /api/tasks`, `GET /api/leaderboard`
- `POST /api/experiments/plan`, `POST /api/experiments`, `GET /api/experiments/{id}`
- `GET /api/runs/{id}`, `GET /api/runs/{id}/artifacts`, `POST /api/experiments/{id}/cancel`
- `POST /api/recommendations`, `GET /api/recommendations/{id}`
- `GET /health`, `GET /ready`

Implement documented OpenAPI contracts and version schemas; validate incoming data and apply rate limits.

## 9. Safety, Fairness, and Reproducibility

- Running GitHub repos is running untrusted code: restrict privilege, use ephemeral workers, enforce resource limits, disable outgoing network except necessary proxy and never expose cloud tokens to task container.
- Distinguish harness failures from model failures and runner/infrastructure failures.
- Publish task/sample manifests and full reproduction instructions; protect hidden graders and private credentials.
- Pin images by immutable digest and source repos by SHA; log dependency and benchmark version changes.
- Avoid making personal benchmark data public without consent.
- Detect benchmark contamination or suspicious task leakage where feasible; document uncertainty.

## 10. Delivery Plan

### Phase 0 — Architecture and feasibility (P0)
- Publish local specifications, eight ADRs, glossary, contracts, risk register, engineering instructions, and 18 dependency-linked tickets before application implementation.
- Verify hosted Gemma 4, CPU-only `laya-serve` with `typed-decisions`, license compatibility, WSL2/Desktop controls, and two cross-compatible harness adapters. Keep documented capabilities separate from experimentally verified results.
- Run two isolated coding agents against one known fixture; validate trace capture and grading. Document resource estimates.

### Phase 1 — Domain, API and UI skeleton (P0)
- Models/schemas and ADRs; app shell; visibly synthetic mock leaderboard; interview API with fake implementation behind an adapter.

### Phase 2 — Interview and profile (P0)
- Gemma interview, structured extraction, editing and confirmation, versioning, fixtures and prompt-injection tests.

### Phase 3 — Runner and grading (P0)
- Docker isolation; harness adapters; task manifest; queue; 10–20 tasks; retries/cancellations and safety tests.

### Phase 4 — Scoring, LAYA and results (P0)
- Central LAYA pairwise decision orchestration over developer and benchmark intelligence; deterministic integrity preprocessing and labeled baseline fallback; relevance-weighted suite selection; separate leaderboard and trace viewer.

### Phase 5 — Release and evaluation (P0)
- Three repeated trials per pairing; benchmark methodology and confidence treatment; reproducible release; Apache-2.0 ownership/dependency review; GitHub Actions CI and public replay/local live demo.
- A one-fixture, two-harness, three-trial demonstrator precedes the complete 10–20-task release. Neither is labeled complete before its acceptance criteria pass. See `docs/roadmap.md` and `.scratch/harnessarena/issues/` for the approved incremental graph.

## 11. Required Automated Tests

- Unit: preference extraction schema, weights, ranking formulas, hard constraints, missing metrics, monotonicity, LAYA fallback.
- Integration: API + DB migrations; queue idempotency; manifest validation; artifact storage; model endpoint mocks.
- Runner: container timeouts, CPU/memory/disk limits, network denial, no host credential exposure, grader independence, cleanup.
- E2E: new developer → interview → profile confirmation → experiment → reproducible results → personalized recommendation.
- Golden fixtures: intentionally failing and passing agents, benchmark runner errors, unavailable model, high-latency model, noncomparable conditions.

## 12. Open Source and Challenge Submission

- Original engineering must include adapter architecture, orchestrator, runner, experiment model, trace recording, privacy-aware dashboard and decision layer; unchanged forks are insufficient.
- Document original vs adapted code and maintain third-party license notices.
- Publish public GitHub repository with LICENSE, README, CONTRIBUTING, architecture docs, example profiles, fixture pack, reproducible experiment instructions, benchmark limitations, architecture decision records, issues for new contributors, and CI badges.
- If shipping agent skills, follow Agent Skill Open Standard with valid `SKILL.md` frontmatter and tests.
- Make open-weight AI important to behavior, not a decorative component: Gemma handles meaningful interview and structured preference inference; LAYA adds measured classification where beneficial.

## 13. Open Questions (resolve through spikes/ADRs, not blockers to scaffolding)

1. Which two harnesses reliably support the **same exact open-weight coding model** and prompt/tool budgets?
2. Which hosted Gemma 4 provider/instance meets demo budgets and terms?
3. Which subset of LAYA typed-decision tasks beats simple rules on a held-out labelled dataset?
4. Do all required controls work on Docker Desktop/WSL2 for curated fixtures? Arbitrary public code is out of MVP scope.
5. Do organizers permit a live API-hosted open-weight model, or require weights downloadable from the repo? Document proof of model use.
6. What baseline benchmarks and hardware are achievable within available funding?

## 15. Challenge submission and implementation status

Primary target: [Best Open-Source AI Project](https://www.mlh.com/events/hacktoberfest-hack-day-pune-x-fair/challenges/01a0d987-0c41-12ea-13ac-5b85755dc2f3). The supplied Pune URL displays Mumbai x FAIR; preserve the organizer's URL and document that discrepancy. The page lists October 11, 2026, 5:00 PM IST as the deadline and requires public GitHub publication, an open-source license, and meaningful open-source/open-weight AI use. The [Gemma challenge](https://www.mlh.com/events/hacktoberfest-hack-day-pune-x-fair/challenges/01a03b87-be22-9180-5e2d-b3beeb66666d) explicitly permits Gemini API use.

Documentation and contract completion do not imply live integration completion. Live Gemma, LAYA, harness, and isolation checks need actual endpoint/host evidence. Record unmeasured values as unmeasured and preserve original source/result hashes.

## 14. References

- Gemma 4 official model card: https://ai.google.dev/gemma/docs/core/model_card_4
- LAYA typed decision engine: https://github.com/NandhaKishorM/laya
- SWE-bench: https://github.com/SWE-bench/SWE-bench
- Foundation ideas: https://github.com/unknown77master/codex-router and https://github.com/unknown77master/open-agent-view
