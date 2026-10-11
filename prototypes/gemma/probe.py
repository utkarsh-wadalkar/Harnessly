"""Run a finite synthetic interview and write a secret-safe evidence report."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

from packages.interview.gemma_client import GemmaClient, GemmaUnavailable, MODEL

ALLOWED = {
    "GEMMA_API_KEY", "GEMMA_MODEL", "GEMMA_FREE_TIER_VERIFIED", "GEMMA_MAX_REQUESTS",
    "GEMMA_MAX_INPUT_TOKENS", "GEMMA_MAX_OUTPUT_TOKENS", "GEMMA_ALLOWANCE_EVIDENCE",
}
DEFAULTS = {
    "GEMMA_MODEL": MODEL,
    "GEMMA_FREE_TIER_VERIFIED": "false",
    "GEMMA_MAX_REQUESTS": "12",
    "GEMMA_MAX_INPUT_TOKENS": "12000",
    "GEMMA_MAX_OUTPUT_TOKENS": "2000",
    "GEMMA_ALLOWANCE_EVIDENCE": ".local/gemma-allowance.json",
}


def _dotenv(path: Path) -> dict[str, str]:
    values = {}
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            key, separator, value = line.partition("=")
            if separator and key.strip() in ALLOWED:
                values[key.strip()] = value.strip().strip("\"'")
    except OSError:
        pass
    return values


def run_probe(output: str | Path = ".local/gemma-probe.json", environ=None,
              transport=None, cwd: str | Path | None = None) -> int:
    root = Path(cwd) if cwd is not None else Path.cwd()
    values = {**DEFAULTS, **_dotenv(root / ".env")}
    if environ is None:
        values.update({key: value for key, value in os.environ.items() if key in ALLOWED})
    else:
        values.update({key: str(value) for key, value in environ.items() if key in ALLOWED})
    allowance_sha256 = None
    allowance_status = "missing"
    try:
        allowance_path = Path(values["GEMMA_ALLOWANCE_EVIDENCE"])
        if not allowance_path.is_absolute():
            allowance_path = root / allowance_path
        try:
            allowance_bytes = allowance_path.read_bytes()
        except OSError:
            raise GemmaUnavailable("missing_allowance_evidence") from None
        allowance_sha256 = hashlib.sha256(allowance_bytes).hexdigest()
        allowance_status = "record_present"
        try:
            allowance_record = json.loads(allowance_bytes)
        except (ValueError, TypeError):
            raise GemmaUnavailable("invalid_allowance_evidence") from None
        if not isinstance(allowance_record, dict):
            raise GemmaUnavailable("invalid_allowance_evidence")
        config = {
            "api_key": values.get("GEMMA_API_KEY", ""),
            "model": values["GEMMA_MODEL"],
            "free_tier_verified": values["GEMMA_FREE_TIER_VERIFIED"].lower() == "true",
            "max_requests": int(values["GEMMA_MAX_REQUESTS"]),
            "max_input_tokens": int(values["GEMMA_MAX_INPUT_TOKENS"]),
            "max_output_tokens": int(values["GEMMA_MAX_OUTPUT_TOKENS"]),
            "allowance_evidence": allowance_record,
        }
        client = GemmaClient(config, transport=transport)
        allowance_status = "operator_verified"
        result = client.probe()
        report = {
            "status": "mock_preparation_only" if transport else "live_probe_completed",
            "provenance": {"provider": "Google Gemini API", "model": result.model,
                           "endpoint": "native_gemini_api", "synthetic_interview": True,
                           "allowance_status": allowance_status, "allowance_record_sha256": allowance_sha256},
            "profile_schema": "packages.contracts.models.ProfileDraft",
            "profile": result.profile.model_dump(mode="json"),
            "evidence_checks": {"valid": True, "count": len(result.profile.evidence)},
            "usage": result.usage,
            "requests": result.requests,
            "transport_elapsed_seconds": round(result.transport_elapsed_seconds, 6),
            "transport_elapsed_source": "local_monotonic_clock",
        }
    except (GemmaUnavailable, ValueError) as caught:
        error = caught if isinstance(caught, GemmaUnavailable) else GemmaUnavailable("invalid_limits")
        report = {
            "status": "unavailable",
            "provenance": {"provider": "Google Gemini API", "model": MODEL, "synthetic_interview": True,
                           "allowance_status": allowance_status, "allowance_record_sha256": allowance_sha256},
            "profile_schema": "packages.contracts.models.ProfileDraft",
            "evidence_checks": {"valid": False, "count": 0},
            "usage": {"input_tokens": None, "output_tokens": None, "cost_usd": None},
            "error": {"code": error.code, "status_code": error.status_code},
        }
    destination = Path(output)
    if not destination.is_absolute():
        destination = root / destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return 0 if report["status"] != "unavailable" else 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=".local/gemma-probe.json")
    args = parser.parse_args()
    return run_probe(args.output)


if __name__ == "__main__":
    raise SystemExit(main())
