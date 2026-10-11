"""Read-only coding model source boundary."""

import json
import urllib.request

import pytest

from packages.harness_adapters.model_source import (
    ModelSource,
    ModelSourceUnavailable,
    container_endpoint,
)
from prototypes.harnesses.model_catalog import run_probe


def test_catalogue_selects_existing_alias_and_keeps_provenance_unknown():
    calls = []

    def transport(url, headers, timeout, max_bytes):
        calls.append((url, headers, timeout, max_bytes))
        return 200, b'{"data":[{"id":"oss-1-anti"},{"id":"other:free"}]}'

    source = ModelSource("http://127.0.0.1:20128/v1", "secret", transport)
    models = source.list_models()
    selected = source.select(models, "oss-1-anti")
    assert models == ("oss-1-anti", "other:free")
    assert selected == {"id": "oss-1-anti", "revision": None, "license": None,
                        "cost_usd": None, "provenance": "unknown"}
    assert calls == [("http://127.0.0.1:20128/v1/models",
                      {"Authorization": "Bearer secret", "Accept": "application/json"},
                      15, 1024 * 1024)]


def test_no_authorization_header_for_empty_key():
    def transport(url, headers, timeout, max_bytes):
        assert headers == {"Accept": "application/json"}
        return 200, b'{"data":[]}'

    assert ModelSource("https://api.example.test/v1", "", transport).list_models() == ()


@pytest.mark.parametrize("base", [
    "http://example.com/v1", "https://user:pass@example.com/v1",
    "https://example.com/v1?token=x", "https://example.com/v1#secret",
    "file:///etc/passwd", "http://192.168.1.2/v1", "http://[::2]/v1",
])
def test_refused_source_urls(base):
    with pytest.raises(ModelSourceUnavailable, match="refused_url"):
        ModelSource(base, "")


@pytest.mark.parametrize("base,expected", [
    ("http://127.0.0.1:20128/v1", "http://host.docker.internal:20128/v1"),
    ("http://localhost:20128/v1", "http://host.docker.internal:20128/v1"),
    ("http://[::1]:20128/v1", "http://host.docker.internal:20128/v1"),
    ("https://example.com/v1", "https://example.com/v1"),
])
def test_container_endpoint_mapping(base, expected):
    assert container_endpoint(base) == expected


@pytest.mark.parametrize("status,body,code", [
    (503, b"private secret body", "source_error"),
    (200, b"not json", "malformed_response"),
    (200, b'{"data":{}}', "malformed_response"),
    (200, b'{"data":[{"id":"bad id"}]}', "invalid_model_id"),
    (200, b'{"data":[{"id":"ok","irrelevant":NaN}]}', "malformed_response"),
    (200, b"x" * (1024 * 1024 + 1), "response_too_large"),
], ids=["provider-error", "json", "schema", "model-id", "nonfinite", "large-body"])
def test_catalogue_rejects_bad_response_without_exposing_body(status, body, code):
    source = ModelSource("https://api.example.test/v1", "secret",
                         lambda *_: (status, body))
    with pytest.raises(ModelSourceUnavailable) as error:
        source.list_models()
    assert error.value.code == code
    assert "secret" not in str(error.value)
    assert "private" not in str(error.value)


def test_catalogue_has_finite_count_and_requires_selection():
    source = ModelSource("https://api.example.test/v1", "",
                         lambda *_: (200, json.dumps({"data": [{"id": "m"}] * 1001}).encode()))
    with pytest.raises(ModelSourceUnavailable, match="too_many_models"):
        source.list_models()
    with pytest.raises(ModelSourceUnavailable, match="model_unavailable"):
        source.select(("a",), "missing")


def test_transport_timeout_uses_safe_error_code():
    def timeout(*_):
        raise TimeoutError("secret backend detail")

    source = ModelSource("https://api.example.test/v1", "secret", timeout)
    with pytest.raises(ModelSourceUnavailable, match="transport_unavailable") as error:
        source.list_models()
    assert "secret" not in str(error.value)


def test_transport_disables_environment_proxy_and_redirects(monkeypatch):
    handlers_seen = []

    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def geturl(self):
            return "http://127.0.0.1:20128/v1/models"

        def read(self, limit):
            assert limit == 1024 * 1024 + 1
            return b'{"data":[]}'

    class Opener:
        def open(self, request, timeout):
            assert timeout == 15
            return Response()

    def build_opener(*handlers):
        handlers_seen.extend(handlers)
        return Opener()

    monkeypatch.setattr(urllib.request, "build_opener", build_opener)
    assert ModelSource("http://127.0.0.1:20128/v1", "").list_models() == ()
    assert any(isinstance(handler, urllib.request.ProxyHandler) and
               handler.proxies == {} for handler in handlers_seen)
    assert any(isinstance(handler, type) and
               issubclass(handler, urllib.request.HTTPRedirectHandler) and
               handler().redirect_request(None, None, None, None, None, None) is None
               for handler in handlers_seen)


def test_provider_cannot_echo_credential_into_catalogue():
    source = ModelSource("https://api.example.test/v1", "private123",
                         lambda *_: (200, b'{"data":[{"id":"alias-private123"}]}'))
    with pytest.raises(ModelSourceUnavailable, match="credential_echo") as error:
        source.list_models()
    assert "private123" not in str(error.value)


def test_probe_writes_safe_report_for_configured_alias(tmp_path):
    def transport(*_):
        return 200, b'{"data":[{"id":"oss-1-anti"}]}'

    status = run_probe(cwd=tmp_path, environ={"CODING_ENDPOINT": "http://127.0.0.1:20128/v1",
                                              "CODING_API_KEY": "do-not-print",
                                              "CODING_MODEL": "oss-1-anti"},
                       transport=transport, container=True)
    report = json.loads((tmp_path / ".local/coding-source.json").read_text())
    assert status == 0
    assert report["selected_model"]["id"] == "oss-1-anti"
    assert report["container_endpoint"] == "http://host.docker.internal:20128/v1"
    assert report["connection"] == "catalogue_available"
    assert "do-not-print" not in json.dumps(report)
