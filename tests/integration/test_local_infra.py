"""Offline contract checks for the two-service local infrastructure workflow."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from scripts import local_infra
from prototypes.laya.probe import synthetic_case


ROOT = Path(__file__).resolve().parents[2]


def _env(tmp_path):
    path = tmp_path / ".env"
    path.write_text("OTHER_USER_SETTING=retain-me\nPOSTGRES_PASSWORD=strong-existing\nLAYA_API_KEY=existing-key\n", encoding="utf-8")
    return path


def _probe(memory_gib=7.46, cpus=12, local=True):
    return {
        "docker_cli": {"available": True, "path_present": True, "version": "29.8.2"},
        "compose": {"available": True, "version": "5.5.1"},
        "docker_endpoint": {"local": local, "kind": "local_named_pipe" if local else "remote"},
        "docker_info": {"OSType": "linux", "NCPU": cpus, "MemTotal": int(memory_gib * 1024**3)},
    }


def test_init_preserves_existing_values_and_is_idempotent(tmp_path):
    path = _env(tmp_path)
    first = local_infra.ensure_env(path)
    contents = path.read_text(encoding="utf-8")
    second = local_infra.ensure_env(path)
    assert first["POSTGRES_PASSWORD"] == "strong-existing"
    assert first["LAYA_API_KEY"] == "existing-key"
    assert first["DATABASE_URL"].startswith("postgresql://harnessarena:strong-existing@127.0.0.1:5432/")
    assert path.read_text(encoding="utf-8") == contents
    assert second == first
    assert "OTHER_USER_SETTING=retain-me" in contents


@pytest.mark.parametrize("line,key", [
    ("POSTGRES_PASSWORD=\n", "POSTGRES_PASSWORD"),
    ("LAYA_API_KEY=REPLACE_LOCALLY\n", "LAYA_API_KEY"),
    ("DATABASE_URL=postgresql://harnessarena:REPLACE_LOCALLY@127.0.0.1:5432/harnessarena\n", "DATABASE_URL"),
])
def test_empty_or_placeholder_configuration_fails_without_values(tmp_path, line, key):
    path = tmp_path / ".env"
    path.write_text(line, encoding="utf-8")
    with pytest.raises(local_infra.InfraError) as error:
        local_infra.ensure_env(path)
    assert key in str(error.value)
    assert "REPLACE_LOCALLY" not in str(error.value)


def test_capacity_and_remote_endpoint_fail_closed():
    assert local_infra.check_host(_probe())["ready"]
    assert not local_infra.check_host(_probe(memory_gib=5.99))["ready"]
    assert not local_infra.check_host(_probe(cpus=2))["ready"]
    assert not local_infra.check_host(_probe(local=False))["ready"]


def test_start_uses_only_two_services_and_no_destructive_command(tmp_path, monkeypatch):
    env_path = _env(tmp_path)
    commands = []
    monkeypatch.setattr(local_infra, "collect_host_probe", lambda **kwargs: _probe())
    monkeypatch.setattr(local_infra, "resolve_docker", lambda *_args, **_kwargs: "docker")

    def runner(command, **kwargs):
        commands.append(command)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    report = local_infra.run("start", root=ROOT, env_path=env_path, report_path=tmp_path / "status.json", command_runner=runner, verify_live=lambda *_args, **_kwargs: {"ready": True, "postgres": "authenticated", "laya": "typedHTTPverified"})
    assert report["status"] == "verified"
    assert ["docker", "compose", "--profile", "control", "--profile", "decision", "up", "--build", "-d", "--wait", "--wait-timeout", "900", "postgres", "laya"] in commands
    assert all("down" not in c and "prune" not in c and "rm" not in c for c in commands)
    assert all("strong-existing" not in str(c) and "existing-key" not in str(c) for c in commands)


def test_compose_uses_validated_credentials_despite_ambient_overrides(tmp_path, monkeypatch):
    env_path = _env(tmp_path)
    monkeypatch.setenv("POSTGRES_PASSWORD", "wrong-ambient-pg")
    monkeypatch.setenv("LAYA_API_KEY", "wrong-ambient-laya")
    monkeypatch.setenv("DOCKER_CONTEXT", "desktop-linux")
    monkeypatch.setattr(local_infra, "resolve_docker", lambda *_args, **_kwargs: "docker")
    observed = []

    def collect(**kwargs):
        observed.append(("probe", kwargs["environ"]))
        return _probe()

    def runner(command, **kwargs):
        observed.append(("command", kwargs["env"]))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    def verify(config, docker, root, runner, compose_env):
        observed.append(("verify", compose_env))
        return {"ready": True, "postgres": "authenticated", "laya": "typedHTTPverified"}

    monkeypatch.setattr(local_infra, "collect_host_probe", collect)
    report = local_infra.run("start", root=ROOT, env_path=env_path, report_path=tmp_path / "status.json", command_runner=runner, verify_live=verify)
    assert report["status"] == "verified"
    for _, env in observed:
        assert env["POSTGRES_PASSWORD"] == "strong-existing"
        assert env["LAYA_API_KEY"] == "existing-key"
        assert env["DOCKER_CONTEXT"] == "desktop-linux"
    assert "wrong-ambient" not in (tmp_path / "status.json").read_text(encoding="utf-8")


def test_compose_model_mapping_drift_blocks_startup(tmp_path):
    compose = yaml.safe_load((ROOT / "compose.yaml").read_text(encoding="utf-8"))
    path = tmp_path / "compose.yaml"
    path.write_text(yaml.safe_dump(compose), encoding="utf-8")
    local_infra.validate_compose(path)
    compose["services"]["laya"]["environment"]["LAYA_EXTRA_MODELS"] = '{"typed-decisions":"wrong/model"}'
    path.write_text(yaml.safe_dump(compose), encoding="utf-8")
    with pytest.raises(local_infra.InfraError, match="compose_configuration_mismatch"):
        local_infra.validate_compose(path)
    _env(tmp_path)
    report = local_infra.run("start", root=tmp_path, report_path=tmp_path / "status.json",
                             command_runner=lambda *_args, **_kwargs: pytest.fail("invalid mapping must block before Docker"))
    assert report["status"] == "blocked"
    assert report["error"]["code"] == "compose_configuration_mismatch"


def test_synthetic_case_is_public_and_returns_independent_copies():
    state, questions = synthetic_case()
    state["metric_examples"][0]["latency_ms"] = -1
    questions["pair"]["criteria"].clear()
    new_state, new_questions = synthetic_case()
    assert new_state["metric_examples"][0]["latency_ms"] == 120
    assert len(new_questions["pair"]["criteria"]) == 4


def test_verify_requires_authenticated_database_and_real_typed_probe(tmp_path, monkeypatch):
    env_path = _env(tmp_path)
    config = local_infra.ensure_env(env_path)
    db_queries = []

    class Connection:
        def __enter__(self): return self
        def __exit__(self, *_args): pass
        def execute(self, query):
            db_queries.append(query)
            return SimpleNamespace(fetchone=lambda: ("harnessarena", "harnessarena", "17.6"))

    def connect(url, **kwargs):
        assert url == config["DATABASE_URL"]
        assert kwargs["connect_timeout"] <= 5
        return Connection()

    def transport(method, url, headers, body, timeout, max_bytes):
        assert headers["Authorization"] == "Bearer existing-key"
        if url.endswith("/health"):
            return 200, json.dumps({"status": "ok", "loaded": ["typed-decisions"], "revisions": {"typed-decisions": local_infra.PINNED_TYPED_REVISION}, "device": "cpu", "device_is_preference": False, "checkpoint_devices": {"typed-decisions": "cpu"}}).encode()
        return 503, b""

    result = local_infra.verify_services(config, db_connect=connect, laya_transport=transport)
    assert result["postgres"] == "authenticated"
    assert result["laya"] == "unavailable"
    assert not result["ready"]
    assert db_queries == ["SELECT current_database(), current_user, current_setting('server_version')"]


def test_verify_accepts_authenticated_sql_and_cpu_typed_response(tmp_path):
    config = local_infra.ensure_env(_env(tmp_path))

    class Connection:
        def __enter__(self): return self
        def __exit__(self, *_args): pass
        def execute(self, query):
            assert query.startswith("SELECT ")
            return SimpleNamespace(fetchone=lambda: ("harnessarena", "harnessarena", "17.6 (Debian)"))

    def transport(method, url, headers, body, timeout, max_bytes):
        assert url.startswith("http://127.0.0.1:8001/")
        if url.endswith("/health"):
            payload = {"status": "ok", "loaded": ["typed-decisions"], "revisions": {"typed-decisions": local_infra.PINNED_TYPED_REVISION}, "device": "cpu", "device_is_preference": False, "checkpoint_devices": {"typed-decisions": "cpu"}}
        else:
            assert json.loads(body)["model"] == "typed-decisions"
            payload = {"model": "laya-rl-agent", "routing": {"model": "typed-decisions"}, "answers": {"pair": {"type": "choice", "choice": "candidate_a", "probabilities": {"candidate_a": 0.7, "candidate_b": 0.1, "equivalent": 0.1, "insufficient_evidence": 0.1}, "confidence": 0.2}}, "usage": {"input_tokens": 12, "output_tokens": 2}}
        return 200, json.dumps(payload).encode()

    result = local_infra.verify_services(config, db_connect=lambda *_args, **_kwargs: Connection(), laya_transport=transport)
    assert result["ready"]
    assert result["postgres"] == "authenticated"
    assert result["laya"] == "typedHTTPverified"
    assert result["laya_device"] == "cpu"
    assert result["typed_outcome"] == "candidate_a"


def test_runtime_inspection_requires_both_caps_and_loopback_ports():
    commands = []

    compose_env = {"DOCKER_CONTEXT": "desktop-linux", "POSTGRES_PASSWORD": "validated"}

    def runner(command, **kwargs):
        commands.append(command)
        assert kwargs["env"] is compose_env
        if command[-2:] == ["-q", "postgres"]:
            output = "a" * 64
        elif command[-2:] == ["-q", "laya"]:
            output = "b" * 64
        else:
            service = "postgres" if command[-1] == "a" * 64 else "laya"
            port = "5432/tcp" if service == "postgres" else "8000/tcp"
            host_port = "5432" if service == "postgres" else "8001"
            output = "|".join(json.dumps(value) for value in (
                (1 if service == "postgres" else 2) * 1_000_000_000,
                (1 if service == "postgres" else 4) * 1024**3,
                "running", "healthy", {port: [{"HostIp": "127.0.0.1", "HostPort": host_port}]},
            ))
        return SimpleNamespace(returncode=0, stdout=output, stderr="")

    assert local_infra._runtime_caps("docker", ROOT, runner, compose_env)["laya"]["loopback"]
    assert len(commands) == 4


def test_report_contains_only_safe_fields(tmp_path, monkeypatch):
    env_path = _env(tmp_path)
    monkeypatch.setattr(local_infra, "collect_host_probe", lambda **kwargs: _probe(memory_gib=5))
    monkeypatch.setattr(local_infra, "resolve_docker", lambda *_args, **_kwargs: "docker")
    output = tmp_path / "status.json"
    report = local_infra.run("start", root=ROOT, env_path=env_path, report_path=output, command_runner=lambda *_args, **_kwargs: pytest.fail("startup must be blocked"))
    assert report["status"] == "blocked"
    serialized = output.read_text(encoding="utf-8")
    assert "existing-key" not in serialized
    assert "strong-existing" not in serialized
    assert "DATABASE_URL" not in serialized
