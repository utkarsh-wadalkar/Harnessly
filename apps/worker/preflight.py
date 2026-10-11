"""Secret-safe local Docker host readiness checks."""

from __future__ import annotations

import argparse
import json
import math
import os
import platform
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

OUTPUT_LIMIT = 16_384
COMMAND_TIMEOUT_SECONDS = 8
GIB = 1024**3
DOCKER_INFO_FIELDS = ("OSType", "NCPU", "MemTotal", "ServerVersion", "Driver")
DOCKER_INFO_FORMAT = "{{json .OSType}}\t{{json .NCPU}}\t{{json .MemTotal}}\t{{json .ServerVersion}}\t{{json .Driver}}"
DOCKER_INFO_PROVENANCE = "docker info projected JSON fields: " + ",".join(DOCKER_INFO_FIELDS)
LOCAL_ENDPOINT_KINDS = {"local_named_pipe", "local_unix_socket"}
SAFE_ENDPOINT_KINDS = LOCAL_ENDPOINT_KINDS | {"remote", "unknown"}
_CONTEXT_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")

DEFAULT_QUOTAS: dict[str, float | int] = {
    "laya_cpus": 2,
    "laya_memory_gib": 4,
    "control_cpus": 1,
    "control_memory_gib": 1,
    "benchmark_cpus": 1,
    "benchmark_memory_gib": 2,
    "benchmark_concurrency": 1,
}


def _validated_quotas(quotas: Mapping[str, Any] | None) -> dict[str, float | int]:
    result = dict(DEFAULT_QUOTAS)
    if quotas is not None:
        unknown = set(quotas) - set(result)
        if unknown:
            raise ValueError(f"unknown quota key: {sorted(unknown)[0]}")
        result.update(quotas)
    for name, value in result.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
            raise ValueError(f"{name} must be a positive finite number")
        try:
            finite_value = float(value)
        except (OverflowError, ValueError):
            raise ValueError(f"{name} must be a positive finite number") from None
        if not math.isfinite(finite_value):
            raise ValueError(f"{name} must be a positive finite number")
        if name == "benchmark_concurrency":
            if not isinstance(value, int):
                raise ValueError("benchmark_concurrency must be a positive integer")
            if value > sys.maxsize:
                raise ValueError("benchmark_concurrency exceeds the supported range")
        else:
            result[name] = finite_value
    return result


def _parse_json(value: Any) -> dict[str, Any] | None:
    if isinstance(value, Mapping):
        return dict(value)
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except (TypeError, ValueError):
            return None
        return dict(parsed) if isinstance(parsed, Mapping) else None
    return None


def _parse_docker_info_projection(output: Any) -> dict[str, Any] | None:
    fields = _decode_output(output).strip().split("\t")
    if len(fields) != len(DOCKER_INFO_FIELDS):
        return None
    try:
        values = [json.loads(field) for field in fields]
    except (TypeError, ValueError):
        return None
    return dict(zip(DOCKER_INFO_FIELDS, values))


def _check(name: str, status: str, message: str, provenance: str = "host probe") -> dict[str, str]:
    return {"name": name, "status": status, "message": message, "provenance": provenance}


