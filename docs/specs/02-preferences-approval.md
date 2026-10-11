# Spec 02: Interview, profile and immutable approval

## Contract

Gemma adaptively asks about high-impact ambiguous preferences and extracts reliability, speed, cost, token efficiency, autonomy, human control, privacy, tasks, languages, environment and caps. Each extracted preference carries an answer evidence span and extraction provenance. Model extraction certainty is not recommendation confidence.

The developer can edit every answer, weight and inferred constraint. Weights are finite [0,1] values with sum one; constraints are separate. High-impact inferred constraints require explicit review. Profile confirmation freezes a version but does not approve an experiment.

Plans bind the confirmed profile, candidate identities, fixed task versions, global/personal scope, trial count, prompt/sampling conditions, limits, model/provider and estimated usage basis. Approval records plan digest, owner, expiry and maximum authorized limits. Dispatch rejects missing, expired or mismatched approvals. Any edit creates a new plan/digest; dispatched manifests never mutate.

## Acceptance scenarios

- Given ambiguous privacy intent, when extraction proposes a hard constraint, then the UI requires explicit review.
- Given invalid weights or a fabricated estimate, when confirmation/planning is submitted, then schema/evidence validation rejects it.
- Given an approved plan, when a task/model/budget/profile changes, then dispatch requires a fresh approval.
- Given a repeated identical dispatch key, when requests race, then exactly one experiment is created.
- Given imported code containing instructions, when a run starts, then approved configuration remains unchanged.

## Required validation

Extraction-schema tests; normalization and user-edit tests; prompt-injection fixtures; API/DB migration integration; digest immutability, owner checks, expiry and idempotent dispatch tests; end-to-end interview → confirmation → approval.

