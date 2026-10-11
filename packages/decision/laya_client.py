"""Small, secret-safe HTTP adapter for the pinned local LAYA service."""

from __future__ import annotations

import ipaddress
import json
import math
import socket
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from typing import Literal
from urllib.parse import urlsplit, urlunsplit

from pydantic import BaseModel, ConfigDict


Outcome = Literal["candidate_a", "candidate_b", "equivalent", "insufficient_evidence"]
ALLOWED_OUTCOMES = ("candidate_a", "candidate_b", "equivalent", "insufficient_evidence")
MAX_RESPONSE_BYTES = 1024 * 1024
MAX_TIMEOUT_SECONDS = 15.0
PINNED_TYPED_REVISION = "1a793eb568e6718f15941d08f85432581df534e3"
UPSTREAM_RUNTIME_MODEL = "laya-rl-agent"


class LayaUnavailable(RuntimeError):
    """A safe, stable failure that never carries a server body or credential."""

    def __init__(self, code: str, status_code: int | None = None):
        self.code = code
        self.status_code = status_code
        super().__init__(code)


class LayaHealth(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["ok"]
    loaded: tuple[str, ...]
    revision: str
    device: str
    device_is_preference: bool
    checkpoint_device: str


class LayaDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    model: str
    checkpoint: Literal["typed-decisions"]
    revision: str
    outcome: Outcome
    probabilities: dict[Outcome, float]
    raw_confidence: float | None = None
    health: LayaHealth


Transport = Callable[[str, str, dict[str, str], bytes | None, float, int], tuple[int, bytes]]


def _normalise_base_url(value: str) -> str:
    try:
        parts = urlsplit(value)
        host = parts.hostname
        port = parts.port
    except (TypeError, ValueError):
        raise LayaUnavailable("refused_url") from None
    if (
        parts.scheme != "http"
        or not host
        or parts.username is not None
        or parts.password is not None
        or parts.query
        or parts.fragment
        or "?" in value
        or "#" in value
        or parts.path not in ("", "/")
    ):
        raise LayaUnavailable("refused_url")
    try:
        loopback = ipaddress.ip_address(host).is_loopback
    except ValueError:
        loopback = host.lower() == "localhost"
    compose_laya = host.lower() == "laya" and port == 8000
    if not (loopback or compose_laya):
        raise LayaUnavailable("refused_url")
    netloc = parts.netloc
    # Keep the validated local authority only; URL parsing has already rejected userinfo.
    return urlunsplit((parts.scheme, netloc, "", "", "")).rstrip("/")


def _urllib_transport(
    method: str,
    url: str,
    headers: dict[str, str],
    body: bytes | None,
    timeout: float,
    max_bytes: int,
) -> tuple[int, bytes]:
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    class _NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, request, response, code, message, headers, new_url):
            return None

    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect())
    try:
        with opener.open(request, timeout=timeout) as response:
            return response.status, response.read(max_bytes + 1)
    except urllib.error.HTTPError as error:
        # Status is useful; response text may contain state, paths, or server details.
        return error.code, b""


def _safe_json(status: int, body: bytes) -> object:
    if status < 200 or status >= 300:
        code = "service_unavailable" if status == 503 else "http_error"
        if status in (401, 403):
            code = "authentication_failed"
        raise LayaUnavailable(code, status)
    if len(body) > MAX_RESPONSE_BYTES:
        raise LayaUnavailable("response_too_large", status)
    try:
        return json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError):
        raise LayaUnavailable("malformed_response", status) from None


