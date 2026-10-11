"""Inspect an operator-configured coding model catalogue without inference."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from packages.harness_adapters.model_source import (
    ModelSource, ModelSourceUnavailable, container_endpoint,
)

ALLOWED = {"CODING_ENDPOINT", "CODING_API_KEY", "CODING_MODEL"}


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


def run_probe(output: str | Path = ".local/coding-source.json", *, environ=None,
              transport=None, cwd: str | Path | None = None, container: bool = False) -> int:
    root = Path(cwd) if cwd is not None else Path.cwd()
    values = _dotenv(root / ".env")
    source = os.environ if environ is None else environ
    values.update({key: str(value) for key, value in source.items() if key in ALLOWED})
    endpoint = values.get("CODING_ENDPOINT", "")
    selected_id = values.get("CODING_MODEL", "")
    report = {"source_configured": bool(endpoint), "credential_present": bool(values.get("CODING_API_KEY")),
              "connection": "not_attempted", "selected_model": None, "model_ids": [],
              "catalogue_only": True, "inference_verified": False,
              "license": None, "revision": None, "cost_usd": None}
    try:
        if not endpoint:
            raise ModelSourceUnavailable("missing_source")
        if not selected_id:
            raise ModelSourceUnavailable("missing_model")
        client = ModelSource(endpoint, values.get("CODING_API_KEY", ""), transport)
        models = client.list_models()
        report["model_ids"] = list(models)
        report["connection"] = "catalogue_available"
        report["selected_model"] = client.select(models, selected_id)
        if container:
            report["container_endpoint"] = container_endpoint(endpoint)
    except ModelSourceUnavailable as exc:
        report["error"] = {"code": exc.code, "status_code": exc.status_code}
        report["connection"] = "unavailable" if report["connection"] == "not_attempted" else report["connection"]
    destination = Path(output)
    if not destination.is_absolute():
        destination = root / destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return 0 if "error" not in report else 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=".local/coding-source.json")
    parser.add_argument("--container", action="store_true", help="Include Docker Desktop host URL metadata")
    args = parser.parse_args()
    return run_probe(args.output, container=args.container)


if __name__ == "__main__":
    raise SystemExit(main())
