"""Start and verify only the loopback PostgreSQL and CPU LAYA services."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import secrets
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.parse import quote, unquote, urlsplit

import yaml

from apps.worker.preflight import GIB, collect_host_probe
from packages.decision.laya_client import LayaDecisionClient, LayaUnavailable, PINNED_TYPED_REVISION
from prototypes.laya.probe import synthetic_case

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = Path(".local/infrastructure-status.json")
COMPOSE_PREFIX = ("compose", "--profile", "control", "--profile", "decision")
START_SUFFIX = ("up", "--build", "-d", "--wait", "--wait-timeout", "900", "postgres", "laya")
REQUIRED_CPUS = 3
REQUIRED_MEMORY_GIB = 6  # Two service caps (4 + 1 GiB) and a 1 GiB host reserve.
SAFE_OUTPUT_BYTES = 4096


class InfraError(RuntimeError):
    """A stable, value-free configuration or readiness failure."""

    def __init__(self, code: str, key: str | None = None):
        self.code = code
        self.key = key
        super().__init__(f"{code}: {key}" if key else code)


def _dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key in {"POSTGRES_PASSWORD", "DATABASE_URL", "LAYA_API_KEY", "LAYA_BASE_URL"}:
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            values[key] = value
    return values


def _configured(value: str | None) -> bool:
    return bool(value and value.strip() and not any(marker in value.upper() for marker in ("REPLACE", "PLACEHOLDER", "CHANGEME", "YOUR_")))


def _validate_database_url(url: str, password: str) -> None:
    try:
        parsed = urlsplit(url)
        valid = (parsed.scheme in {"postgresql", "postgres"} and parsed.hostname == "127.0.0.1"
                 and parsed.port == 5432 and parsed.username == "harnessarena"
                 and parsed.path == "/harnessarena" and unquote(parsed.password or "") == password
                 and not parsed.query and not parsed.fragment)
    except ValueError:
        valid = False
    if not valid:
        raise InfraError("invalid_local_configuration", "DATABASE_URL")


def ensure_env(path: Path) -> dict[str, str]:
    """Append missing local settings once; never replace an existing entry."""
    path = Path(path)
    values = _dotenv(path)
    for key in ("POSTGRES_PASSWORD", "DATABASE_URL", "LAYA_API_KEY", "LAYA_BASE_URL"):
        if key in values and not _configured(values[key]):
            raise InfraError("empty_or_placeholder_configuration", key)
    additions: dict[str, str] = {}
    password = values.get("POSTGRES_PASSWORD")
    if password is None:
        existing_url = values.get("DATABASE_URL")
        if existing_url:
            try:
                password = unquote(urlsplit(existing_url).password or "")
            except ValueError:
                password = ""
            if not _configured(password):
                raise InfraError("invalid_local_configuration", "DATABASE_URL")
        else:
            password = secrets.token_urlsafe(32)
        additions["POSTGRES_PASSWORD"] = password
    if "DATABASE_URL" not in values:
        additions["DATABASE_URL"] = f"postgresql://harnessarena:{quote(password, safe='')}@127.0.0.1:5432/harnessarena"
    if "LAYA_API_KEY" not in values:
        additions["LAYA_API_KEY"] = secrets.token_urlsafe(32)
    if "LAYA_BASE_URL" not in values:
        additions["LAYA_BASE_URL"] = "http://127.0.0.1:8001"
    merged = values | additions
    _validate_database_url(merged["DATABASE_URL"], merged["POSTGRES_PASSWORD"])
    if merged["LAYA_BASE_URL"].rstrip("/") != "http://127.0.0.1:8001":
        raise InfraError("invalid_local_configuration", "LAYA_BASE_URL")
    if additions:
        path.parent.mkdir(parents=True, exist_ok=True)
        existing = path.read_text(encoding="utf-8") if path.exists() else ""
        separator = "" if not existing or existing.endswith(("\n", "\r")) else "\n"
        with path.open("a", encoding="utf-8") as stream:
            stream.write(separator + "".join(f"{key}={value}\n" for key, value in additions.items()))
    return merged


def validate_compose(path: Path) -> None:
    """Reject drift from the reviewed two-service, local CPU configuration."""
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        services = doc["services"]
        pg, laya = services["postgres"], services["laya"]
        valid = (
            pg.get("image") == "postgres:17.6" and pg.get("profiles") == ["control"]
            and pg.get("ports") == ["127.0.0.1:5432:5432"]
            and "postgres-data:/var/lib/postgresql/data" in pg.get("volumes", [])
            and float(pg.get("cpus")) == 1 and str(pg.get("mem_limit")).lower() == "1g"
            and laya.get("profiles") == ["decision"]
            and laya.get("build", {}).get("context") == "https://github.com/NandhaKishorM/laya.git#68804629e8ccd9d616d48a40e87de9fabbeae069"
            and laya.get("ports") == ["127.0.0.1:8001:8000"]
            and "laya-model-cache:/home/laya/.cache/huggingface" in laya.get("volumes", [])
            and float(laya.get("cpus")) == 2 and str(laya.get("mem_limit")).lower() == "4g"
            and laya.get("environment", {}).get("LAYA_DEVICE") == "cpu"
            and laya.get("environment", {}).get("LAYA_MODELS") == "typed-decisions"
            and json.loads(laya.get("environment", {}).get("LAYA_EXTRA_MODELS", ""))
                == {"typed-decisions": "convaiinnovations/laya-typed-decisions"}
            and laya.get("environment", {}).get("LAYA_REVISION") == PINNED_TYPED_REVISION
            and laya.get("environment", {}).get("HF_HOME") == "/home/laya/.cache/huggingface"
            and all(name in doc.get("volumes", {}) for name in ("postgres-data", "laya-model-cache"))
        )
    except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError):
        valid = False
    if not valid:
        raise InfraError("compose_configuration_mismatch")


def check_host(probe: Mapping[str, Any]) -> dict[str, Any]:
    info = probe.get("docker_info") if isinstance(probe.get("docker_info"), Mapping) else {}
    endpoint = probe.get("docker_endpoint") if isinstance(probe.get("docker_endpoint"), Mapping) else {}
    cli = probe.get("docker_cli") if isinstance(probe.get("docker_cli"), Mapping) else {}
    compose = probe.get("compose") if isinstance(probe.get("compose"), Mapping) else {}
    try:
        cpus = float(info.get("NCPU", 0))
        memory_gib = float(info.get("MemTotal", 0)) / GIB
    except (TypeError, ValueError, OverflowError):
        cpus, memory_gib = 0, 0
    if not math.isfinite(cpus) or not math.isfinite(memory_gib):
        cpus, memory_gib = 0, 0
    checks = {
        "docker_cli": cli.get("available") is True,
        "compose": compose.get("available") is True,
        "local_endpoint": endpoint.get("local") is True and endpoint.get("kind") in {"local_named_pipe", "local_unix_socket"},
        "linux_engine": info.get("OSType") == "linux",
        "cpu_capacity": cpus >= REQUIRED_CPUS,
        "memory_capacity": memory_gib >= REQUIRED_MEMORY_GIB,
    }
    return {"ready": all(checks.values()), "checks": checks, "cpus": cpus, "memory_gib": round(memory_gib, 2),
            "required_cpus": REQUIRED_CPUS, "required_memory_gib": REQUIRED_MEMORY_GIB}


def resolve_docker(override: str | None = None) -> str:
    if override:
        if Path(override).is_file():
            return override
        raise InfraError("docker_cli_unavailable")
    found = shutil.which("docker")
    if found:
        return found
    for base in (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)")):
        if base:
            candidate = Path(base) / "Docker" / "Docker" / "resources" / "bin" / "docker.exe"
            if candidate.is_file():
                return str(candidate)
    local = os.environ.get("LOCALAPPDATA")
    if local:
        candidate = Path(local) / "Programs" / "DockerDesktop" / "resources" / "bin" / "docker.exe"
        if candidate.is_file():
            return str(candidate)
    raise InfraError("docker_cli_unavailable")


def _command(runner: Callable[..., Any], args: list[str], timeout: int, cwd: Path,
             env: Mapping[str, str] | None = None) -> str:
    try:
        result = runner(args, capture_output=True, text=True, timeout=timeout, check=False, cwd=cwd, env=env)
    except (OSError, subprocess.SubprocessError):
        raise InfraError("docker_command_unavailable") from None
    if result.returncode != 0:
        raise InfraError("docker_command_failed")
    return str(result.stdout or "")[:SAFE_OUTPUT_BYTES].strip()


def _runtime_caps(docker: str, root: Path, runner: Callable[..., Any],
                  compose_env: Mapping[str, str]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for service, cpus, memory_gib, port in (("postgres", 1, 1, "5432/tcp"), ("laya", 2, 4, "8000/tcp")):
        container = _command(runner, [docker, *COMPOSE_PREFIX, "ps", "-q", service], 20, root, compose_env)
        if not re.fullmatch(r"[0-9a-f]{12,64}", container):
            raise InfraError("service_not_running", service)
        template = "{{json .HostConfig.NanoCpus}}|{{json .HostConfig.Memory}}|{{json .State.Status}}|{{json .State.Health.Status}}|{{json .HostConfig.PortBindings}}"
        raw = _command(runner, [docker, "inspect", "--format", template, container], 20, root, compose_env)
        try:
            nano, memory, status, health, bindings = (json.loads(part) for part in raw.split("|"))
            bound = bindings[port]
            valid = (0 < nano <= cpus * 1_000_000_000 and 0 < memory <= memory_gib * GIB
                     and status == "running" and health == "healthy" and len(bound) == 1
                     and bound[0]["HostIp"] == "127.0.0.1"
                     and bound[0]["HostPort"] == ("5432" if service == "postgres" else "8001"))
        except (ValueError, KeyError, TypeError, IndexError):
            valid = False
        if not valid:
            raise InfraError("runtime_limit_or_health_mismatch", service)
        result[service] = {"healthy": True, "cpu_cap": cpus, "memory_cap_gib": memory_gib, "loopback": True}
    return result


def verify_services(config: Mapping[str, str], *, db_connect: Callable[..., Any] | None = None,
                    laya_transport: Callable[..., Any] | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"ready": False, "postgres": "unavailable", "laya": "unavailable"}
    try:
        if db_connect is None:
            import psycopg
            db_connect = psycopg.connect
        with db_connect(config["DATABASE_URL"], connect_timeout=5) as connection:
            row = connection.execute("SELECT current_database(), current_user, current_setting('server_version')").fetchone()
        if row and row[0] == "harnessarena" and row[1] == "harnessarena" and re.match(r"^17\.6(?:\s|$)", str(row[2])):
            result["postgres"] = "authenticated"
            result["postgres_version"] = str(row[2]).split()[0]
    except Exception:
        result["postgres_error"] = "connection_or_query_failed"
    try:
        client = LayaDecisionClient(config["LAYA_API_KEY"], config["LAYA_BASE_URL"], transport=laya_transport)
        health = client.health()
        state, questions = synthetic_case()
        choice = client.predict(state, questions)
        result["laya"] = "typedHTTPverified"
        result["laya_device"] = health.device
        result["laya_checkpoint"] = choice.checkpoint
        result["laya_revision"] = choice.revision
        result["typed_outcome"] = choice.outcome
    except LayaUnavailable as error:
        result["laya_error"] = error.code
    except Exception:
        result["laya_error"] = "typed_probe_failed"
    result["ready"] = result["postgres"] == "authenticated" and result["laya"] == "typedHTTPverified"
    return result


def _live_verification(config: Mapping[str, str], docker: str, root: Path,
                       runner: Callable[..., Any], compose_env: Mapping[str, str]) -> dict[str, Any]:
    runtime = _runtime_caps(docker, root, runner, compose_env)
    services = verify_services(config)
    services["runtime"] = runtime
    return services


def _write_report(path: Path, report: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def run(action: str, *, root: Path = ROOT, env_path: Path | None = None, report_path: Path | None = None,
        docker_executable: str | None = None, wait_timeout: int = 900,
        command_runner: Callable[..., Any] = subprocess.run,
        verify_live: Callable[..., dict[str, Any]] = _live_verification) -> dict[str, Any]:
    root = Path(root)
    report_path = Path(report_path) if report_path else root / DEFAULT_REPORT
    report: dict[str, Any] = {"timestamp": datetime.now(timezone.utc).isoformat(), "action": action,
                              "status": "blocked", "host": None, "services": None}
    try:
        if action not in {"start", "verify"} or not 1 <= wait_timeout <= 3600:
            raise InfraError("invalid_arguments")
        config = ensure_env(Path(env_path) if env_path else root / ".env")
        validate_compose(root / "compose.yaml")
        compose_env = os.environ.copy()
        compose_env.update({key: config[key] for key in ("POSTGRES_PASSWORD", "LAYA_API_KEY")})
        docker = resolve_docker(docker_executable)
        host = check_host(collect_host_probe(docker_executable=docker, command_runner=command_runner,
                                             environ=compose_env))
        report["host"] = host
        if not host["ready"]:
            raise InfraError("host_not_ready")
        if action == "start":
            command = [docker, *COMPOSE_PREFIX, "up", "--build", "-d", "--wait", "--wait-timeout", str(wait_timeout), "postgres", "laya"]
            # Explicit environment prevents ambient credentials from overriding ignored .env.
            _command(command_runner, command, wait_timeout + 120, root, compose_env)
        services = verify_live(config, docker, root, command_runner, compose_env)
        report["services"] = services
        if not services.get("ready"):
            raise InfraError("service_verification_failed")
        report["status"] = "verified"
    except InfraError as error:
        report["error"] = {"code": error.code, **({"key": error.key} if error.key else {})}
    except (OSError, ValueError):
        report["error"] = {"code": "local_infrastructure_unavailable"}
    _write_report(report_path, report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("start", "verify"))
    parser.add_argument("--docker-executable")
    parser.add_argument("--wait-timeout", type=int, default=900)
    args = parser.parse_args(argv)
    report = run(args.action, docker_executable=args.docker_executable, wait_timeout=args.wait_timeout)
    if report["status"] == "verified":
        print(f"infrastructure=verified report={DEFAULT_REPORT}")
        return 0
    print(f"infrastructure=blocked error={report.get('error', {}).get('code', 'unknown')} report={DEFAULT_REPORT}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
