# Configured coding model source

`CODING_ENDPOINT` is the operator's OpenAI-compatible API base URL, such as
`http://127.0.0.1:20128/v1`. Set `CODING_MODEL` to one model ID returned by
that source's `GET /models`. `CODING_API_KEY` is optional for a local proxy and
stays in ignored local configuration. The read-only catalogue probe reads these
three values from `.env`, with process environment values taking precedence:

```powershell
.venv/Scripts/python.exe -m prototypes.harnesses.model_catalog --container
```

It writes `.local/coding-source.json`. `--container` includes a derived Docker
Desktop endpoint: `127.0.0.1`, `localhost`, and `[::1]` become
`host.docker.internal`, while the port and API base path are preserved.
`CODING_CONTAINER_ENDPOINT` may override that derived address for a future
trusted gateway configuration, but this probe neither uses nor validates the
override. The probe makes one bounded catalogue request and no inference call.
It does not start a container. HTTP sources are limited to loopback and
`host.docker.internal`; remote sources require HTTPS. Credential-bearing URLs,
queries, fragments, and redirects are refused.

The catalogue confirms only that the configured alias appears in the source's
current model list. It does not establish an immutable model revision, open
weight provenance, license, cost, free-tier eligibility, or inference behavior.
Those fields remain unknown/null in the report. An alias ending `:free` and a
local proxy do not establish free use. Later benchmark adapters must select a
configured, present model ID and record the alias plus independently verified
immutable identity when the source provides one. The comparison must use the
same recorded model and conditions for both harnesses.

When execution is implemented, the trusted worker/gateway will hold the source
credential, enforce the approved request and token allowance, and issue a
temporary gateway credential and model specification to each task container.
The task container must not receive `CODING_API_KEY` or direct host secrets.
This gateway and its allowance checks are planned, not implemented by the
catalogue probe.
