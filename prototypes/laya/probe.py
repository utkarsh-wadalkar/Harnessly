"""Run a local, synthetic typed-decision HTTP probe and save a safe report."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from packages.decision.laya_client import (
    PINNED_TYPED_REVISION,
    LayaDecisionClient,
    LayaUnavailable,
)


SOURCE_COMMIT = "68804629e8ccd9d616d48a40e87de9fabbeae069"
DEFAULT_OUTPUT = Path(".local/laya-probe.json")
_CONFIG_KEYS = ("LAYA_API_KEY", "LAYA_BASE_URL")
_QUESTION = {
    "pair": {
        "type": "choice",
        "instructions": "For the synthetic metric examples, which candidate better follows the stated preference?",
        "criteria": ["candidate_a", "candidate_b", "equivalent", "insufficient_evidence"],
    }
}
_SYNTHETIC_STATE = {
    "preference": "Prefer lower latency within a fixed synthetic monthly cap.",
    "metric_examples": [
        {"candidate": "candidate_a", "latency_ms": 120, "monthly_cost_units": 4, "synthetic": True},
        {"candidate": "candidate_b", "latency_ms": 180, "monthly_cost_units": 3, "synthetic": True},
    ],
}


def _dotenv_values(path: Path = Path(".env")) -> dict[str, str]:
    values: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return values
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        name, value = stripped.split("=", 1)
        name = name.strip()
        if name not in _CONFIG_KEYS:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        values[name] = value
    return values


def _config(environ: Mapping[str, str] | None) -> tuple[str | None, str]:
    process_env = os.environ if environ is None else environ
    file_values = _dotenv_values()
    key = process_env.get("LAYA_API_KEY") if "LAYA_API_KEY" in process_env else file_values.get("LAYA_API_KEY")
    base_url = process_env.get("LAYA_BASE_URL") if "LAYA_BASE_URL" in process_env else file_values.get("LAYA_BASE_URL")
    return key, base_url or "http://127.0.0.1:8001"


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _empty_report() -> dict[str, object]:
    return {
        "timestamp": _timestamp(),
        "source": f"laya.serve@{SOURCE_COMMIT}",
        "checkpoint": {
            "name": "typed-decisions",
            "requested_revision": PINNED_TYPED_REVISION,
            "served_revision": None,
        },
        "cpu_health": None,
        "typed_decision": None,
        "outcome": "unavailable",
        "verification": "unavailable",
    }


def run_probe(
    output_path: str | Path = DEFAULT_OUTPUT,
    *,
    environ: Mapping[str, str] | None = None,
    transport: Callable | None = None,
) -> int:
    """Probe using the explicit key and save only bounded, non-private response fields."""
    report = _empty_report()
    api_key, base_url = _config(environ)
    if not api_key:
        report["error"] = {"code": "missing_credentials"}
        _write_report(output_path, report)
        return 1
    try:
        client = LayaDecisionClient(api_key, base_url, transport=transport)
        health = client.health()
        report["checkpoint"] = {
            "name": "typed-decisions",
            "requested_revision": PINNED_TYPED_REVISION,
            "served_revision": health.revision,
        }
        report["cpu_health"] = {
            "status": health.status,
            "device": health.device,
            "device_is_preference": health.device_is_preference,
            "checkpoint_device": health.checkpoint_device,
            "loaded": list(health.loaded),
        }
        decision = client.predict(_SYNTHETIC_STATE, _QUESTION)
        report["typed_decision"] = {
            "model": decision.model,
            "checkpoint": decision.checkpoint,
            "revision": decision.revision,
            "probabilities": decision.probabilities,
            "raw_confidence": decision.raw_confidence,
        }
        report["outcome"] = decision.outcome
        report["verification"] = "typedHTTPverified"
    except LayaUnavailable as error:
        report["outcome"] = "unavailable"
        report["verification"] = "unavailable"
        report["error"] = {"code": error.code, "status_code": error.status_code}
    _write_report(output_path, report)
    return 0 if report["verification"] == "typedHTTPverified" else 1


def _write_report(output_path: str | Path, report: dict[str, object]) -> None:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    code = run_probe(args.output)
    report = json.loads(args.output.read_text(encoding="utf-8"))
    if code == 0:
        print(f"verification={report['verification']} outcome={report['outcome']}")
    else:
        print(f"verification=unavailable error={report.get('error', {}).get('code', 'probe_failed')}", file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
