# ADR 002: PostgreSQL durable queue and fenced leases

Status: accepted for MVP.

Decision: use transactional PostgreSQL claims with expiring leases and monotonic fencing tokens. Renewal and finalization require the current token. Infrastructure recovery creates a distinct attempt after cleanup; repeated finalization is idempotent.

Why: one source of durable truth is sufficient for a small local worker pool.

Tradeoff: queue contention and polling are acceptable at MVP scale. A future queue service must retain fencing and immutable attempt history.

Redis and Redis job frameworks from the original PRD §8 are excluded by amended PRD v1.1. Requires tickets 10–12.

