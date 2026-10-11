# HarnessArena architecture and implementation plan

## 1. Direction and deliverables

Build a local-first platform whose personalized recommendation flow is:

**Gemma 4 interview + verified Docker benchmark evidence → LAYA decision engine → recommended harness/model combination.**

The planning stage will produce the following artifacts before application implementation:

- Updated `prd.md`, preserving its requirements while replacing the optional-LAYA and remote-worker architecture.
- Research findings with primary-source links and explicit **documented / experimentally verified / unverified** status.
- Domain glossary, state-transition definitions, invariants, architecture diagrams, and risk register.
- ADRs covering the consequential architectural decisions below.
- Versioned OpenAPI and JSON Schema contracts.
- Executable specifications with PRD-to-spec-to-ticket traceability.
- One local Markdown file per approved ticket, plus a dependency roadmap.
- Root `AGENTS.md`, focused engineering instructions, README, contribution guidance, environment examples, and Docker Compose definitions.

Use Matt Pocock’s requested sequence: `research` → `domain-modeling` → `codebase-design` → `to-spec` → `to-tickets` → `writing-for-agents`. Implementation then follows `implement-spec` → `tdd` → `code-review`, one eligible ticket at a time.

The primary submission target is [Best Open-Source AI Project](https://www.mlh.com/events/hacktoberfest-hack-day-pune-x-fair/challenges/01a0d987-0c41-12ea-13ac-5b85755dc2f3). Its page requires meaningful open-source/open-weight AI use, a public GitHub repository, and an open-source license, and lists **October 11, 2026, 5:00 PM IST** as the deadline. The first demonstrator and complete PRD release will be labeled separately; neither will claim uncompleted functionality.

## 2. Architecture, repository, and domain

### Deployment and module design

- **Next.js frontend:** local development first; optional DigitalOcean hosting for public, sanitized results and replay.
- **FastAPI:** runs locally alongside LAYA for the MVP. Owns profiles, experiment approval, durable job leases, recommendations, access control, and publication.
- **PostgreSQL:** authoritative records and job queue. Atomic claims, leases, heartbeats, and fencing tokens replace the proposed Redis queue.
- **Local worker:** trusted process using Docker Desktop’s WSL2/Linux backend. Polls the API outbound; supports the same protocol for future remote workers.
- **Model gateway:** holds hosted coding-model credentials and enforces request/token allowances. Task containers receive only short-lived, attempt-scoped gateway credentials.
- **Artifact storage:** local persistent storage initially, behind an interface also implemented for S3-compatible storage.
- **LAYA:** separate CPU inference container, inaccessible to benchmark containers and publicly hosted frontend code.

Deep modules expose small workflow interfaces for interviews, experiments, execution, recommendations, and publication. PostgreSQL, hosted inference, harnesses, Docker, and storage sit behind replaceable adapters. Pure domain logic has no Docker, HTTP, or database imports.

### Planned repository shape

```text
apps/
  web/
  api/
  worker/
packages/
  domain/
  contracts/
  interview/
  decision/
  evaluation/
  harness_adapters/
  persistence/
  artifacts/
benchmarks/
  manifests/
  visible/
  grader/
  reference_fixes/
prototypes/
  gemma/
  laya/
  harnesses/
  isolation/
tests/
  integration/
  runner/
  e2e/
docs/
  research/
  adr/
  specs/
  engineering/
  roadmap.md
.scratch/harnessarena/issues/
AGENTS.md
GLOSSARY.md
prd.md
compose.yaml
.env.example
```

Use Python 3.11 with locked dependencies for backend packages, TypeScript with a pnpm workspace for the frontend, pytest for Python behavior, and Playwright for browser workflows. FastAPI/Pydantic contracts generate frontend types; CI detects contract drift.

Hidden graders remain inaccessible during agent execution. Open-source reproduction instructions explain their separation and benchmark-contamination limitations; secrecy is not treated as a permanent guarantee.

### Canonical entities and states

| Entity | Definition and lifecycle |
|---|---|
| Profile version | Immutable confirmed preferences, constraints, and interview provenance; edits create a new version. |
| Candidate configuration | Harness commit, adapter version, coding model, provider, and effective configuration. |
| Experiment plan | Immutable tasks, candidates, profile version, budgets, and scope; draft → approved → dispatched, with expiry/invalidation rules. |
| Experiment | Collection of planned runs; queued → running → completed, partially completed, failed, or cancelled. |
| Run | Logical candidate/task/trial pairing. |
| Attempt | One concrete execution; queued → leased → preparing → executing → grading → terminal outcome. Retries have distinct IDs. |
| Recommendation | Versioned decision over an evidence snapshot; LAYA result or explicitly labeled deterministic fallback. |
| Published cohort | Maintainer-verified global comparison under comparable conditions. |

Execution outcomes distinguish completion, timeout, cancellation, resource exhaustion, infrastructure error, harness error, and model/provider error. Grading independently records pass, fail, invalid patch, or unavailable.

Core invariants:

- Dispatch binds the exact approved plan and confirmed profile version.
- Measurements are immutable; preference changes create new recommendations.
- Constraints are enforced before LAYA and checked again against its output.
- Unknown evidence stays unknown.
- Personal experiments cannot be converted silently into global leaderboard evidence.
- Every displayed measurement and recommendation component has provenance.
- Expired workers cannot finalize attempts after a newer lease exists.
- Infrastructure retries are bounded and retain the original attempt’s evidence.

### ADRs

Record decisions for:

1. Local Windows/WSL2 execution and curated-fixture scope.
2. PostgreSQL leases and outbound worker protocol.
3. Central LAYA selection with deterministic integrity checks and labeled fallback.
4. CPU-only private LAYA deployment and pinned checkpoints.
5. Immutable experiment/evidence manifests and independent grading.
6. Separate public and personalized evidence.
7. Hosted inference behind provider adapters and a budget-enforcing gateway.
8. Apache-2.0 for original project code, subject to ownership and dependency review.

## 3. Decision engine, execution, and contracts

### Gemma interview

Use hosted **Gemma 4 through Google AI Studio/Gemini API**, initially testing `gemma-4-26b-a4b-it`. Google documents hosted access; endpoint availability, extraction behavior, and limits remain prototype gates. [Official integration](https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api)

Gemma must adapt follow-up questions to earlier answers, identify conflicts, and produce schema-validated preferences with message/evidence references. All inferred constraints require confirmation. Store final responses and extraction provenance; keep preferences out of benchmark prompts.

### Local LAYA

Build from a pinned official repository revision with CPU-only PyTorch and run official `laya-serve`.

Specify:

- Host mapping `127.0.0.1:8001:8000`; FastAPI uses the private Compose hostname.
- `LAYA_DEVICE=cpu`, `LAYA_PRELOAD=1`, `LAYA_MODELS=typed-decisions`.
- `LAYA_DEFAULT_MODEL=typed-decisions`, `LAYA_MAX_LOADED=1`, `LAYA_AUTO_TASK=0`.
- Explicit `model: "typed-decisions"` in requests to `/v1/systemone`.
- Named Hugging Face cache volume; recorded checkpoint revision and hashes.
- Initial limits: two CPUs, 4 GiB memory, two inference threads, one admitted request. Preflight verifies capacity before starting.
- `/health` liveness plus an authenticated typed-request readiness probe.
- Bounded HTTP timeout, schema validation, overload handling, and clear unavailable status.

These controls are supported by the [official Compose configuration](https://github.com/NandhaKishorM/laya/blob/main/compose.http.yaml) and [HTTP server source](https://github.com/NandhaKishorM/laya/blob/main/laya/serve.py). Runtime compatibility and resource sufficiency must still be measured.

### Preference-aware selection

HarnessArena preprocesses confirmed preferences and verified evidence, enforcing constraints and applying versioned normalization. The original weighted sum becomes an **audited baseline**, rather than the primary selection algorithm.

Start with at most eight eligible candidates and orchestrate pairwise LAYA choices:

- Finite outcomes: candidate A, candidate B, equivalent fit, or insufficient evidence.
- Each request includes both candidates’ measured outcomes, coverage, confirmed priorities, and relevant verified capabilities.
- Ask predefined tradeoff/reason questions; attach supporting evidence IDs through HarnessArena.
- Repeat comparisons with reversed ordering. Contradictions and preference cycles produce uncertainty or a partial ordering.
- Produce a complete ordering only where consistent decisions support it. Stable IDs control display order within ties without implying superiority.
- Explain decisions using selected reason labels and evidence-backed templates.

Model probabilities, calibration quality, benchmark dispersion, and evidence coverage remain separate. Uncalibrated probabilities are never presented as the probability that a recommendation is correct.

When LAYA is unavailable, fails validation, or cannot reliably distinguish candidates, return the **explicitly labeled deterministic fallback** selected by the user. If its positively weighted criteria lack evidence, return insufficient evidence instead of imputing values.

### Reproducible execution

OpenCode and Aider are the initial adapter candidates. Both document OpenAI-compatible endpoints, but exact shared-model compatibility requires live validation. [OpenCode](https://docs.opencode.ai/docs/providers/), [Aider](https://aider.chat/docs/llms/openai-compat.html)

Probe one hosted open-weight coding checkpoint, initially Qwen3-Coder-30B-A3B-Instruct, through the same provider endpoint for both harnesses. Record immutable model revision where available; disclose mutable provider aliases and restrict comparability accordingly.

Every attempt pins task snapshot, base commit, harness version, adapter version, model/provider, image digest, grader version, sampling controls, and effective limits. Unsupported controls are recorded rather than silently claimed.

Default to one benchmark container at a time. Containers use non-root execution, dropped capabilities, no privileged mode or Docker socket, read-only root filesystems, bounded writable storage, PID/CPU/memory limits, and isolated networks. Only the model gateway is reachable from agent containers.

A fresh grader container applies the validated patch to a clean snapshot, then executes hidden tests without inference access. Timeout, cancellation, cleanup, bounded logs, and partial artifacts are required behavior.

Live free-tier calls are allowed only after eligibility and quotas are verified. Otherwise dispatch fails closed. Request/token caps apply regardless of tier; monetary cost remains unknown unless verifiable.

### Versioned interfaces

Define OpenAPI under `/api/v1` for:

- Interviews and messages; profile editing and confirmation.
- Harness/model catalog and task catalog.
- Experiment planning, explicit approval, dispatch, status, and cancellation.
- Run manifests, metrics, artifacts, and traces.
- Recommendations and preference-based reranking.
- Verified global leaderboard and maintainer publication.

Worker contracts cover claim, heartbeat, progress, artifact submission, and fenced completion. Submission is idempotent; stale leases receive conflicts. Workers do not access PostgreSQL directly.

Schemas include `ProfileVersion`, `CandidateConfiguration`, `ExperimentPlan`, `AttemptManifest`, `MetricObservation`, `ArtifactManifest`, `DecisionEvidence`, and `Recommendation`.

Recommendations return engine/version, profile/evidence versions, primary candidate and alternatives where supported, constraint exclusions, typed decisions, uncertainty, evidence references, and fallback reason. Authentication, ownership, pagination, rate limits, idempotency, and consistent error shapes are contract requirements.

## 4. Prototype gates and risk assessment

| Risk | Minimal validation and response |
|---|---|
| Docker Desktop/WSL2 unavailable | Preflight checks Linux backend and effective limits. Current inspection did not find Docker CLI and could not read WSL status; no execution validation is claimed. |
| LAYA unreliable for candidate selection | Evaluate the selected checkpoint on 120 labeled cases: 40 development, 40 calibration, 40 held-out. Include tradeoffs, negation, ties, missing data, order swaps, and cycles. |
| Unsupported LAYA confidence | Select thresholds using calibration data; require ≥90% accuracy among accepted held-out decisions, ≥50% coverage, and ≥95% swap consistency. Report sample size and uncertainty; failed gates activate labeled fallback. |
| Hosted Gemma extraction failures | Script adaptive interviews, contradictory answers, malformed responses, and injection cases; require schema validity and evidence fidelity. |
| Harness incompatibility | One fixture, identical coding model/provider, pinned adapters, independent grading, trace capture, and actual usage reports. |
| Isolation controls ineffective on Desktop | Test egress denial, privilege restrictions, bounded disk/logs, timeout, memory/PID limits, grader separation, and cleanup. Block live runs on failed controls. |
| Misleading statistical claims | Three trials per pairing minimum; expose raw outcomes and dispersion. Keep infrastructure errors separate and disclose small samples. |
| Free-tier or licensing assumptions fail | Verify terms and quotas before calls; review original-code ownership, dependencies, model weights, and notices before release. |
| Local PC offline during judging | Local live demo plus public sanitized replay and recording. No publicly exposed LAYA or required hosted API tunnel. |

These thresholds are engineering release gates, not claims of statistical significance. LAYA validation is mandatory before its ranking logic becomes an accepted product capability.

## 5. Approved roadmap and completion rules

| Ticket | Priority | Depends on | Observable completion |
|---|---|---|---|
| 01 Planning package | P0 | — | PRD, ADRs, contracts, specs, instructions, risks, and tickets agree. |
| 02 Docker preflight | P0 | 01 | Backend/limits reported; unsafe or unavailable execution rejected. |
| 03 CPU LAYA server | P0 | 02 | Typed calls, private binding, cache reuse, health, and failure tests pass. |
| 04 LAYA feasibility | P0 | 03 | Held-out evaluation and baseline comparison produce a reproducible report. |
| 05 Gemma feasibility | P0 | 01 | Adaptive interview and evidence-backed extraction pass live probes. |
| 06 Safe fixture execution | P0 | 02 | Fake agents grade correctly; isolation and cleanup checks pass. |
| 07 OpenCode probe | P0 | 06 | Pinned live fixture produces patch, trace, usage, and grade. |
| 08 Matched Aider probe | P0 | 07 | Shared conditions verified; capability differences documented. |
| 09 Profile workflow | P0 | 05 | Private interview, edits, confirmation, and versioning work end to end. |
| 10 Approved plans | P0 | 06, 09 | Exact approval, quotas, coverage, and inference allowances enforced. |
| 11 Leased execution | P0 | 10 | Claim, heartbeat, fencing, and offline-worker behavior pass. |
| 12 Recovery/cancellation | P0 | 11 | Execution stops safely; bounded infrastructure retries retain evidence. |
| 13 Comparison viewer | P0 | 08, 12 | Live comparisons show provenance, grades, traces, and redaction. |
| 14 Recommendations | P0 | 04, 13 | Central LAYA selection, evidence, reranking, and labeled fallback work. |
| 15 Public publication | P0 | 13 | Only verified, redacted global cohorts enter the leaderboard. |
| 16 Curated pack | P0 | 06 | Ten tasks span TypeScript/Python and four task families; reference fixes verified. |
| 17 Repeated reports | P0 | 13, 16 | Three trials per pairing, comparable cohorts, and dispersion published. |
| 18 Release/demo | P0 | 14, 15, 17 | Fresh-checkout reproduction, CI, documentation, licenses, and replay pass. |

Each ticket includes executable acceptance scenarios, dependencies, relevant contracts, validation commands, and evidence requirements. Infrastructure probes are independently verifiable; product tickets exercise complete workflow slices.

Implement through public interfaces with red-green-refactor tests. Run relevant integration/runner tests and acceptance checks, then review against both specifications and engineering standards. Mark a ticket complete only when its acceptance evidence passes; blocked live integrations remain explicitly blocked.

The first demonstrator uses one fixture and two harnesses with three trials per pairing. The complete release adds the curated pack, repeated reports, and release documentation. No paid infrastructure, local GPU, arbitrary repository submissions, or public benchmark dispatch is assumed.

Automatic approval review rejected external `to-spec` publication because its tracker destination was unspecified. Specifications and tickets will remain local; no external publication is required for this plan.
