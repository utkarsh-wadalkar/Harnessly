# ADR 001: Local execution and public replay

Status: accepted for MVP.

Decision: use a local FastAPI/PostgreSQL control plane and outbound-polling worker on Windows 11 with Docker Desktop WSL2. Future Next.js frontend publishes reviewed replay evidence; invited judges use quota-limited local live sessions. No live API tunnel.

Why: this matches available compute and limits exposure while preserving inspectable public evidence.

Tradeoff: live sessions depend on the operator's machine. A replay must display its capture time and provenance, and cannot imply present availability. Dedicated remote compute and arbitrary submissions are deferred.

Records the local execution refinement incorporated into amended PRD v1.1 §8. Requires tickets 02, 11–13 and 15.

