# Domain and invariants

The product recommends a candidate using confirmed preferences and actual benchmark observations. Gemma interviews the developer; LAYA makes the central finite-choice selection after deterministic validation, constraint filtering and measurement normalization. The deterministic weighted baseline remains inspectable and supplies a labeled fallback. Neither model supplies benchmark values.

## Boundaries

- **Preferences:** interview, evidence spans, profile edits and explicit profile confirmation.
- **Evaluation:** proposed plan, immutable approval, experiment, run manifest, attempts and cancellation.
- **Execution:** adapter invocation, worker ownership, isolated task container, protected grading and cleanup.
- **Evidence:** observed measurements, artifacts, redaction and explicit publication.
- **Decision:** candidate eligibility, comparable evidence, deterministic baseline, typed comparisons and recommendation provenance.

A profile confirmation does not authorize spending. An evaluation approval authorizes only the exact plan digest, approved limits and selected profile version. Editing either creates a new version and requires a new approval.

## Entities

| Entity | Identity and important relationships |
| --- | --- |
| Profile version | Owner, confirmed answers, weights, constraints, evidence spans, extraction source |
| Candidate | Harness version, adapter version, model identifier and endpoint provenance |
| Task version | Suite, family, language, snapshot hash, base SHA, hidden grader version and reference-fix evidence |
| Plan | Profile version, candidates, task versions, repetitions and effective resource/usage caps |
| Approval | Approver, plan digest, time, expiry and exact authorized limits |
| Experiment | Visibility, approved plan, runs and lifecycle |
| Run | Immutable manifest, task/candidate/trial, attempt history |
| Attempt | Worker lease token, status, timestamps, metrics and artifact hashes |
| Recommendation | Profile version, evidence snapshot, constraints, baseline, LAYA comparisons and fallback reason |
| Publication | Reviewed global evidence snapshot, redaction record and artifact allowlist |

## Invariants

1. Weights are finite numbers in [0,1] and sum to one after explicit normalization; hard constraints remain separate.
2. Explicit constraints outrank inferred classifications. Unverified capability means unknown eligibility; an unknown must-have cannot pass.
3. Run manifests pin task SHA, harness version, exact model identifier, image digest, adapter, budgets, prompt policy, sampling where supported and network policy.
4. Infrastructure retries create new attempt identities. Task failure, harness failure, provider failure, infrastructure failure, timeout and cancellation are distinct.
5. Only the current fenced worker lease can renew ownership or finalize an attempt. Expiry never grants two workers publication authority.
6. Missing tokens, price, cost or outcomes remain unknown. Observed zero must have supporting evidence.
7. Passing requires independent deterministic grading; model judgment never converts a failed test to a pass.
8. Private profile and personal benchmark evidence cannot enter public prompts, aggregates or exports by default.
9. Public aggregate membership requires verified curated provenance and reviewed redaction.
10. Weight edits rerank the existing evidence snapshot without mutating measurements. Missing positively weighted evidence yields insufficient evidence; weight redistribution is prohibited.
11. A LAYA response is schema-validated and evidence-bound. Cycles and inconsistent comparisons produce a partial/uncertain result, never an invented total ranking.

## Lifecycles

Profile: editable draft → immutable confirmed version; subsequent edits produce another version. Plan: draft → approved → dispatched; draft/approved plans may become expired or invalidated. Experiment: queued → running → completed, partially_completed, failed or cancelled. Attempt: queued → leased → preparing → executing → grading → terminal execution outcome; expired ownership is recovered through a distinct attempt after orphan cleanup. Terminal outcomes are completed, timeout, cancelled, resource_exhausted, infrastructure_error, harness_error and model_error; grading independently records pass, fail, invalid_patch or unavailable. Publication: private → review-pending → published/rejected.

These are planned contracts, not claims that the application or probes have been implemented.

