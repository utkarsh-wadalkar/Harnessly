# Spec 07: Privacy and publication

Anonymous users can read published global evidence. Private profiles and personal experiments require owner-scoped sessions; guest sessions may precede durable accounts. Store only necessary personal information. API and worker credentials stay outside task containers and logs. BYOK is deferred; admin-configured providers have verified limits.

Publication is an explicit operation binding selected controlled global run/artifact hashes, review/redaction record and provenance. Allowlist fields and artifact types; scan/redact secrets, identities, private code and prompts. Failed redaction prevents export. Personal results never silently enter global aggregates. Public snapshots cannot contain confirmed profile answers or private recommendations. Retention policy and deletion behavior must be documented before collecting personal data.

Given a user guesses another private artifact ID, when requesting it, then authorization denies access. Given a secret in a log, when publication is requested, then review fails or the reviewed redacted artifact replaces it with separate hashes. Given a personal experiment, when publication is requested through the global path, then it is rejected. Given quota exhaustion, when a local judge submits work, then dispatch is denied before provider calls.

Required validation: owner/anonymous access integration; secret-bearing artifact fixtures; global/personal aggregate segregation; publication immutability and explicit review tests; session quotas, expiry, cancellation and documented retention checks.