class LayaDecisionClient:
    """Authenticated client for local `/health` and `/v1/systemone` endpoints."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "http://127.0.0.1:8001",
        *,
        timeout: float = MAX_TIMEOUT_SECONDS,
        transport: Transport | None = None,
    ) -> None:
        if not isinstance(api_key, str) or not api_key.strip():
            raise LayaUnavailable("missing_credentials")
        if not math.isfinite(timeout) or timeout <= 0 or timeout > MAX_TIMEOUT_SECONDS:
            raise ValueError("timeout must be greater than zero and at most 15 seconds")
        self._api_key = api_key
        self._base_url = _normalise_base_url(base_url)
        self._timeout = timeout
        self._transport = _urllib_transport if transport is None else transport

    def _request(self, method: str, path: str, payload: Mapping[str, object] | None = None) -> object:
        try:
            body = None if payload is None else json.dumps(payload, separators=(",", ":")).encode("utf-8")
        except (TypeError, ValueError):
            raise LayaUnavailable("invalid_request") from None
        headers = {"Authorization": f"Bearer {self._api_key}", "Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        try:
            status, response_body = self._transport(
                method,
                f"{self._base_url}{path}",
                headers,
                body,
                self._timeout,
                MAX_RESPONSE_BYTES,
            )
        except (TimeoutError, socket.timeout) as error:
            raise LayaUnavailable("timeout") from None
        except urllib.error.URLError as error:
            if isinstance(error.reason, (TimeoutError, socket.timeout)):
                raise LayaUnavailable("timeout") from None
            raise LayaUnavailable("unreachable") from None
        except OSError:
            raise LayaUnavailable("unreachable") from None
        return _safe_json(status, response_body)

    def health(self) -> LayaHealth:
        raw = self._request("GET", "/health")
        if not isinstance(raw, dict):
            raise LayaUnavailable("malformed_health")
        loaded = raw.get("loaded")
        revisions = raw.get("revisions")
        checkpoint_devices = raw.get("checkpoint_devices")
        revision = revisions.get("typed-decisions") if isinstance(revisions, dict) else None
        device = checkpoint_devices.get("typed-decisions") if isinstance(checkpoint_devices, dict) else None
        # These names and fields follow laya/serve.py's authenticated /health response.
        if (
            raw.get("status") != "ok"
            or loaded != ["typed-decisions"]
            or raw.get("device") != "cpu"
            or raw.get("device_is_preference") is not False
            or device != "cpu"
        ):
            raise LayaUnavailable("unhealthy")
        if revision != PINNED_TYPED_REVISION:
            raise LayaUnavailable("checkpoint_mismatch")
        try:
            return LayaHealth(
                status="ok",
                loaded=("typed-decisions",),
                revision=revision,
                device="cpu",
                device_is_preference=False,
                checkpoint_device="cpu",
            )
        except (TypeError, ValueError):
            raise LayaUnavailable("malformed_health") from None

    def predict(self, state: object, questions: Mapping[str, object]) -> LayaDecision:
        if not isinstance(questions, Mapping) or len(questions) != 1:
            raise ValueError("exactly one typed choice question is required")
        question_id, question = next(iter(questions.items()))
        if not isinstance(question_id, str) or not isinstance(question, Mapping):
            raise ValueError("question must have a string id and object definition")
        criteria = question.get("criteria")
        if (
            question.get("type") != "choice"
            or not isinstance(criteria, (list, tuple))
            or not all(isinstance(label, str) for label in criteria)
            or set(criteria) != set(ALLOWED_OUTCOMES)
            or len(criteria) != len(ALLOWED_OUTCOMES)
        ):
            raise ValueError("choice criteria must declare the four supported outcomes")
        health = self.health()
        raw = self._request(
            "POST",
            "/v1/systemone",
            {"state": state, "questions": dict(questions), "model": "typed-decisions"},
        )
        if not isinstance(raw, dict):
            raise LayaUnavailable("malformed_response")
        routing = raw.get("routing")
        if not isinstance(routing, dict) or routing.get("model") != "typed-decisions":
            raise LayaUnavailable("model_mismatch")
        answers = raw.get("answers")
        answer = answers.get(question_id) if isinstance(answers, dict) else None
        if not isinstance(answer, dict) or answer.get("type") != "choice":
            raise LayaUnavailable("malformed_decision")
        outcome = answer.get("choice")
        probabilities = answer.get("probabilities")
        if outcome not in ALLOWED_OUTCOMES or outcome not in criteria:
            raise LayaUnavailable("invalid_label")
        if not isinstance(probabilities, dict) or set(probabilities) != set(criteria):
            raise LayaUnavailable("malformed_probabilities")
        try:
            if any(
                isinstance(probabilities[label], bool)
                or not isinstance(probabilities[label], (int, float))
                for label in ALLOWED_OUTCOMES
            ):
                raise TypeError
            checked = {label: float(probabilities[label]) for label in ALLOWED_OUTCOMES}
        except (TypeError, ValueError, KeyError, OverflowError):
            raise LayaUnavailable("malformed_probabilities") from None
        if (
            any(not math.isfinite(value) or value < 0 or value > 1 for value in checked.values())
            or abs(sum(checked.values()) - 1.0) > 1e-3
        ):
            raise LayaUnavailable("malformed_probabilities")
        confidence = answer.get("confidence")
        if confidence is not None:
            if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
                raise LayaUnavailable("malformed_decision")
            try:
                confidence = float(confidence)
            except (TypeError, ValueError, OverflowError):
                raise LayaUnavailable("malformed_decision") from None
            if not math.isfinite(confidence) or not 0 <= confidence <= 1:
                raise LayaUnavailable("malformed_decision")
        reported_model = raw.get("model")
        if reported_model != UPSTREAM_RUNTIME_MODEL:
            raise LayaUnavailable("model_mismatch")
        try:
            return LayaDecision(
                model=reported_model,
                checkpoint="typed-decisions",
                revision=health.revision,
                outcome=outcome,
                probabilities=checked,
                raw_confidence=confidence,
                health=health,
            )
        except (TypeError, ValueError):
            raise LayaUnavailable("malformed_decision") from None