def assess_host(probe: Mapping[str, Any], quotas: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Assess injected host evidence without trusting or returning raw command output."""
    q = _validated_quotas(quotas)
    checks: list[dict[str, str]] = []
    raw_platform = str(probe.get("platform", "unknown"))
    evidence: dict[str, Any] = {"platform": raw_platform if raw_platform in {"Windows", "Linux", "Darwin"} else "unknown"}
    platform_name = str(probe.get("platform", "")).lower()

    cli = probe.get("docker_cli")
    cli = cli if isinstance(cli, Mapping) else {}
    cli_path_present = cli.get("path_present", cli.get("available") is True) is True
    cli_version = _docker_cli_version(cli.get("version"))
    cli_available = cli.get("available") is True and cli_version is not None
    checks.append(_check("docker_cli", "pass" if cli_available else "fail", "Docker CLI is present and its version command succeeded." if cli_available else "Docker CLI is missing or unreadable; install it or verify `docker --version`."))
    evidence["docker_cli"] = {"path_present": cli_path_present, "version": cli_version}

    endpoint = probe.get("docker_endpoint")
    endpoint = endpoint if isinstance(endpoint, Mapping) else {}
    endpoint_kind = endpoint.get("kind") if endpoint.get("kind") in SAFE_ENDPOINT_KINDS else "unknown"
    endpoint_local = endpoint.get("local") is True and endpoint_kind in LOCAL_ENDPOINT_KINDS
    checks.append(_check(
        "docker_endpoint",
        "pass" if endpoint_local else "fail",
        "Active Docker endpoint is a recognized local pipe or Unix socket." if endpoint_local else "Docker endpoint locality is remote or unverified; select a verified local Docker endpoint.",
        "docker context inspect and Docker endpoint environment",
    ))
    evidence["docker_endpoint"] = {"local": endpoint_local, "kind": endpoint_kind}

    compose = probe.get("compose")
    compose = compose if isinstance(compose, Mapping) else {}
    compose_version = _compose_version(compose.get("version"))
    compose_available = compose.get("available") is True and compose_version is not None
    checks.append(_check("compose", "pass" if compose_available else "fail", "Docker Compose is available." if compose_available else "Install the Docker Compose plugin and verify `docker compose version`."))
    if compose_available:
        evidence["compose"] = {"version": compose_version}

    info = _parse_json(probe.get("docker_info"))
    info_error = probe.get("docker_info_error")
    engine_ok = cli_path_present and info is not None and not info_error
    engine_message = "Docker engine responded with valid JSON." if engine_ok else _failure_message(info_error, "Docker engine is unavailable or returned invalid JSON; start Docker Desktop/Engine and retry.")
    checks.append(_check("docker_engine", "pass" if engine_ok else "fail", engine_message, DOCKER_INFO_PROVENANCE))

    resource_ok = False
    backend_ok = False
    if info is not None:
        ostype = str(info.get("OSType", "")).lower()
        safe_backend = ostype if ostype in {"linux", "windows"} else None
        backend_ok = safe_backend == "linux"
        checks.append(_check("docker_backend", "pass" if backend_ok else "fail", "Docker daemon uses the required Linux backend." if backend_ok else "Docker daemon must use the Linux backend."))
        cpus = _positive_finite(info.get("NCPU"))
        memory_bytes = _positive_finite(info.get("MemTotal"))
        try:
            required_cpus = q["laya_cpus"] + q["control_cpus"] + q["benchmark_cpus"] * q["benchmark_concurrency"]
            required_gib = q["laya_memory_gib"] + q["control_memory_gib"] + q["benchmark_memory_gib"] * q["benchmark_concurrency"] + 1
            required_bytes = required_gib * GIB
        except OverflowError:
            raise ValueError("configured workload requirements exceed the supported finite range") from None
        if not all(math.isfinite(float(value)) for value in (required_cpus, required_gib, required_bytes)):
            raise ValueError("configured workload requirements exceed the supported finite range")
        resource_ok = cpus is not None and memory_bytes is not None and cpus >= required_cpus and memory_bytes >= required_bytes
        if resource_ok:
            message = f"Docker reports {cpus:g} CPUs and {memory_bytes / GIB:g} GiB; configured workload plus 1 GiB reserve requires {required_cpus:g} CPUs and {required_gib:g} GiB."
        else:
            message = f"Docker must report valid CPU and memory totals meeting {required_cpus:g} CPUs and {required_gib:g} GiB (including 1 GiB reserve)."
        checks.append(_check("docker_resources", "pass" if resource_ok else "fail", message, "docker info projected fields: NCPU,MemTotal"))
        evidence["docker"] = {
            "backend": safe_backend,
            "cpus": cpus,
            "memory_gib": memory_bytes / GIB if memory_bytes is not None else None,
            "server_version": _exact_version(info.get("ServerVersion")),
            "storage_driver": _storage_driver(info.get("Driver")),
            "quota_required_cpus": required_cpus,
            "quota_required_memory_gib": required_gib,
        }
    else:
        checks.extend([
            _check("docker_backend", "unknown", "Backend cannot be determined without valid Docker engine information."),
            _check("docker_resources", "unknown", "CPU and memory capability cannot be determined without valid Docker engine information."),
        ])

    if platform_name.startswith("win") or platform_name == "windows":
        wsl = probe.get("wsl")
        wsl = wsl if isinstance(wsl, Mapping) else {}
        inventory = wsl.get("inventory")
        has_wsl2 = isinstance(inventory, list) and any(
            isinstance(item, Mapping) and str(item.get("version", "")) == "2" for item in inventory
        )
        wsl_ok = wsl.get("available") is True and has_wsl2
        checks.append(_check("wsl2", "pass" if wsl_ok else "fail", "WSL2 distribution inventory was read." if wsl_ok else "WSL inventory is unavailable or has no WSL2 distribution; enable WSL2 and retry."))
        if isinstance(inventory, list):
            evidence["wsl"] = {"inventory": [{"name": _safe_distribution(i.get("name")), "state": _wsl_state(i.get("state")), "version": _wsl_version(i.get("version"))} for i in inventory if isinstance(i, Mapping)]}

    ready = all(item["status"] == "pass" for item in checks)
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "ready" if ready else "blocked",
        "ready": ready,
        "checks": checks,
        "evidence": evidence,
        "scope_note": "Network, storage, and privilege safety are not verified by this preflight.",
    }


def _positive_finite(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        return None
    try:
        number = float(value)
    except (OverflowError, ValueError):
        return None
    return number if math.isfinite(number) else None


VERSION_PATTERN = r"v?\d+(?:\.\d+){1,3}(?:[-+][A-Za-z0-9.]+)?"
_EXACT_VERSION = re.compile(rf"^{VERSION_PATTERN}$")
_DOCKER_VERSION_LINE = re.compile(rf"^Docker version ({VERSION_PATTERN})(?:, build [A-Fa-f0-9]+)?$")
_COMPOSE_VERSION_LINE = re.compile(rf"^Docker Compose version ({VERSION_PATTERN})$")


def _exact_version(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value if _EXACT_VERSION.fullmatch(value) else None


def _docker_cli_version(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    if _EXACT_VERSION.fullmatch(value):
        return value
    match = _DOCKER_VERSION_LINE.fullmatch(value)
    return match.group(1) if match else None


def _compose_version(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    if _EXACT_VERSION.fullmatch(value):
        return value
    match = _COMPOSE_VERSION_LINE.fullmatch(value)
    return match.group(1) if match else None


def _storage_driver(value: Any) -> str | None:
    allowed = {"aufs", "btrfs", "devicemapper", "fuse-overlayfs", "overlay", "overlay2", "vfs", "windowsfilter", "zfs"}
    return value.lower() if isinstance(value, str) and value.lower() in allowed else None


def _safe_distribution(value: Any) -> str:
    if not isinstance(value, str):
        return "other"
    label = value.strip()
    if label in {"docker-desktop", "docker-desktop-data", "Debian", "kali-linux"}:
        return label
    if re.fullmatch(r"Ubuntu(?:-\d{2}\.\d{2})?", label):
        return label
    return "other"


def _wsl_state(value: Any) -> str | None:
    return value.title() if isinstance(value, str) and value.lower() in {"running", "stopped"} else None


def _wsl_version(value: Any) -> str | None:
    text = str(value) if isinstance(value, (int, str)) and not isinstance(value, bool) else ""
    return text if text in {"1", "2"} else None


def _first_line(value: Any) -> str | None:
    text = _decode_output(value).splitlines()
    return text[0][:OUTPUT_LIMIT] if text else None


def _failure_message(error: Any, fallback: str) -> str:
    # Never expose stderr, exception text, command output, or credential-like material.
    if error in ("timeout", "timed_out"):
        return "Docker engine probe timed out; start Docker Desktop/Engine and retry."
    return fallback


def _decode_output(value: Any) -> str:
    if isinstance(value, bytes):
        encoding = "utf-16-le" if b"\x00" in value else "utf-8"
        return value.decode(encoding, errors="replace")
    return str(value or "")


def _wsl_inventory(output: Any) -> list[dict[str, str]]:
    text = _decode_output(output).replace("\x00", "").lstrip("\ufeff")
    rows = []
    for line in text.splitlines():
        stripped = line.strip().lstrip("* ").strip()
        match = re.match(r"(.+?)\s+(Running|Stopped)\s+(\d+)\s*$", stripped, re.IGNORECASE)
        if match:
            rows.append({
                "name": _safe_distribution(match.group(1).strip()),
                "state": _wsl_state(match.group(2)),
                "version": _wsl_version(match.group(3)),
            })
    return rows


def _classify_endpoint(value: Any) -> str:
    if not isinstance(value, str):
        return "unknown"
    endpoint = value.strip().lower()
    if endpoint in {
        "npipe:////./pipe/docker_engine",
        "npipe:////./pipe/dockerdesktoplinuxengine",
    }:
        return "local_named_pipe"
    if endpoint.startswith("unix://"):
        path = endpoint[len("unix://"):]
        if path.startswith("/") and ".." not in path.split("/") and not any(ch in path for ch in "?#@"):
            return "local_unix_socket"
        return "unknown"
    if endpoint.startswith(("ssh://", "tcp://", "http://", "https://")):
        return "remote"
    return "unknown"


def _collect_endpoint(
    command_runner: Callable[..., Any],
    docker_path: str,
    environ: Mapping[str, str],
) -> dict[str, Any]:
    selected_context = environ.get("DOCKER_CONTEXT")
    if selected_context:
        if not isinstance(selected_context, str) or not _CONTEXT_NAME.fullmatch(selected_context):
            return {"local": False, "kind": "unknown"}
    else:
        shown = _run_probe(command_runner, [docker_path, "context", "show"])
        selected_context = _first_line(shown.get("stdout")) if shown.get("ok") else None
        if not selected_context or not _CONTEXT_NAME.fullmatch(selected_context):
            return {"local": False, "kind": "unknown"}

    inspected = _run_probe(command_runner, [
        docker_path,
        "context",
        "inspect",
        "--format",
        "{{.Endpoints.docker.Host}}",
        selected_context,
    ])
    context_kind = _classify_endpoint(_first_line(inspected.get("stdout"))) if inspected.get("ok") else "unknown"

    docker_host_present = "DOCKER_HOST" in environ and environ.get("DOCKER_HOST") not in (None, "")
    host_kind = _classify_endpoint(environ.get("DOCKER_HOST")) if docker_host_present else None
    kinds = [context_kind] + ([host_kind] if docker_host_present else [])
    if "remote" in kinds:
        return {"local": False, "kind": "remote"}
    if any(kind not in LOCAL_ENDPOINT_KINDS for kind in kinds):
        return {"local": False, "kind": "unknown"}
    # DOCKER_HOST overrides the active context endpoint for the CLI connection.
    return {"local": True, "kind": host_kind if docker_host_present else context_kind}


def _docker_candidates(environ: Mapping[str, str] | None = None) -> list[str]:
    candidates: list[str] = []
    env = environ if environ is not None else os.environ
    for key in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
        base = env.get(key)
        if base:
            candidates.append(str(Path(base) / "Docker" / "Docker" / "resources" / "bin" / "docker.exe"))
    local = env.get("LOCALAPPDATA")
    if local:
        candidates.append(str(Path(local) / "Programs" / "DockerDesktop" / "resources" / "bin" / "docker.exe"))
    return candidates


def collect_host_probe(
    *,
    docker_executable: str | None = None,
    command_runner: Callable[..., Any] = subprocess.run,
    platform_name: str | None = None,
    which: Callable[[str], str | None] = shutil.which,
    file_exists: Callable[[str], bool] = os.path.isfile,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Collect bounded CLI evidence. The runner is injectable for offline callers/tests."""
    host = platform_name or sys.platform
    windows = host.lower().startswith("win") or host.lower() == "windows"
    probe_env = environ if environ is not None else os.environ
    path = docker_executable
    invalid_override = False
    if path is not None:
        if not file_exists(path):
            invalid_override = True
            path = None
    else:
        path = which("docker")
        if path is None and windows:
            path = next((candidate for candidate in _docker_candidates(environ) if file_exists(candidate)), None)

    result: dict[str, Any] = {"platform": "Windows" if windows else ("Linux" if host.lower().startswith("linux") else platform.system())}
    if invalid_override:
        result["docker_cli_error"] = "invalid_override"
    if not path:
        result["docker_cli"] = {"available": False, "path_present": False}
        env_host = probe_env.get("DOCKER_HOST")
        env_kind = _classify_endpoint(env_host) if env_host else "unknown"
        result["docker_endpoint"] = {"local": False, "kind": "remote" if env_kind == "remote" else "unknown"}
    else:
        result["docker_cli"] = {"available": False, "path_present": True}
        version = _run_probe(command_runner, [path, "--version"])
        version_token = _docker_cli_version(_first_line(version.get("stdout"))) if version.get("ok") else None
        result["docker_cli"]["version"] = version_token
        result["docker_cli"]["available"] = version_token is not None
        info = _run_probe(command_runner, [path, "info", "--format", DOCKER_INFO_FORMAT])
        if info.get("ok"):
            parsed_info = _parse_docker_info_projection(info.get("stdout"))
            if parsed_info is None:
                result["docker_info_error"] = "invalid_projection"
            else:
                result["docker_info"] = parsed_info
        else:
            result["docker_info_error"] = info.get("error", "command_failed")
        compose = _run_probe(command_runner, [path, "compose", "version"])
        compose_token = _compose_version(_first_line(compose.get("stdout"))) if compose.get("ok") else None
        result["compose"] = {"available": compose_token is not None, "version": compose_token}
        result["docker_endpoint"] = _collect_endpoint(command_runner, path, probe_env)

    if windows:
        wsl = which("wsl")
        if not wsl:
            result["wsl"] = {"available": False, "error": "missing"}
        else:
            inventory = _run_probe(command_runner, [wsl, "--list", "--verbose"])
            result["wsl"] = {"available": inventory.get("ok"), "inventory": _wsl_inventory(inventory.get("stdout")) if inventory.get("ok") else []}
    return result


def _run_probe(command_runner: Callable[..., Any], args: list[str]) -> dict[str, Any]:
    try:
        completed = command_runner(args, capture_output=True, timeout=COMMAND_TIMEOUT_SECONDS, check=False)
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "timeout"}
    except (OSError, subprocess.SubprocessError):
        return {"ok": False, "error": "command_failed"}
    stdout = _decode_output(getattr(completed, "stdout", ""))[:OUTPUT_LIMIT]
    return {"ok": getattr(completed, "returncode", 1) == 0, "stdout": stdout, "error": None if getattr(completed, "returncode", 1) == 0 else "command_failed"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check local Docker host readiness without launching workloads.")
    parser.add_argument("--docker-executable", help="Path to a Docker CLI file")
    for name, default in DEFAULT_QUOTAS.items():
        parser.add_argument("--" + name.replace("_", "-"), type=int if name == "benchmark_concurrency" else float, default=default)
    args = parser.parse_args(argv)
    quotas = {name: getattr(args, name) for name in DEFAULT_QUOTAS}
    try:
        probe = collect_host_probe(docker_executable=args.docker_executable)
        result = assess_host(probe, quotas)
    except (ValueError, OverflowError) as exc:
        result = {"timestamp": datetime.now(timezone.utc).isoformat(), "status": "blocked", "ready": False, "checks": [_check("configuration", "fail", str(exc))], "evidence": {}}
    print(json.dumps(result, separators=(",", ":")))
    return 0 if result["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
