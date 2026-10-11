# ADR 004: Evidence-bound typed candidate selection

Status: accepted for MVP.

Decision: deterministically validate preferences, enforce constraints and normalize genuine observations. LAYA then selects between eligible harness/model candidates using A/B/equivalent/insufficient comparisons across at most eight eligible candidates. All unordered pairs receive reverse-order checks, yielding at most 28 pairs and 56 total calls. Cycles or contradictory outcomes remain partial/uncertain. The weighted baseline is always inspectable and provides a labeled fallback.

Why: LAYA is central to selection while objective grading, explicit constraints and measurements retain authority.

Tradeoff: a finite comparison budget may not resolve every candidate. Abstention reduces coverage; calibrated quality matters more than manufacturing a total order. Confidence is suppressed until held-out calibration passes the declared gates.

This implements PRD v1.1 §5.2's central selection role without allowing fabricated metrics or overriding failed tests. Requires tickets 04 and 14.

