"""Export proposed OpenAPI/JSON Schema from the authoritative Pydantic contracts."""
import argparse
import json
from pathlib import Path

from pydantic.json_schema import models_json_schema

from packages.contracts.models import ALL_MODELS

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "packages" / "contracts" / "generated"

# Method, path, operation ID, request, response, access role, success status.
OPERATIONS = [
    ("post", "/interviews", "startInterview", None, "Interview", "session", "201"),
    ("post", "/interviews/{interview_id}/messages", "sendMessage", "InterviewMessage", "InterviewReply", "owner", "200"),
    ("get", "/profiles/{profile_id}", "getProfile", None, "ProfileDraft", "owner", "200"),
    ("patch", "/profiles/{profile_id}", "editProfile", "ProfileDraft", "ProfileDraft", "owner", "200"),
    ("post", "/profiles/{profile_id}/confirm", "confirmProfile", "ProfileConfirmation", "ProfileVersion", "owner", "201"),
    ("get", "/harnesses", "listHarnesses", None, "CandidateConfiguration", "public", "200"),
    ("get", "/models", "listModels", None, "ModelIdentity", "public", "200"),
    ("get", "/tasks", "listTasks", None, "TaskCatalogEntry", "public", "200"),
    ("post", "/experiments/plan", "planExperiment", "PlanRequest", "ExperimentPlan", "owner", "201"),
    ("post", "/plans/{plan_id}/approve", "approvePlan", "PlanApproval", "ExperimentPlan", "owner", "200"),
    ("post", "/experiments", "dispatchExperiment", "DispatchRequest", "Experiment", "owner", "202"),
    ("get", "/experiments/{experiment_id}", "getExperiment", None, "Experiment", "owner", "200"),
    ("post", "/experiments/{experiment_id}/cancel", "cancelExperiment", None, "Experiment", "owner", "202"),
    ("get", "/runs/{run_id}", "getRun", None, "RunDetail", "owner_or_published", "200"),
    ("get", "/runs/{run_id}/artifacts", "listArtifacts", None, "ArtifactManifest", "owner_or_published", "200"),
    ("post", "/recommendations", "recommend", "RecommendationRequest", "Recommendation", "owner", "201"),
    ("get", "/recommendations/{recommendation_id}", "getRecommendation", None, "Recommendation", "owner", "200"),
    ("get", "/leaderboard", "listLeaderboard", None, "LeaderboardEntry", "public", "200"),
    ("post", "/publications", "publishCohort", "PublicationRequest", "LeaderboardEntry", "maintainer", "201"),
    ("post", "/workers/claim", "claimAttempt", "LeaseClaim", "AttemptLease", "worker", "200"),
    ("post", "/attempts/{attempt_id}/heartbeat", "heartbeat", "LeaseUpdate", "AttemptLease", "worker", "200"),
    ("post", "/attempts/{attempt_id}/progress", "progress", "AttemptProgress", "Health", "worker", "200"),
    ("post", "/attempts/{attempt_id}/artifacts", "submitArtifact", "ArtifactSubmission", "ArtifactUpload", "worker", "201"),
    ("post", "/attempts/{attempt_id}/complete", "completeAttempt", "AttemptCompletion", "RunDetail", "worker", "200"),
    ("get", "/health", "health", None, "Health", "public", "200"),
    ("get", "/ready", "ready", None, "Health", "public", "200"),
]
LIST_OPERATIONS = {"listHarnesses", "listModels", "listTasks", "listArtifacts", "listLeaderboard"}
IDEMPOTENT_OPERATIONS = {"startInterview", "sendMessage", "confirmProfile", "planExperiment", "approvePlan", "dispatchExperiment", "recommend", "publishCohort", "submitArtifact", "completeAttempt"}


def content(schema):
    return {"application/json": {"schema": schema}}


def ref(name):
    return {"$ref": f"#/components/schemas/{name}"}


def build_contracts():
    _, document = models_json_schema([(model, "validation") for model in ALL_MODELS])
    schema = {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "urn:harnessarena:contracts:1.0", **document}
    schemas = json.loads(json.dumps(document["$defs"]).replace("#/$defs/", "#/components/schemas/"))
    paths = {}
    for method, suffix, opid, request, response, role, status in OPERATIONS:
        operation = {
            "operationId": opid,
            "x-implementation-status": "planned",
            "x-access-role": role,
            "security": [] if role == "public" else [{"workerToken" if role == "worker" else "sessionCookie": []}],
            "parameters": [],
            "responses": {status: {"description": "Success", "content": content(ref(response))}},
        }
        for part in suffix.split("/"):
            if part.startswith("{"):
                operation["parameters"].append({"name": part[1:-1], "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}})
        if opid in LIST_OPERATIONS:
            operation["responses"][status]["content"] = content({"type": "object", "required": ["items", "next_cursor"], "properties": {"items": {"type": "array", "items": ref(response)}, "next_cursor": {"type": ["string", "null"]}}, "additionalProperties": False})
            operation["parameters"].extend([
                {"name": "cursor", "in": "query", "schema": {"type": "string"}},
                {"name": "limit", "in": "query", "schema": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20}},
            ])
        if opid in IDEMPOTENT_OPERATIONS:
            operation["parameters"].append({"name": "Idempotency-Key", "in": "header", "required": True, "schema": {"type": "string", "format": "uuid"}})
        if request:
            operation["requestBody"] = {"required": True, "content": content(ref(request))}
        for error_status in ["400", "401", "403", "404", "409", "422", "429", "503"]:
            operation["responses"][error_status] = {"description": "Structured error", "content": content(ref("Error"))}
        if opid == "claimAttempt":
            operation["responses"]["204"] = {"description": "No eligible job; wait before polling again."}
        if opid == "getRun":
            operation["parameters"].append({"name": "attempt_id", "in": "query", "schema": {"type": "string", "format": "uuid"}, "description": "Select historical attempt; absent means latest attempt, never merged retries."})
        paths.setdefault("/api/v1" + suffix, {})[method] = operation
    openapi = {
        "openapi": "3.1.0",
        "info": {"title": "HarnessArena proposed API", "version": "1.0.0", "description": "Design contract only. Routes are not yet implemented. Normative transaction/access behavior: docs/specs and docs/engineering/api-contracts.md."},
        "servers": [{"url": "http://127.0.0.1:8000"}],
        "paths": paths,
        "components": {"schemas": schemas, "securitySchemes": {
            "sessionCookie": {"type": "apiKey", "in": "cookie", "name": "harnessarena_session", "description": "HttpOnly session cookie; mutating browser requests also require CSRF validation."},
            "workerToken": {"type": "http", "scheme": "bearer", "description": "Rotatable worker-scoped token; never a model provider key."},
        }},
    }
    return {"schema.json": schema, "openapi.json": openapi}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Fail on generated-contract drift without modifying files.")
    args = parser.parse_args()
    for name, contract in build_contracts().items():
        text = json.dumps(contract, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        path = DEST / name
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                raise SystemExit(f"Contract drift: {path}. Run python -m scripts.export_contracts.")
        else:
            DEST.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
    print("Contracts match." if args.check else "Exported proposed contracts.")


if __name__ == "__main__":
    main()
