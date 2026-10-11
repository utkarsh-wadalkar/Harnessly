import json

import pytest

from apps.worker.preflight import assess_host, collect_host_probe, main


def ready_probe():
    return {
        "platform": "Windows",
        "docker_cli": {"available": True, "version": "Docker version 27.0"},
        "compose": {"available": True, "version": "Docker Compose version v2.29"},
        "docker_info": {
            "OSType": "linux",
            "NCPU": 8,
            "MemTotal": 16 * 1024**3,
            "ServerVersion": "27.0",
            "Driver": "overlay2",
        },
        "docker_endpoint": {"local": True, "kind": "local_named_pipe"},
        "wsl": {"available": True, "inventory": [{"name": "docker-desktop", "state": "Running", "version": 2}]},
    }


def projected_docker_info(ostype="linux", cpus=8, memory=16 * 1024**3, version="29.8.2", driver="overlay2"):
    return "\t".join(json.dumps(value) for value in (ostype, cpus, memory, version, driver)).encode()


def test_enough_linux_resources_and_windows_wsl2_are_ready():
    result = assess_host(ready_probe())
    assert result["ready"] is True
    assert result["status"] == "ready"
    assert result["evidence"]["docker"]["server_version"] == "27.0"
    assert result["evidence"]["docker"]["storage_driver"] == "overlay2"


@pytest.mark.parametrize(
    ("probe", "check"),
    [
        ({"platform": "Linux", "docker_cli": {"available": False}}, "docker_cli"),
        ({"platform": "Linux", "docker_cli": {"available": True}, "docker_info_error": "connection refused"}, "docker_engine"),
        ({"platform": "Linux", "docker_cli": {"available": True}, "docker_info_error": "timeout"}, "docker_engine"),
        ({**ready_probe(), "docker_info": {"OSType": "windows", "NCPU": 8, "MemTotal": 16 * 1024**3}}, "docker_backend"),
        ({**ready_probe(), "docker_info": {"OSType": "linux", "NCPU": "bad", "MemTotal": 8}}, "docker_resources"),
        ({**ready_probe(), "docker_info": "not-json"}, "docker_engine"),
        ({**ready_probe(), "compose": {"available": False}}, "compose"),
        ({**ready_probe(), "docker_info": {"OSType": "linux", "NCPU": 2, "MemTotal": 5 * 1024**3}}, "docker_resources"),
    ],
)
def test_failed_or_insufficient_evidence_blocks_readiness(probe, check):
    result = assess_host(probe)
    assert result["ready"] is False
    assert check in {item["name"] for item in result["checks"] if item["status"] == "fail"}


@pytest.mark.parametrize("quotas", [{"laya_cpus": 0}, {"laya_memory_gib": float("nan")}, {"benchmark_concurrency": 1.5}])
def test_invalid_quota_configuration_is_rejected(quotas):
    with pytest.raises(ValueError):
        assess_host(ready_probe(), quotas=quotas)


def test_partial_probe_failure_keeps_other_evidence():
    probe = ready_probe()
    probe["docker_info_error"] = "timeout"
    result = assess_host(probe)
    assert result["ready"] is False
    assert result["evidence"]["docker_cli"]["version"] == "27.0"
    assert any(item["name"] == "compose" and item["status"] == "pass" for item in result["checks"])


def test_windows_readiness_requires_successful_wsl2_inventory():
    probe = {**ready_probe(), "platform": "Windows", "wsl": {"available": False, "error": "denied"}}
    result = assess_host(probe)
    assert result["ready"] is False
    assert any(item["name"] == "wsl2" and item["status"] == "fail" for item in result["checks"])


def test_output_does_not_echo_secret_like_command_output(capsys):
    result = assess_host({"platform": "Linux", "docker_cli": {"available": False, "raw": "TOKEN=super-secret-value"}})
    assert "super-secret-value" not in json.dumps(result)


