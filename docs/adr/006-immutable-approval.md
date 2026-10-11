# ADR 006: Immutable approval and execution manifests

Status: accepted for MVP.

Decision: approval binds the exact plan digest, owner, confirmed profile version, task/candidate conditions and maximum limits. Any effective edit requires a new approval. Atomic idempotent dispatch creates immutable run manifests; later observations attach without changing inputs.

Why: preferences alone cannot authorize spend or silently changed experiments.

Tradeoff: versioning introduces additional records and explicit reapproval. This is preferable to ambiguous consent or irreproducible runs. Estimates use verified pricing and configured caps; unknown cost stays unknown.

Requires tickets 09–11 and [spec 02](../specs/02-preferences-approval.md).

