"""Validate planning links, ticket graph, contracts and local infrastructure guardrails."""
import json
import re
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator
from openapi_spec_validator import validate

from scripts.export_contracts import build_contracts

ROOT = Path(__file__).resolve().parents[1]


def validate_project(root=ROOT):
    failures = []
    markdown = [root / name for name in ["README.md", "AGENTS.md", "GLOSSARY.md", "CONTRIBUTING.md", "THIRD_PARTY_NOTICES.md", "prd.md"]]
    markdown.extend((root / "docs").rglob("*.md"))
    issues = sorted((root / ".scratch/harnessarena/issues").glob("*.md"))
    markdown.extend(issues)
    for path in markdown:
        if not path.is_file():
            failures.append(f"Missing document: {path.relative_to(root)}")
            continue
        text = path.read_text(encoding="utf-8")
        for target in re.findall(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", text):
            if re.match(r"^[a-z]+://", target) or target.startswith("#"):
                continue
            location = target.split("#", 1)[0].strip("<>")
            if location and not (path.parent / location).exists():
                failures.append(f"Broken link: {path.relative_to(root)} -> {location}")
    if len(issues) != 18:
        failures.append("Expected exactly 18 approved ticket files.")
    for path in issues:
        number = int(path.name[:2])
        text = path.read_text(encoding="utf-8")
        for dependency in re.findall(r"\[([0-9]{2})\]\([^)]+\)", text):
            if int(dependency) >= number:
                failures.append(f"Non-topological dependency in {path.name}: {dependency}")
        if "Status:" not in text or "## Acceptance criteria" not in text or "## Required validation" not in text:
            failures.append(f"Incomplete ticket structure: {path.name}")
    adrs = list((root / "docs/adr").glob("*.md"))
    if len(adrs) != 8:
        failures.append("Expected eight approved ADR topics.")
    for name, expected in build_contracts().items():
        path = root / "packages/contracts/generated" / name
        if not path.exists() or json.loads(path.read_text(encoding="utf-8")) != expected:
            failures.append(f"Generated contract drift: {name}")
    contracts = build_contracts()
    Draft202012Validator.check_schema(contracts["schema.json"])
    validate(contracts["openapi.json"])
    compose = yaml.safe_load((root / "compose.yaml").read_text(encoding="utf-8"))
    laya = compose["services"]["laya"]
    env = laya["environment"]
    guards = {
        "loopback-only LAYA": laya["ports"] == ["127.0.0.1:8001:8000"],
        "CPU-only LAYA": env["LAYA_DEVICE"] == "cpu" and laya["build"]["args"]["TORCH_INDEX"] == "cpu",
        "typed checkpoint only": env["LAYA_MODELS"] == "typed-decisions" and env["LAYA_DEFAULT_MODEL"] == "typed-decisions" and env["LAYA_MAX_LOADED"] == "1" and env["LAYA_AUTO_TASK"] == "0",
        "bounded LAYA": laya["cpus"] <= 2 and laya["mem_limit"] == "4g" and env["LAYA_MAX_CONCURRENT"] == "1",
        "immutable source/checkpoint pins": bool(re.search(r"#[a-f0-9]{40}$", laya["build"]["context"])) and bool(re.fullmatch(r"[a-f0-9]{40}", env["LAYA_REVISION"])),
        "persistent weights": any("laya-model-cache:" in volume for volume in laya["volumes"]),
        "no GPU/socket": not laya.get("gpus") and not any("docker.sock" in volume for volume in laya["volumes"]),
    }
    failures.extend(f"Infrastructure guard failed: {name}" for name, passed in guards.items() if not passed)
    return failures


def main():
    failures = validate_project()
    for failure in failures:
        print(failure)
    if failures:
        raise SystemExit(1)
    print("Validated documentation links, 18-ticket graph, 8 ADRs, OpenAPI/JSON Schema, and Compose guardrails.")


if __name__ == "__main__":
    main()
