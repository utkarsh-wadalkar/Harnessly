# Spec 01: Feasibility and preflight

## Contract

Preflight records OS, WSL2/Docker Desktop availability, Docker CLI/version, engine access, CPU/memory capability, PostgreSQL reachability and provider configuration without printing credentials. Each check is pass/fail/unknown with timestamp, command or request provenance and bounded output. Failure cannot be reported as a successful probe.

Official LAYA runs only on loopback port 8001 with a CPU-compatible typed-decision model, cache and 2 CPU/4 GiB caps. The probe must record server/model versions, selected device, startup, valid finite-choice response and observed resource use. GPU fallback is prohibited.

Gemma probe targets Google AI Studio `gemma-4-26b-a4b-it`: confirm endpoint support, credentials, terms, eligibility, caps and structured extraction on a non-personal fixture. Hosted coding probes use the same Qwen model endpoint. Free-tier entitlement and zero cost are never assumed.

## Acceptance scenarios

- Given missing Docker CLI or denied WSL access, when preflight runs, then execution readiness is blocked with the failed check retained.
- Given no credentials, when a provider probe is requested, then no paid/unverified call occurs and missing configuration is reported.
- Given LAYA cannot load within caps, when selection is requested, then the result identifies deterministic fallback and its cause.
- Given verified provider eligibility and limits, when a fixture probe runs, then model identifier, usage source, request outcome and effective caps are recorded without secrets.

## Required validation

Unit checks for readiness aggregation and secret-safe output; mocked unavailable/denied providers; live Docker and LAYA resource evidence; a real authorized Gemma fixture response. Unavailable live prerequisites leave their tickets open.

## Current provenance notes

Source discovery recorded LAYA main commit `68804629e8ccd9d616d48a40e87de9fabbeae069` and typed checkpoint revision `1a793eb568e6718f15941d08f85432581df534e3`; these pins are not runtime success evidence. Elevated inspection found Docker CLI 29.8.2, Compose 5.5.1 and Ubuntu/docker-desktop WSL2 distributions. The engine and distributions were stopped; Docker startup was declined. Compose configuration parsing passes without starting services. Execution-limit enforcement, PostgreSQL and live provider readiness remain unverified. Host Python is 3.13 for current checks; production/CI target is 3.11 and requires its own validation.

