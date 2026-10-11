# 17: Execute repeated comparisons and report uncertainty

Status: planned
Dependencies: [13](13-live-viewer.md), [16](16-task-pack.md)
Specification: [docs/specs/05-benchmarks.md](../../../docs/specs/05-benchmarks.md)

## Scope

Implement and validate the contract in the linked specification. Preserve public/personal separation, immutable evidence, approved limits and unknown metric values. No completion claim is valid without linked evidence.

## Acceptance criteria

- [ ] Run three independent trials per harness/task pair with fixed shared model and declared comparable conditions.
- [ ] For two harnesses and ten tasks collect at least 60 standard attempts, excluding infrastructure retry inflation.
- [ ] Publish raw counts, exclusions, uncertainty method, elapsed dispersion and token/cost coverage without unsupported precision.

## Given / When / Then scenarios

- Given infrastructure retry, when aggregating trials, then it does not become an extra independent success.
- Given missing provider usage or incomparable conditions, when reporting, then missing/excluded coverage is visible.
- Given small samples, when displaying leaderboard, then uncertainty and sample sizes remain prominent.

## Required validation

Aggregation/interval/count fixtures; verify manifests and independent attempt provenance; actual repeated-run evidence and reviewed output report.

## Validation commands

Run in the locked Python environment: `python -m pytest tests/integration/test_repeated_reports.py`.
The named test modules are implementation targets; create them with meaningful acceptance tests before completing this ticket. Missing modules are not passing evidence.
For product workflows, add API/database integration and browser acceptance checks required by the linked specification. Record commands, actual outcomes and evidence paths; mocked provider responses establish contract handling only.

## Evidence and completion

- Implementation: pending.
- Automated checks: pending; record command, outcome and relevant report path.
- Live probe/artifacts where required: pending; blocked prerequisites do not count as passing.
- Review: pending; retain failed outcomes and limitations.

Mark complete only after every acceptance criterion and required scenario has evidence. Do not present fixtures, target configuration, installed packages or source pins as measured runtime success.

