# Spec 06: Local viewer and public replay

The future Next.js interface has three surfaces: public recorded leaderboard/replay, private preference/recommendation views and local live experiment inspection. Every displayed score links to run ID, metric, immutable configuration and grading artifacts. Record date, suite/model/harness, raw sample size, uncertainty, elapsed-time distribution, observed usage/cost and missing coverage.

Live views expose status, bounded tool timeline, patches, stdout/stderr, grades and downloadable manifests. Preference edits rerank stored compatible evidence without changing measurements. Recommendation views show constraints, evidence sources, baseline, LAYA comparisons, partial/uncertain results and fallback reason. Numeric confidence is hidden until calibrated.

Public hosting serves reviewed static artifacts only; no tunnel or frontend call reaches the local control plane. Invited judges receive scoped, expiring local sessions with quotas and cancellation controls. When local services are unavailable, a live session visibly reports unavailability while captured replay stays labeled recorded.

Given a missing metric, when a table renders, then unknown is readable and sortable without implying zero. Given fallback or a cycle, when recommendations render, then its status is prominent. Given keyboard/mobile usage, when viewing comparisons, then content and controls remain usable. Given loading/empty/error states, when evidence is unavailable, then no fabricated result appears.

Required validation: artifact/provenance link checks; accessible keyboard/mobile/high-contrast checks; live status/cancellation E2E; quota/expiry checks; public build inspection proving no local API dependency or private data; golden fixtures labeled synthetic.