def test_cli_emits_structured_json_and_nonzero_when_blocked(monkeypatch, capsys):
    monkeypatch.setattr("apps.worker.preflight.collect_host_probe", lambda **kwargs: {"platform": "Linux", "docker_cli": {"available": False}})
    code = main([])
    out = json.loads(capsys.readouterr().out)
    assert code != 0
    assert out["status"] == "blocked"


def test_windows_collection_uses_bounded_shell_free_commands_and_decodes_wsl_utf16():
    import subprocess

    calls = []

    def runner(args, **kwargs):
        calls.append((args, kwargs))
        if args[-2:] == ["--list", "--verbose"]:
            return subprocess.CompletedProcess(args, 0, stdout="NAME STATE VERSION\r\n* docker-desktop Running 2\r\n".encode("utf-16-le"))
        if args[1:] == ["--version"]:
            return subprocess.CompletedProcess(args, 0, stdout=b"Docker version 27.0\n")
        if "info" in args:
            return subprocess.CompletedProcess(args, 0, stdout=projected_docker_info())
        return subprocess.CompletedProcess(args, 0, stdout=b"Docker Compose version v2.29\n")

    probe = collect_host_probe(
        command_runner=runner,
        platform_name="Windows",
        which=lambda name: {"docker": "docker.exe", "wsl": "wsl.exe"}.get(name),
    )
    assert probe["wsl"]["inventory"] == [{"name": "docker-desktop", "state": "Running", "version": "2"}]
    assert all(call[1]["timeout"] > 0 and "shell" not in call[1] for call in calls)


def test_discovers_observed_per_user_docker_cli_path():
    import subprocess

    expected = "C:/Users/ASUS/AppData/Local/Programs/DockerDesktop/resources/bin/docker.exe"
    calls = []

    def runner(args, **kwargs):
        calls.append(args)
        if args[1:] == ["--version"]:
            return subprocess.CompletedProcess(args, 0, stdout=b"Docker version 29.8.2, build abc123\n")
        if "info" in args:
            return subprocess.CompletedProcess(args, 1, stdout=b"")
        return subprocess.CompletedProcess(args, 1, stdout=b"")

    probe = collect_host_probe(
        platform_name="Windows",
        command_runner=runner,
        which=lambda name: None,
        file_exists=lambda value: value.replace("\\", "/") == expected,
        environ={"LOCALAPPDATA": "C:/Users/ASUS/AppData/Local"},
    )
    assert calls[0][0].replace("\\", "/") == expected
    assert probe["docker_cli"]["path_present"] is True


def test_overflow_quota_is_structured_failure_in_assessment_and_cli(monkeypatch, capsys):
    with pytest.raises(ValueError):
        assess_host(ready_probe(), {"benchmark_concurrency": 10**1000})
    with pytest.raises(ValueError):
        assess_host(ready_probe(), {"laya_memory_gib": 1e308})

    monkeypatch.setattr("apps.worker.preflight.collect_host_probe", lambda **kwargs: ready_probe())
    code = main(["--benchmark-concurrency", str(10**1000)])
    output = json.loads(capsys.readouterr().out)
    assert code != 0
    assert output["status"] == "blocked"
    assert output["checks"][0]["name"] == "configuration"
    code = main(["--laya-memory-gib", "1e308"])
    output = json.loads(capsys.readouterr().out)
    assert code != 0
    assert output["status"] == "blocked"
    assert output["checks"][0]["name"] == "configuration"


def test_invalid_explicit_cli_path_still_collects_windows_wsl():
    import subprocess

    calls = []

    def runner(args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, stdout=b"NAME STATE VERSION\r\n* Ubuntu Running 2\r\n")

    probe = collect_host_probe(
        docker_executable="missing-docker.exe",
        platform_name="Windows",
        command_runner=runner,
        which=lambda name: "wsl.exe" if name == "wsl" else None,
        file_exists=lambda value: False,
    )
    assert probe["docker_cli"]["available"] is False
    assert probe["wsl"]["available"] is True
    assert calls == [["wsl.exe", "--list", "--verbose"]]


