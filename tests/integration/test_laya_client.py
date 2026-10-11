import json
import urllib.request

import pytest

from packages.decision.laya_client import LayaDecisionClient, LayaUnavailable, _urllib_transport
from prototypes.laya.probe import run_probe


REVISION = "1a793eb568e6718f15941d08f85432581df534e3"
HEALTH = {
    "status": "ok",
    "loaded": ["typed-decisions"],
    "revisions": {"typed-decisions": REVISION},
    "device": "cpu",
    "device_is_preference": False,
    "checkpoint_devices": {"typed-decisions": "cpu"},
    "cpu_fallbacks": {"typed-decisions": {"count": 0, "last_reason": None}},
}
CHOICE = {
    "type": "choice",
    "choice": "candidate_a",
    "probabilities": {
        "candidate_a": 0.7,
        "candidate_b": 0.1,
        "equivalent": 0.1,
        "insufficient_evidence": 0.1,
    },
    "confidence": 0.2,
}
DECISION = {
    "model": "laya-rl-agent",
    "routing": {"model": "typed-decisions"},
    "answers": {"pair": CHOICE},
    "usage": {"input_tokens": 12, "output_tokens": 2},
}
QUESTIONS = {
    "pair": {
        "type": "choice",
        "instructions": "Select the better synthetic candidate.",
        "criteria": ["candidate_a", "candidate_b", "equivalent", "insufficient_evidence"],
    }
}


def _payload(value):
    return json.dumps(value, allow_nan=True).encode()


def _client(health=HEALTH, decision=DECISION, response_override=None):
    def transport(method, url, headers, body, timeout, max_bytes):
        if response_override is not None:
            return response_override(method, url, headers, body, timeout, max_bytes)
        if url.endswith("/health"):
            return 200, _payload(health)
        return 200, _payload(decision)

    return LayaDecisionClient("test-secret", transport=transport)


def test_predict_sends_explicit_checkpoint_and_bearer_then_validates_choice():
    calls = []

    def transport(method, url, headers, body, timeout, max_bytes):
        calls.append((method, url, headers, body, timeout, max_bytes))
        if url.endswith("/health"):
            return 200, _payload(HEALTH)
        return 200, _payload(DECISION)

    result = LayaDecisionClient("test-secret", transport=transport).predict(
        {"summary": "synthetic preference fixture"}, QUESTIONS
    )

    assert result.outcome == "candidate_a"
    assert result.probabilities["candidate_a"] == 0.7
    assert result.revision == REVISION
    assert calls[0][0:2] == ("GET", "http://127.0.0.1:8001/health")
    assert calls[1][0:2] == ("POST", "http://127.0.0.1:8001/v1/systemone")
    assert calls[0][2]["Authorization"] == "Bearer test-secret"
    assert calls[1][2]["Authorization"] == "Bearer test-secret"
    assert calls[1][4:] == (15.0, 1024 * 1024)
    assert json.loads(calls[1][3]) == {
        "state": {"summary": "synthetic preference fixture"},
        "questions": QUESTIONS,
        "model": "typed-decisions",
    }


def test_predict_rejects_actual_checkpoint_mismatch():
    decision = {**DECISION, "routing": {"model": "english"}}

    with pytest.raises(LayaUnavailable) as error:
        _client(decision=decision).predict({"summary": "synthetic"}, QUESTIONS)

    assert error.value.code == "model_mismatch"


def test_health_requires_the_pinned_typed_checkpoint_revision():
    health = {**HEALTH, "revisions": {"typed-decisions": "0" * 40}}

    with pytest.raises(LayaUnavailable) as error:
        _client(health=health).predict({"summary": "synthetic"}, QUESTIONS)

    assert error.value.code == "checkpoint_mismatch"


@pytest.mark.parametrize(
    "loaded",
    [["typed-decisions", "english"], ["typed-decisions", "typed-decisions"], ["typed-decisions", 7]],
)
def test_health_rejects_any_loaded_checkpoint_besides_typed(loaded):
    with pytest.raises(LayaUnavailable) as error:
        _client(health={**HEALTH, "loaded": loaded}).health()

    assert error.value.code == "unhealthy"


def test_predict_rejects_untrusted_generic_model_identifier():
    decision = {**DECISION, "model": "test-secret"}

    with pytest.raises(LayaUnavailable) as error:
        _client(decision=decision).predict({"summary": "synthetic"}, QUESTIONS)

    assert error.value.code == "model_mismatch"
    assert "test-secret" not in str(error.value)


@pytest.mark.parametrize(
    "health",
    [
        {**HEALTH, "device": "cuda"},
        {**HEALTH, "device_is_preference": True},
        {**HEALTH, "checkpoint_devices": {"typed-decisions": "cuda"}},
        {**HEALTH, "loaded": ["english"]},
    ],
)
def test_health_requires_resident_typed_checkpoint_on_actual_cpu(health):
    with pytest.raises(LayaUnavailable) as error:
        _client(health=health).health()

    assert error.value.code == "unhealthy"


@pytest.mark.parametrize(
    ("answer", "expected_code"),
    [
        ({**CHOICE, "choice": "invented"}, "invalid_label"),
        ({**CHOICE, "probabilities": {**CHOICE["probabilities"], "candidate_a": float("nan")}}, "malformed_probabilities"),
        ({**CHOICE, "probabilities": {**CHOICE["probabilities"], "candidate_a": 10**1000}}, "malformed_probabilities"),
        ({**CHOICE, "probabilities": {"candidate_a": 1.0}}, "malformed_probabilities"),
    ],
)
def test_predict_rejects_invalid_label_or_probability_distribution(answer, expected_code):
    decision = {**DECISION, "answers": {"pair": answer}}

    with pytest.raises(LayaUnavailable) as error:
        _client(decision=decision).predict({"summary": "synthetic"}, QUESTIONS)

    assert error.value.code == expected_code


