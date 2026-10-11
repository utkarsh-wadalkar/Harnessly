# HarnessArena

An open-source, personalized AI coding harness benchmarking and recommendation platform.

**Gemma 4 developer interview + real Docker benchmark evidence → local LAYA typed decisions → recommended harness/model combination.**

Current milestone: architecture/contracts and feasibility tooling. The application, live benchmark integrations and verified leaderboard are **not yet implemented**. [Ticket status](docs/roadmap.md) and [implementation evidence](docs/engineering/progress.md) are authoritative; generated API routes are proposed interfaces.

## Local prerequisites

- Windows 11, Docker Desktop with the WSL2/Linux backend; use dedicated curated fixtures only.
- Python 3.11 recommended (current host checks use 3.13), with an isolated virtual environment.
- Hosted Google AI Studio Gemma credentials and a verified inference allowance for live probes; no GPU required.
- LAYA uses two CPUs/4 GiB; defaults reserve resources for PostgreSQL/control modules and one benchmark container. Preflight rejects insufficient resources.

## Validate the current milestone

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
.\.venv\Scripts\python.exe -m pip install --no-deps --no-build-isolation -e .
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m scripts.export_contracts --check
.\.venv\Scripts\python.exe -m scripts.validate_project
.\.venv\Scripts\python.exe -m apps.worker.preflight
```

The frontend contract tooling uses pnpm 11.25.0 with a frozen lockfile: `pnpm install --frozen-lockfile`, then `pnpm contracts:check`. After an intentional schema change, export Python contracts first and run `pnpm contracts:generate`. [Generated TypeScript types](packages/contracts/generated/api.d.ts) do not imply a frontend application exists.

Preflight returns nonzero for unavailable prerequisites; that is a blocked execution state, not a benchmark failure. Provider access and isolation smoke tests remain separate live gates.

## Local LAYA deployment

Copy `.env.example` to ignored `.env`, configure independent random `LAYA_API_KEY` and `POSTGRES_PASSWORD` values, then run preflight before starting services. Never place provider keys in source control.

```powershell
docker compose --profile decision up --build -d --wait laya
docker compose --profile control up -d --wait postgres
.\.venv\Scripts\python.exe -m prototypes.laya.probe --output .local/laya-probe.json
```

The Compose source/checkpoint are pinned; live build, CPU execution, cache persistence, resource behavior and model hashes must still be verified before ticket 03 is complete. Only LAYA's host port `127.0.0.1:8001` is published. A future containerized FastAPI adapter uses `http://laya:8000` on its private network. No public LAYA endpoint or benchmark-container access is configured.

`compose.yaml` currently defines infrastructure only. Starting it does not create a web/API application. First startup downloads model weights into a persistent named cache; offline restarts can set `HF_HUB_OFFLINE=1` after successful provisioning. No NVIDIA dependencies or all-checkpoint preload is configured.

## Engineering map

- [Architecture and diagrams](docs/architecture.md), [domain and invariants](docs/domain.md), [glossary](GLOSSARY.md), [ADRs](docs/adr/001-local-execution.md).
- [Research and validation status](docs/research/integrations.md), [risk register](docs/risks.md), [API semantics](docs/engineering/api-contracts.md).
- [Proposed OpenAPI](packages/contracts/generated/openapi.json), [JSON Schema](packages/contracts/generated/schema.json), [specifications and traceability](docs/specs/08-release-traceability.md).
- [Roadmap](docs/roadmap.md), [first ticket](.scratch/harnessarena/issues/01-planning.md), [contribution guide](CONTRIBUTING.md).

The first demonstrator targets one fixture, two harnesses using the same coding model, and three independent trials per pairing. The full MVP adds ten curated tasks, reproducible repeated reports, profile workflows, central LAYA selection and explicit fallback, plus a separate verified global leaderboard. Synthetic fixtures and upstream performance numbers are never HarnessArena benchmark results.

Original project code targets Apache-2.0. Upstream harness/model/runtime licenses remain independent; see [third-party policy](THIRD_PARTY_NOTICES.md). Primary challenge: [Best Open-Source AI Project](https://www.mlh.com/events/hacktoberfest-hack-day-pune-x-fair/challenges/01a0d987-0c41-12ea-13ac-5b85755dc2f3). Public replay and a local live demo do not require paid cloud hosting.
