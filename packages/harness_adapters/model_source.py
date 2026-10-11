"""Bounded, read-only OpenAI-compatible model catalogue source."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from urllib.parse import urlsplit, urlunsplit

TIMEOUT = 15
MAX_BYTES = 1024 * 1024
MAX_MODELS = 1000
MODEL_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/+\-]{0,127}\Z")
LOOPBACK = {"localhost", "127.0.0.1", "::1"}


class ModelSourceUnavailable(Exception):
    """A safe, stable error code with no provider response or credentials."""

    def __init__(self, code: str, status_code: int | None = None):
        self.code = code
        self.status_code = status_code
        super().__init__(code)


def _validated_parts(endpoint: str):
    if not isinstance(endpoint, str) or not endpoint or any(ord(c) <= 32 for c in endpoint):
        raise ModelSourceUnavailable("refused_url")
    try:
        parts = urlsplit(endpoint)
        host = parts.hostname
        port = parts.port
    except ValueError:
        raise ModelSourceUnavailable("refused_url") from None
    if (parts.scheme not in {"http", "https"} or not host or
            parts.username is not None or parts.password is not None or
            parts.query or parts.fragment or endpoint.endswith(("?", "#")) or
            (parts.scheme == "http" and host.lower() not in LOOPBACK | {"host.docker.internal"})):
        raise ModelSourceUnavailable("refused_url")
    # Accessing parts.port validates its range; the value is otherwise preserved.
    del port
    return parts


def container_endpoint(endpoint: str) -> str:
    """Translate Docker Desktop loopback to its host gateway, preserving path/port."""
    parts = _validated_parts(endpoint)
    if parts.hostname.lower() not in LOOPBACK:
        return endpoint
    port = f":{parts.port}" if parts.port is not None else ""
    return urlunsplit((parts.scheme, f"host.docker.internal{port}", parts.path, "", ""))


def _transport(url: str, headers: dict[str, str], timeout: int, max_bytes: int):
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, response_headers, new_url):
            return None

    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect)
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with opener.open(request, timeout=timeout) as response:
            if response.geturl() != url:
                raise ModelSourceUnavailable("redirect_refused")
            return response.status, response.read(max_bytes + 1)
    except urllib.error.HTTPError as exc:
        raise ModelSourceUnavailable("source_error", exc.code) from None
    except (TimeoutError, urllib.error.URLError, OSError):
        raise ModelSourceUnavailable("transport_unavailable") from None


class ModelSource:
    def __init__(self, endpoint: str, api_key: str, transport=None):
        parts = _validated_parts(endpoint)
        if not isinstance(api_key, str) or "\r" in api_key or "\n" in api_key:
            raise ModelSourceUnavailable("invalid_credentials")
        self.endpoint = endpoint
        self.api_key = api_key
        self.transport = transport or _transport
        self.models_url = urlunsplit((parts.scheme, parts.netloc,
                                     parts.path.rstrip("/") + "/models", "", ""))

    def list_models(self) -> tuple[str, ...]:
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        try:
            status, body = self.transport(self.models_url, headers, TIMEOUT, MAX_BYTES)
        except ModelSourceUnavailable:
            raise
        except Exception:
            raise ModelSourceUnavailable("transport_unavailable") from None
        if type(status) is not int or not 200 <= status < 300:
            raise ModelSourceUnavailable("source_error", status if type(status) is int else None)
        if not isinstance(body, bytes):
            raise ModelSourceUnavailable("malformed_response")
        if len(body) > MAX_BYTES:
            raise ModelSourceUnavailable("response_too_large")
        try:
            document = json.loads(body, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
        except (TypeError, ValueError, UnicodeDecodeError):
            raise ModelSourceUnavailable("malformed_response") from None
        if not isinstance(document, dict) or not isinstance(document.get("data"), list):
            raise ModelSourceUnavailable("malformed_response")
        entries = document["data"]
        if len(entries) > MAX_MODELS:
            raise ModelSourceUnavailable("too_many_models")
        ids = []
        for entry in entries:
            model_id = entry.get("id") if isinstance(entry, dict) else None
            if not isinstance(model_id, str) or not MODEL_ID.fullmatch(model_id):
                raise ModelSourceUnavailable("invalid_model_id")
            if self.api_key and self.api_key in model_id:
                raise ModelSourceUnavailable("credential_echo")
            ids.append(model_id)
        if len(set(ids)) != len(ids):
            raise ModelSourceUnavailable("duplicate_model_id")
        return tuple(ids)

    @staticmethod
    def select(models: tuple[str, ...], selected_id: str) -> dict:
        if selected_id not in models:
            raise ModelSourceUnavailable("model_unavailable")
        return {"id": selected_id, "revision": None, "license": None,
                "cost_usd": None, "provenance": "unknown"}
