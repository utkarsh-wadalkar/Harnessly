import pytest
from pydantic import ValidationError

from packages.contracts.models import ProfileDraft


def test_profile_weights_must_sum_to_one():
    with pytest.raises(ValidationError, match="sum to one"):
        ProfileDraft(weights={"reliability": 0.7, "speed": 0.7})


def test_unknown_cost_cannot_be_fabricated_as_zero():
    from packages.contracts.models import MetricObservation
    with pytest.raises(ValidationError, match="unknown metrics"):
        MetricObservation(name="cost", value=0, unit="USD", quality="unknown", source="unknown", artifact_ids=[], missing_reason="provider does not report billing")


def test_measured_metrics_require_artifact_provenance():
    from packages.contracts.models import MetricObservation
    with pytest.raises(ValidationError, match="artifact evidence"):
        MetricObservation(name="elapsed", value=12, unit="seconds", quality="measured", source="worker", artifact_ids=[])


def test_unredacted_artifact_cannot_be_public():
    from uuid import uuid4
    from packages.contracts.models import ArtifactManifest
    with pytest.raises(ValidationError, match="redaction"):
        ArtifactManifest(id=uuid4(), attempt_id=uuid4(), kind="trace", sha256="a" * 64, size_bytes=10, media_type="application/json", redaction_status="pending", visibility="public")


def test_generated_openapi_is_valid_and_has_explicit_planned_status():
    from openapi_spec_validator import validate
    from scripts.export_contracts import build_contracts
    api = build_contracts()["openapi.json"]
    validate(api)
    assert api["paths"]["/api/v1/attempts/{attempt_id}/complete"]["post"]["x-access-role"] == "worker"
    assert all(op["x-implementation-status"] == "planned" for methods in api["paths"].values() for op in methods.values())


def test_json_schema_accepts_known_evidence_and_rejects_invalid_probability():
    from jsonschema import Draft202012Validator
    from scripts.export_contracts import build_contracts
    schema = build_contracts()["schema.json"]
    Draft202012Validator.check_schema(schema)
    schema["$ref"] = "#/$defs/ProfileDraft"
    validator = Draft202012Validator(schema)
    validator.validate({"weights": {"reliability": 1.0}})
    assert list(validator.iter_errors({"weights": {"reliability": 1.1}}))


def test_confirmed_profile_rejects_unreviewed_inferred_constraint():
    from datetime import datetime, timezone
    from uuid import uuid4
    from packages.contracts.models import ProfileVersion
    with pytest.raises(ValidationError, match="user confirmation"):
        ProfileVersion(id=uuid4(), owner_id=uuid4(), version=1, status="confirmed", confirmed_at=datetime.now(timezone.utc), interview_model="gemma-4-26b-a4b-it", extraction_version="1", weights={"reliability": 1}, constraints=[{"key": "local_inference", "value": True, "origin": "inferred", "user_confirmed": False}])


def test_lease_expiry_rejects_ambiguous_naive_timestamp():
    from datetime import datetime
    from uuid import uuid4
    from packages.contracts.models import ArtifactUpload
    with pytest.raises(ValidationError, match="timezone"):
        ArtifactUpload(artifact_id=uuid4(), upload_url="http://127.0.0.1/upload", expires_at=datetime(2026, 10, 11, 16, 0))


def test_known_metric_rejects_unknown_source():
    from uuid import uuid4
    from packages.contracts.models import MetricObservation
    with pytest.raises(ValidationError, match="source"):
        MetricObservation(name="elapsed", value=12, unit="seconds", quality="measured", source="unknown", artifact_ids=[uuid4()])


def test_approved_plan_requires_bound_execution_conditions():
    from scripts.export_contracts import build_contracts
    definitions = build_contracts()["schema.json"]["$defs"]
    assert "execution_conditions" in definitions["ExperimentPlan"]["required"]
    assert {"prompt_policy_version", "trial_seeds", "network_policy_version", "normalization_version"} <= set(definitions["ExecutionConditions"]["required"])
