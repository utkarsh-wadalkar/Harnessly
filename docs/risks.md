# Risks and evidence required

| Risk | Mitigation and release gate |
| --- | --- |
| Docker engine stopped / isolation unverified | Elevated checks found Docker CLI 29.8.2, Compose 5.5.1 and stopped Ubuntu/docker-desktop WSL2 distributions. Compose syntax validates, but the Linux daemon is stopped and startup was declined. Block execution until local engine and live isolation/limit checks pass. |
| Missing provider credentials | Keep hosted calls disabled; validate secrets through controlled probes without logging values. |
| Free-tier assumptions | Verify account eligibility, model availability, quotas and budget before requests; never promise cost-free inference. |
| LAYA CPU runtime/model incompatibility | Probe official server within 2 CPU/4 GiB limits; cache model; disable typed decisions on failure and label fallback. |
| Uncalibrated selection quality | Use fixed 120 labeled cases with disjoint 40 development/40 calibration/40 test splits; gates are 90% accepted accuracy, 50% coverage, 95% swap consistency. No confidence claims until calibration evidence exists. |
| Prompt injection or host credential exposure | Curated fixtures only, protected grader, proxy-held credentials, default-deny network and adversarial isolation tests. |
| Unequal adapter capabilities | Same hosted coding model and recorded conditions; disclose tool/prompt differences and mark incomparable pairs. |
| Tiny benchmark sample | Ten curated tasks, four task families, TypeScript/Python, three independent trials per harness/task pair; display raw counts and uncertainty. |
| Missing telemetry | Preserve unknown values and metric coverage; disable recommendations dependent on unavailable must-have evidence. |
| Duplicate or stale worker completion | Transactional PostgreSQL claims, monotonic fencing tokens, idempotent finalization and recovery tests. |
| Privacy leakage in replay | Separate public/personal evidence; explicit publication, redaction allowlist, secret scanning and private-access tests. |
| Unavailable local judge session | Public replay remains available; distinguish recorded evidence from live sessions and apply quotas. No API tunnel. |
| License or endpoint term mismatch | Apache-2.0 applies to original code subject to dependency and model review; document notices and source attribution. |
| Submission interpretation | Organizer challenge page URL says Pune while its content says Mumbai. Preserve source discrepancy; deadline is October 11, 2026, 5 PM IST. Verify public GitHub, license, meaningful open-source engineering and substantive AI behavior. |

Organizer reference: [challenge page](https://www.mlh.com/events/hacktoberfest-hack-day-pune-x-fair/challenges/01a0d987-0c41-12ea-13ac-5b85755dc2f3). Release documentation must distinguish confirmed source requirements from remaining provider and execution probe questions. Planning targets are not measured results.