@pytest.mark.parametrize("confidence", [True, "0.2"])
def test_predict_rejects_boolean_or_string_raw_confidence(confidence):
    decision = {**DECISION, "answers": {"pair": {**CHOICE, "confidence": confidence}}}

    with pytest.raises(LayaUnavailable) as error:
        _client(decision=decision).predict({"summary": "synthetic"}, QUESTIONS)

    assert error.value.code == "malformed_decision"


@pytest.mark.parametrize(
    ("response", "expected_code", "status"),
    [
        (lambda *args: (503, b"server details include test-secret"), "service_unavailable", 503),
        (lambda *args: (_ for _ in ()).throw(TimeoutError("test-secret")), "timeout", None),
        (lambda *args: (200, b"not-json test-secret"), "malformed_response", 200),
        (lambda *args: (200, b"x" * (1024 * 1024 + 1)), "response_too_large", 200),
    ],
)
def test_transport_failures_use_safe_codes_without_server_text(response, expected_code, status):
    with pytest.raises(LayaUnavailable) as error:
        _client(response_override=response).health()

    assert error.value.code == expected_code
    assert error.value.status_code == status
    assert "test-secret" not in str(error.value)


@pytest.mark.parametrize(
    "base_url",
    [
        "https://example.com",
        "http://example.com",
        "http://user:password@127.0.0.1:8001",
        "http://127.0.0.1:8001?token=test-secret",
        "http://127.0.0.1:8001?",
        "http://127.0.0.1:8001#fragment",
        "http://127.0.0.1:8001#",
        "http://laya:8001",
    ],
)
def test_client_refuses_nonlocal_or_ambiguous_base_urls(base_url):
    with pytest.raises(LayaUnavailable) as error:
        LayaDecisionClient("test-secret", base_url)

    assert error.value.code == "refused_url"
    assert "test-secret" not in str(error.value)


def test_urllib_transport_disables_environment_proxies(monkeypatch):
    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self, size):
            return b"{}"

    class Opener:
        def open(self, request, timeout):
            return Response()

    def build_opener(*handlers):
        proxy_handlers = [handler for handler in handlers if isinstance(handler, urllib.request.ProxyHandler)]
        assert len(proxy_handlers) == 1
        assert proxy_handlers[0].proxies == {}
        return Opener()

    monkeypatch.setattr(urllib.request, "build_opener", build_opener)
    assert _urllib_transport("GET", "http://laya:8000/health", {}, None, 15, 100) == (200, b"{}")


def test_probe_writes_safe_report_for_two_synthetic_examples(tmp_path):
    calls = []

    def transport(method, url, headers, body, timeout, max_bytes):
        calls.append((method, url, headers, body))
        if url.endswith("/health"):
            return 200, _payload(HEALTH)
        return 200, _payload(DECISION)

    output = tmp_path / "probe.json"
    code = run_probe(
        output,
        environ={"LAYA_API_KEY": "test-secret", "LAYA_BASE_URL": "http://127.0.0.1:8001"},
        transport=transport,
    )

    report = json.loads(output.read_text(encoding="utf-8"))
    request = json.loads(next(call[3] for call in calls if call[0] == "POST"))
    assert code == 0
    assert report["verification"] == "typedHTTPverified"
    assert report["outcome"] == "candidate_a"
    assert report["cpu_health"]["checkpoint_device"] == "cpu"
    assert report["checkpoint"]["name"] == "typed-decisions"
    assert len(request["state"]["metric_examples"]) == 2
    assert all(example["synthetic"] is True for example in request["state"]["metric_examples"])
    assert "synthetic preference fixture" not in output.read_text(encoding="utf-8")
    assert "test-secret" not in output.read_text(encoding="utf-8")
    assert "rankingvalidated" not in output.read_text(encoding="utf-8")


def test_probe_writes_structured_unavailable_report_without_credentials(tmp_path, monkeypatch):
    output = tmp_path / "probe.json"
    (tmp_path / ".env").write_text("OTHER_SECRET=must-not-be-read\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    code = run_probe(output, environ={})

    report = json.loads(output.read_text(encoding="utf-8"))
    assert code != 0
    assert report["outcome"] == "unavailable"
    assert report["error"]["code"] == "missing_credentials"
    assert report["typed_decision"] is None


def test_probe_reads_only_supported_values_from_simple_dotenv(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text(
        "LAYA_API_KEY=dotenv-secret\nLAYA_BASE_URL=http://127.0.0.1:8001\nOTHER_SECRET=must-not-be-read\n",
        encoding="utf-8",
    )
    output = tmp_path / "probe.json"

    def malformed_response(method, url, headers, body, timeout, max_bytes):
        return (200, _payload(HEALTH)) if url.endswith("/health") else (200, b"not-json")

    assert run_probe(
        output,
        environ={"LAYA_API_KEY": "dotenv-secret"},
        transport=malformed_response,
    ) == 1
    report_text = output.read_text(encoding="utf-8")
    report = json.loads(report_text)
    assert report["error"]["code"] == "malformed_response"
    assert "dotenv-secret" not in report_text
    assert "must-not-be-read" not in report_text
