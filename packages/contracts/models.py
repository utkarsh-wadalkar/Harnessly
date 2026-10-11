"""Pydantic is the source of truth for version 1 wire schemas.

These define proposed interfaces, not implemented API routes. Cross-record
authorization, provenance and transactional invariants belong to workflow specs.
"""
from __future__ import annotations

from enum import StrEnum
from math import isclose
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

Probability = Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]
PositiveInt = Annotated[int, Field(gt=0)]
Sha256 = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
CommitSha = Annotated[str, Field(pattern=r"^[a-f0-9]{40}$")]
ImageDigest = Annotated[str, Field(pattern=r"^.+@sha256:[a-f0-9]{64}$")]
UtcTime = Annotated[AwareDatetime, Field(description="Timezone-aware RFC3339 timestamp; store UTC.")]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Criterion(StrEnum):
    reliability = "reliability"
    speed = "speed"
    monetary_cost = "monetary_cost"
    token_efficiency = "token_efficiency"
    autonomy = "autonomy"
    control = "control"
    privacy = "privacy"


class PreferenceEvidence(Contract):
    message_id: UUID
    start: Annotated[int, Field(ge=0)]
    end: PositiveInt
    criterion: Criterion

    @model_validator(mode="after")
    def valid_span(self):
        if self.end <= self.start:
            raise ValueError("evidence span end must follow start")
        return self


class HardConstraint(Contract):
    key: Literal["local_inference", "approval_control", "max_elapsed_seconds", "max_cost_usd", "language", "os"]
    value: bool | str | float
    origin: Literal["explicit", "inferred"]
    user_confirmed: bool


class ProfileDraft(Contract):
    weights: dict[Criterion, Probability] = Field(min_length=1)
    constraints: list[HardConstraint] = Field(default_factory=list)
    task_distribution: dict[str, Probability] = Field(default_factory=dict)
    languages: list[str] = Field(default_factory=list)
    evidence: list[PreferenceEvidence] = Field(default_factory=list)

    @model_validator(mode="after")
    def normalized(self):
        if not isclose(sum(self.weights.values()), 1, abs_tol=1e-6, rel_tol=0):
            raise ValueError("weights must sum to one")
        if self.task_distribution and not isclose(sum(self.task_distribution.values()), 1, abs_tol=1e-6, rel_tol=0):
            raise ValueError("task distribution must sum to one")
        return self


class ProfileVersion(ProfileDraft):
    id: UUID
    owner_id: UUID
    version: PositiveInt
    status: Literal["confirmed"]
    confirmed_at: UtcTime
    interview_model: str
    extraction_version: str

    @model_validator(mode="after")
    def confirmed_constraints(self):
        if any(not c.user_confirmed for c in self.constraints):
            raise ValueError("every confirmed profile constraint requires user confirmation")
        return self


class ModelIdentity(Contract):
    identifier: str
    provider: str
    provider_endpoint_id: str = Field(description="Registry reference; never credentials or a user-supplied URL.")
    revision: str | None = Field(default=None, description="Unknown if the provider cannot prove an immutable revision.")
    revision_kind: Literal["immutable", "mutable_alias", "unknown"]
    license: str | None = None


class CandidateConfiguration(Contract):
    id: UUID
    harness_id: str
    harness_commit: CommitSha
    adapter_version: str
    model: ModelIdentity
    runner_image: ImageDigest
    capabilities: dict[str, Literal["verified_supported", "verified_unsupported", "unknown"]]
    effective_sampling: dict[str, float | int | bool] = Field(default_factory=dict, description="Actual supported sampling values applied by the adapter, not capability claims.")
    effective_configuration_sha256: Sha256 = Field(description="Digest of the fully resolved, non-secret harness configuration.")
    unsupported_controls: list[str] = Field(default_factory=list)


class Budgets(Contract):
    wall_seconds: PositiveInt
    cpu_count: Annotated[float, Field(gt=0)]
    memory_mib: PositiveInt
    disk_mib: PositiveInt
    pids: PositiveInt
    max_requests: PositiveInt
    max_input_tokens: PositiveInt
    max_output_tokens: PositiveInt
    max_log_bytes: PositiveInt
    max_cost_usd: Annotated[float, Field(ge=0)] | None = None
    inference_allowance_id: UUID = Field(description="Server-verified free-tier/paid allowance, not a client attestation.")


class TaskSelection(Contract):
    task_id: str
    version: str
    base_commit: CommitSha
    snapshot_sha256: Sha256
    grader_version: str
    grader_image: ImageDigest


class PlanRequest(Contract):
    profile_version_id: UUID
    suite_version: str
    candidate_ids: list[UUID] = Field(min_length=2, max_length=8)
    task_ids: list[str] = Field(min_length=1, max_length=20)
    trials: Annotated[int, Field(ge=3, le=20)] = 3
    scope: Literal["personal", "global"] = "personal"
    budgets: Budgets


