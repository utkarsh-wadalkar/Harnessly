# ADR 007: Fixed-model repeated benchmark comparison

Status: accepted for MVP.

Decision: start with ten curated TypeScript/Python tasks covering bug fixes, features, tests and refactoring. Compare OpenCode and Aider on the same hosted Qwen model and fixed fixture/budget conditions, using three independent trials per harness/task pair. Publish raw counts, capability differences, coverage and uncertainty.

Why: a small reproducible suite can support inspectable evidence without pretending to generalize to all software work.

Tradeoff: at least 60 standard attempts require verified quota and time. Missing telemetry and unsupported sampling remain visible; infrastructure retries are not extra independent trials. Factorial model comparisons are optional and labeled separately.

Requires tickets 07–08, 16–17 and [spec 05](../specs/05-benchmarks.md).