def test_cli_version_probe_failure_fails_readability_check():
    import subprocess

    def runner(args, **kwargs):
        if args[1:] == ["--version"]:
            return subprocess.CompletedProcess(args, 1, stdout=b"")
        if "info" in args:
            return subprocess.CompletedProcess(args, 1, stdout=b"")
        return subprocess.CompletedProcess(args, 0, stdout=b"Docker Compose version v2.29\n")

    probe = collect_host_probe(command_runner=runner, platform_name="Linux", which=lambda _: "docker")
    result = assess_host(probe)
    cli_check = next(item for item in result["checks"] if item["name"] == "docker_cli")
    assert probe["docker_cli"]["path_present"] is True
    assert probe["docker_cli"]["available"] is False
    assert cli_check["status"] == "fail"


def test_command_stdout_secrets_are_not_emitted_as_metadata():
    import subprocess

    secret = "TOKEN=super-secret-value"

    def runner(args, **kwargs):
        if args[-2:] == ["--list", "--verbose"]:
            return subprocess.CompletedProcess(args, 0, stdout=f"NAME STATE VERSION\r\n* {secret} Running 2\r\n".encode())
        if args[1:] == ["--version"]:
            return subprocess.CompletedProcess(args, 0, stdout=f"Docker version {secret}\n".encode())
        if "info" in args:
            return subprocess.CompletedProcess(args, 0, stdout=projected_docker_info(secret, 8, 16 * 1024**3, secret, secret))
        return subprocess.CompletedProcess(args, 0, stdout=f"Docker Compose version {secret}\n".encode())

    result = assess_host(collect_host_probe(
        command_runner=runner,
        platform_name="Windows",
        which=lambda name: "wsl.exe" if name == "wsl" else "docker.exe",
    ))
    assert secret not in json.dumps(result)
    assert result["evidence"]["docker_cli"]["version"] is None
    assert result["evidence"]["docker"]["server_version"] is None
    assert result["evidence"]["docker"]["backend"] is None
    assert result["evidence"]["wsl"]["inventory"][0]["name"] == "other"


def test_remote_docker_host_blocks_otherwise_ready_daemon():
    probe = {**ready_probe(), "docker_endpoint": {"local": False, "kind": "remote"}}
    result = assess_host(probe)
    assert result["ready"] is False
    check = next(item for item in result["checks"] if item["name"] == "docker_endpoint")
    assert check["status"] == "fail"
    assert result["evidence"]["docker_endpoint"] == {"local": False, "kind": "remote"}


@pytest.mark.parametrize(
    ("endpoint", "kind"),
    [
        ("npipe:////./pipe/dockerDesktopLinuxEngine", "local_named_pipe"),
        ("npipe:////./pipe/docker_engine", "local_named_pipe"),
        ("unix:///var/run/docker.sock", "local_unix_socket"),
    ],
)
def test_local_docker_endpoints_are_recognized(endpoint, kind):
    import subprocess

    def runner(args, **kwargs):
        if args[-2:] == ["--list", "--verbose"]:
            return subprocess.CompletedProcess(args, 0, stdout=b"NAME STATE VERSION\r\n* docker-desktop Running 2\r\n")
        if args[1:] == ["context", "show"]:
            return subprocess.CompletedProcess(args, 0, stdout=b"desktop-linux\n")
        if args[1:3] == ["context", "inspect"]:
            assert "--format" in args
            return subprocess.CompletedProcess(args, 0, stdout=(endpoint + "\n").encode())
        if args[1:] == ["--version"]:
            return subprocess.CompletedProcess(args, 0, stdout=b"Docker version 29.8.2, build abc123\n")
        if "info" in args:
            return subprocess.CompletedProcess(args, 0, stdout=projected_docker_info())
        return subprocess.CompletedProcess(args, 0, stdout=b"Docker Compose version v2.29\n")

    probe = collect_host_probe(command_runner=runner, platform_name="Windows", which=lambda _: "docker.exe")
    result = assess_host(probe)
    assert probe["docker_endpoint"] == {"local": True, "kind": kind}
    assert result["ready"] is True


