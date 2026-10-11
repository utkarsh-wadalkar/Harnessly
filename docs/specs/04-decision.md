# Spec 04: LAYA candidate selection and evaluated fallback

## Preprocessing and baseline

Use confirmed profile and immutable real-metric snapshot. Reject incomparable conditions, enforce explicit hard constraints and preserve unknown eligibility. Define per-criterion polarity, reference range, task-family relevance and evidence coverage. Never impute missing values as zero or median. The deterministic baseline is Σ(weight × normalized observation) over the confirmed criterion set. Every positively weighted criterion requires valid comparable evidence; a missing positively weighted observation produces insufficient evidence. Weight redistribution is prohibited.

### Normalization policy v1

Reference ranges come from the approved plan and are frozen with the evidence snapshot; candidate-dependent min/max scaling is prohibited. Reliability is solved eligible trials divided by eligible trials. Elapsed time and total tokens use `1 - min(value / approved_cap, 1)` with positive wall-time and combined input/output token caps. Verified monetary cost uses the same lower-is-better transform against a positive approved cost cap; a zero-cost allowance accepts only verified zero-cost usage. Unknown cost remains unknown.

Autonomy, control and privacy fit use versioned capability probes mapped to `1` (meets the confirmed preference), `0` (does not) or unknown. Hard privacy constraints exclude candidates before scoring. Do not infer these capabilities from benchmark pass rate. For personal evidence, average trials within each task, tasks within each family, then apply the confirmed task-family distribution. Any positively weighted family without evidence remains unknown. Global cohorts use their frozen uniform task weights instead of a personal distribution.

Infrastructure failures are excluded from scored trial denominators and reported separately. Retries replace a logical trial only after valid evidence exists and never add trials to the denominator. Timeouts, provider errors and harness errors retain separate execution outcomes; unavailable grading is not a measured test failure. Scores within `1e-9` form a tie group; stable IDs determine display order only. All positively weighted observations must be known before the audited baseline can select a candidate.

## Typed selection

LAYA is central to selecting the eligible harness/model configuration. Input contains only finite candidate labels, confirmed preferences and cited real metric summaries. Its permitted output is A, B, equivalent or insufficient. At most eight eligible candidates are compared across all unordered pairs, with reversed-order checks: at most 28 pairs and 56 total calls per recommendation; schedule and unresolved candidates are recorded. It cannot generate measurement values, override constraints, or convert failed tests to passing results.

Validate response schema and label support. Inconsistent reversed comparisons, cycles, missing evidence, service failure or failed evaluation gates produce a labeled deterministic fallback or partial/uncertain recommendation. Never force a complete ordering from contradictory comparisons. Persist model/server versions, prompt/schema version, every pair and orientation, evidence IDs, baseline and fallback reason.

## Evaluation gates

Create 120 manually labeled cases before evaluating: 40 development, 40 calibration, 40 test. Keep case identities disjoint, freeze labels/splits and prevent test-set tuning. Cases include constraint exclusions, ties, missing evidence, score directions, task relevance, swaps and cycles.

At the frozen operating threshold require accepted-decision accuracy ≥90%, decision coverage ≥50% and order-swap consistency ≥95% on the held-out test set. Publish numerators, denominators, errors and uncertainty. An abstention excludes the decision from accepted accuracy but counts against coverage. Swap consistency compares both orientations with A/B remapped, includes explicit equivalent and insufficient responses, and reports the exact denominator. Confidence language requires calibration evidence; meeting accuracy alone does not justify a numeric confidence display.

## Acceptance scenarios

- Given an explicit hard constraint, when LAYA prefers an excluded candidate, then the candidate remains excluded.
- Given unavailable cost data, when cost is decisive, then unknown evidence is surfaced without fabricated prices.
- Given a cyclic or swap-inconsistent comparison, when recommendations render, then unresolved relationships and reason are visible.
- Given an unavailable LAYA service, when reranking runs, then the baseline is labeled fallback with evidence references.
- Given a failed gate or uncalibrated output, when confidence would display, then confidence claims are suppressed.

## Required validation

Normalization, monotonicity, constraints, ties, missing data, polarity and explanation tests; mocked malformed/timeout LAYA responses; eight-candidate/28-pair/56-call limits and reversal tests; reproducible split/evaluation report; exact gate boundary tests. Live selection quality remains unproven until recorded evaluation passes.