class ExecutionConditions(Contract):
    prompt_policy_version: str = Field(min_length=1)
    prompt_snapshot_sha256: Sha256 = Field(description="Digest of resolved task/candidate prompt templates; excludes private preferences.")
    trial_seeds: list[int | None] = Field(min_length=3, description="One seed per trial; null explicitly records an unsupported control.")
    network_policy_version: str = Field(min_length=1)
    normalization_version: str = Field(min_length=1)


class ExperimentPlan(Contract):
    id: UUID
    owner_id: UUID
    profile_version_id: UUID
    suite_version: str
    candidates: list[CandidateConfiguration] = Field(min_length=2, max_length=8)
    tasks: list[TaskSelection] = Field(min_length=1)
    trials: Annotated[int, Field(ge=3)]
    scope: Literal["personal", "global"]
    budgets: Budgets
    execution_conditions: ExecutionConditions
    plan_hash: Sha256
    created_at: UtcTime
    expires_at: UtcTime
    status: Literal["draft", "approved", "dispatched", "expired", "invalidated"]
    requested_attempts: PositiveInt
    estimated_cost_usd: Annotated[float, Field(ge=0)] | None

    @model_validator(mode="after")
    def bound_trials(self):
        if len(self.execution_conditions.trial_seeds) != self.trials:
            raise ValueError("trial seed count must match approved trials")
        return self


class PlanApproval(Contract):
    plan_hash: Sha256
    approved: Literal[True]


class DispatchRequest(Contract):
    plan_id: UUID
    plan_hash: Sha256


class Experiment(Contract):
    id: UUID
    plan_id: UUID
    status: Literal["queued", "running", "completed", "partially_completed", "failed", "cancelled"]
    scope: Literal["personal", "global"]
    total_runs: PositiveInt
    terminal_runs: Annotated[int, Field(ge=0)]
    created_at: UtcTime


class AttemptManifest(Contract):
    schema_version: Literal["1.0"] = "1.0"
    run_id: UUID
    attempt_id: UUID
    experiment_id: UUID
    plan_hash: Sha256
    candidate: CandidateConfiguration
    task: TaskSelection
    budgets: Budgets
    trial_index: Annotated[int, Field(ge=0)]
    retry_index: Annotated[int, Field(ge=0, le=1)]
    sampling_seed: int | None
    prompt_policy_version: str
    prompt_sha256: Sha256
    network_policy_version: str
    normalization_version: str
    worker_environment_sha256: Sha256


class MetricObservation(Contract):
    name: str
    value: float | bool | None
    unit: str = Field(min_length=1)
    quality: Literal["measured", "verified_capability", "unknown"]
    source: Literal["grader", "worker", "provider", "capability_probe", "unknown"]
    artifact_ids: list[UUID]
    missing_reason: str | None = None

    @model_validator(mode="after")
    def unknown_is_null(self):
        if self.quality == "unknown" and (self.value is not None or not self.missing_reason):
            raise ValueError("unknown metrics require null value and missing reason")
        if self.quality != "unknown" and (self.value is None or not self.artifact_ids):
            raise ValueError("known metrics require a value and artifact evidence")
        if self.quality != "unknown" and (self.source == "unknown" or self.missing_reason is not None):
            raise ValueError("known metrics require a known source and no missing reason")
        return self


class ArtifactManifest(Contract):
    id: UUID
    attempt_id: UUID
    kind: Literal["manifest", "patch", "stdout", "stderr", "trace", "grading", "usage", "environment"]
    sha256: Sha256
    size_bytes: Annotated[int, Field(ge=0)]
    media_type: str
    redaction_status: Literal["pending", "passed", "rejected"]
    visibility: Literal["private", "public"]

    @model_validator(mode="after")
    def publication_requires_redaction(self):
        if self.visibility == "public" and self.redaction_status != "passed":
            raise ValueError("public artifacts require passed redaction")
        return self


class RunDetail(Contract):
    manifest: AttemptManifest
    execution_status: Literal["queued", "leased", "preparing", "executing", "grading", "completed", "timeout", "cancelled", "resource_exhausted", "infrastructure_error", "harness_error", "model_error"]
    grading_outcome: Literal["pass", "fail", "invalid_patch", "unavailable"] | None
    metrics: list[MetricObservation]
    artifacts: list[ArtifactManifest]


class DecisionEvidence(Contract):
    candidate_ids: list[UUID] = Field(min_length=1, max_length=2)
    outcome: Literal["candidate_a", "candidate_b", "equivalent", "insufficient_evidence"]
    reason_codes: list[Literal["reliability", "speed", "cost", "token_efficiency", "workflow", "control", "privacy", "coverage"]]
    probabilities: dict[str, Probability]
    calibrated_probability: Probability | None
    calibration_version: str | None
    order_consistent: bool
    artifact_ids: list[UUID]
    profile_evidence: list[PreferenceEvidence]


