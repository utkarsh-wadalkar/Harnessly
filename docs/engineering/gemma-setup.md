# Hosted Gemma interview probe

Local PostgreSQL and LAYA do not require hosted inference credentials. For the separate live interview probe, put the Google AI Studio key in ignored `.env` as `GEMMA_API_KEY`. Do not paste keys into chat, commit them or include them in evidence reports.

Keep `GEMMA_FREE_TIER_VERIFIED=false` until an operator checks the account's current Gemma model availability, free-tier terms and remaining quotas. Copy [the deliberately expired example](gemma-allowance.example.json) to `.local/gemma-allowance.json`, replace the operator and evidence reference, and set the actual UTC verification/expiry times and remaining request/token allowance. Keep account evidence private and exclude credentials. The example dates intentionally fail validation; do not treat an example as quota evidence.

Set `GEMMA_ALLOWANCE_EVIDENCE=.local/gemma-allowance.json` and enable the flag only after that review. Configured caps must fit the recorded allowance; the three generations share the input/output token budget. Both `countTokens` and `generateContent` consume the conservative request allowance. The record is an operator assertion, not independent proof of Google's current entitlement; an expired or missing record blocks all requests.

Run `python -m prototypes.gemma.probe --output .local/gemma-probe.json` in the locked virtual environment. A successful scripted probe establishes native HTTP/extraction compatibility only. Adaptive question quality, conflicting answers, injection resistance and evidence fidelity require the complete feasibility evaluation before ticket 05 can close. Missing model usage and monetary cost remain unknown.

`CODING_ENDPOINT` supplies coding-model discovery and future harness execution. It does not substitute an undocumented alias for the required Gemma 4 preference interview.
