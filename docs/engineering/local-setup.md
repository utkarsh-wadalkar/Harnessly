# Local PostgreSQL and LAYA setup

These commands start only the `postgres` and `laya` Compose services. They do not start benchmark task containers or make hosted model calls. The LAYA image builds from the pinned official source and loads the pinned `typed-decisions` checkpoint on CPU; the first build and model download can take time. Named volumes preserve PostgreSQL data and the Hugging Face model cache between ordinary restarts.

## Prerequisites

- Docker Desktop with its Linux engine running and a local Docker context. The scripts reject a remote endpoint, even when Docker itself responds.
- At least 3 CPUs and 6 GiB reported by the Docker engine: 2 CPUs/4 GiB for LAYA, 1 CPU/1 GiB for PostgreSQL, and 1 GiB reserve. The full benchmark preflight has a separate 8 GiB requirement; meeting this infrastructure threshold does not clear that gate.
- A repository `.venv` with the locked dependencies, including `psycopg-binary` and PyYAML. On Windows, create it with Python 3.13 if absent, then install `requirements.lock` using the repository's dependency instructions.

The ignored `.env` is user owned. On first run, the scripts append only missing `POSTGRES_PASSWORD`, `DATABASE_URL`, `LAYA_API_KEY`, and `LAYA_BASE_URL` settings. Existing values and the named volumes are preserved. An existing blank or placeholder value blocks startup and the report names only the affected key. Keep `.env` private; do not paste it or print it in logs. `DATABASE_URL` must point to `harnessarena` on `127.0.0.1:5432` and use the configured PostgreSQL password; `LAYA_BASE_URL` must be `http://127.0.0.1:8001`.

## Start and verify

From the repository root in PowerShell:

```powershell
.\scripts\start-local.ps1
.\scripts\verify-local.ps1
```

If Docker is outside `PATH`, pass `-DockerExecutable 'C:\Program Files\Docker\Docker\resources\bin\docker.exe'` to either script. Startup waits up to 900 seconds for Compose health checks; use `-WaitTimeout 1800` on the start script if a slow first build needs more time. The scripts exit nonzero on any failed check and write a bounded, secret-free `.local/infrastructure-status.json` with safe error codes.

Verification checks the active local Linux Docker engine and its resources, the running containers' CPU/memory caps, health and loopback port bindings, an authenticated PostgreSQL `SELECT` over the host TCP port, and a synthetic typed choice through the LAYA HTTP client. The script also checks the pinned standalone model mapping (`typed-decisions` → `convaiinnovations/laya-typed-decisions`) before startup. Compose receives the validated `.env` credentials explicitly, so stale shell credentials cannot override them. `typedHTTPverified` is reported only after a real response validates the CPU device, checkpoint revision, finite labels and choice schema. A mocked test result is never a live verification result.

If startup fails, inspect the report's `error.code` and `host.checks` first. Docker build, service and model-loading details remain in Docker's own logs (`docker compose --profile control --profile decision logs --tail 80 postgres laya`); review them locally without sharing credentials. The first LAYA model download needs network access unless its named cache is already populated. GPU availability is neither required nor used.

To stop these services manually while retaining both named volumes, run `docker compose --profile control --profile decision stop postgres laya`. Do not add a volume-removal flag when preserving the database and model cache.