@pytest.mark.parametrize(
    ("environment", "context_name", "context_endpoint"),
    [
        ({"DOCKER_HOST": "tcp://user:secret@remote.example:2376"}, "desktop-linux", "npipe:////./pipe/dockerDesktopLinuxEngine"),
        ({"DOCKER_CONTEXT": "prod"}, "prod", "ssh://deploy@remote.example"),
        ({"DOCKER_CONTEXT": "prod", "DOCKER_HOST": "unix:///var/run/docker.sock"}, "prod", "ssh://deploy@remote.example"),
    ],
)
def test_remote_environment_or_selected_context_blocks_and_redacts(
    environment, context_name, context_endpoint,
):
    import subprocess

    calls = []

    def runner(args, **kwargs):
        calls.append(args)
        if args[-2:] == ["--list", "--verbose"]:
            return subprocess.CompletedProcess(args, 0, stdout=b"NAME STATE VERSION\r\n* docker-desktop Running 2\r\n")
        if args[1:] == ["context", "show"]:
            return subprocess.CompletedProcess(args, 0, stdout=b"desktop-linux\n")
        if args[1:3] == ["context", "inspect"]:
            return subprocess.CompletedProcess(args, 0, stdout=(context_endpoint + "\n").encode())
        if args[1:] == ["--version"]:
            return subprocess.CompletedProcess(args, 0, stdout=b"Docker version 29.8.2, build abc123\n")
        if "info" in args:
            return subprocess.CompletedProcess(args, 0, stdout=projected_docker_info())
        return subprocess.CompletedProcess(args, 0, stdout=b"Docker Compose version v2.29\n")

    probe = collect_host_probe(
        command_runner=runner,
        platform_name="Windows",
        which=lambda _: "docker.exe",
        environ=environment,
    )
    result = assess_host(probe)
    assert probe["docker_endpoint"]["local"] is False
    assert result["ready"] is False
    assert "remote.example" not in json.dumps(result)
    assert "secret" not in json.dumps(result)
    inspect_call = next(call for call in calls if call[1:3] == ["context", "inspect"])
    assert inspect_call[-1] == context_name


def test_docker_info_probe_requests_and_parses_only_required_projection():
    import subprocess

    calls = []
    projection = projected_docker_info("linux", 12, 8_014_450_688, "29.8.2", "overlayfs")

    def runner(args, **kwargs):
        calls.append(args)
        if args[1:] == ["context", "show"]:
            return subprocess.CompletedProcess(args, 0, stdout=b"desktop-linux\n")
        if args[1:3] == ["context", "inspect"]:
            return subprocess.CompletedProcess(args, 0, stdout=b"npipe:////./pipe/dockerDesktopLinuxEngine\n")
        if args[1:] == ["--version"]:
            return subprocess.CompletedProcess(args, 0, stdout=b"Docker version 29.8.2, build abc123\n")
        if "info" in args:
            return subprocess.CompletedProcess(args, 0, stdout=projection)
        if args[-2:] == ["--list", "--verbose"]:
            return subprocess.CompletedProcess(args, 0, stdout=b"NAME STATE VERSION\r\n* docker-desktop Running 2\r\n")
        return subprocess.CompletedProcess(args, 0, stdout=b"Docker Compose version v2.29\n")

    probe = collect_host_probe(command_runner=runner, platform_name="Windows", which=lambda _: "docker.exe")
    info_call = next(call for call in calls if "info" in call)
    assert info_call == ["docker.exe", "info", "--format", "{{json .OSType}}\t{{json .NCPU}}\t{{json .MemTotal}}\t{{json .ServerVersion}}\t{{json .Driver}}"]
    assert probe["docker_info"] == {
        "OSType": "linux", "NCPU": 12, "MemTotal": 8_014_450_688,
        "ServerVersion": "29.8.2", "Driver": "overlayfs",
    }
    result = assess_host(probe)
    assert result["ready"] is False
    assert next(item for item in result["checks"] if item["name"] == "docker_engine")["provenance"] == (
        "docker info projected JSON fields: OSType,NCPU,MemTotal,ServerVersion,Driver"
    )
    assert result["evidence"]["docker"]["memory_gib"] < 8