class RecommendationRequest(Contract):
    profile_version_id: UUID
    experiment_ids: list[UUID] = Field(min_length=1)
    engine: Literal["laya", "deterministic_baseline"] = "laya"


class Recommendation(Contract):
    id: UUID
    profile_version_id: UUID
    evidence_snapshot_sha256: Sha256
    engine: Literal["laya", "deterministic_fallback", "deterministic_baseline"]
    engine_version: str
    status: Literal["recommended", "uncertain", "insufficient_evidence", "unavailable"]
    primary_candidate: CandidateConfiguration | None
    rank_groups: list[list[UUID]] = Field(description="Equal ranks remain grouped; incomplete orders may have no primary.")
    exclusions: dict[str, list[str]]
    decisions: list[DecisionEvidence]
    fallback_reason: str | None
    normalization_version: str
    coverage: dict[str, Probability]
    explanation: str

    @model_validator(mode="after")
    def labeled_fallback(self):
        if self.engine == "deterministic_fallback" and not self.fallback_reason:
            raise ValueError("deterministic fallback requires an explicit reason")
        if self.status == "recommended" and self.primary_candidate is None:
            raise ValueError("recommended status requires a primary candidate")
        return self


class Interview(Contract):
    id: UUID
    model_id: str
    status: Literal["active", "awaiting_confirmation", "completed", "unavailable"]


class InterviewMessage(Contract):
    text: str = Field(min_length=1, max_length=10000)


class InterviewReply(Contract):
    message_id: UUID
    text: str
    draft: ProfileDraft | None


class ProfileConfirmation(Contract):
    draft_hash: Sha256
    confirmed: Literal[True]


class TaskCatalogEntry(Contract):
    id: str
    version: str
    title: str
    tags: list[str]
    language: Literal["typescript", "python"]
    difficulty: Literal["easy", "medium", "hard"]


class LeaseClaim(Contract):
    worker_id: UUID
    capabilities: list[str]
    available_memory_mib: PositiveInt
    available_cpu_count: Annotated[float, Field(gt=0)]


class AttemptLease(Contract):
    manifest: AttemptManifest
    lease_id: UUID
    fencing_token: PositiveInt
    expires_at: UtcTime


class LeaseUpdate(Contract):
    lease_id: UUID
    fencing_token: PositiveInt


class AttemptProgress(LeaseUpdate):
    status: Literal["preparing", "executing", "grading"]
    sequence: Annotated[int, Field(ge=0)]


class AttemptCompletion(LeaseUpdate):
    execution_status: Literal["completed", "timeout", "cancelled", "resource_exhausted", "infrastructure_error", "harness_error", "model_error"]
    grading_outcome: Literal["pass", "fail", "invalid_patch", "unavailable"]
    metrics: list[MetricObservation]
    artifacts: list[ArtifactManifest]


class ArtifactSubmission(LeaseUpdate):
    artifact: ArtifactManifest


class ArtifactUpload(Contract):
    artifact_id: UUID
    upload_url: str = Field(description="Short-lived owner/attempt-scoped upload URL.")
    expires_at: UtcTime


class PublicationRequest(Contract):
    experiment_id: UUID
    evidence_snapshot_sha256: Sha256


class LeaderboardEntry(Contract):
    cohort_id: UUID
    candidate: CandidateConfiguration
    suite_version: str
    solved: Annotated[int, Field(ge=0)]
    task_attempts: PositiveInt
    infrastructure_errors: Annotated[int, Field(ge=0)]
    uncertainty_method: str
    success_interval: list[Probability] = Field(min_length=2, max_length=2)
    median_elapsed_seconds: float | None
    metric_coverage: dict[str, Probability]
    run_ids: list[UUID]
    published_at: UtcTime


class Error(Contract):
    code: str
    message: str
    request_id: UUID


class Health(Contract):
    status: Literal["ok", "unavailable"]


ALL_MODELS = [ProfileDraft, ProfileVersion, CandidateConfiguration, ExperimentPlan,
              AttemptManifest, MetricObservation, ArtifactManifest, DecisionEvidence,
              Recommendation, PlanRequest, PlanApproval, DispatchRequest, Experiment,
              RunDetail, RecommendationRequest, Interview, InterviewMessage, InterviewReply,
              ProfileConfirmation, TaskCatalogEntry, LeaseClaim, AttemptLease, LeaseUpdate,
              AttemptProgress, AttemptCompletion, ArtifactSubmission, ArtifactUpload,
              PublicationRequest, LeaderboardEntry, Error, Health]
