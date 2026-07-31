# HiveSight

HiveSight is a Varroa-focused inspection support system for hobbyist and small-scale beekeepers. The registered product domain is hive-sight.com.

The first codebase follows [ADR-0001](architecture/adr/0001-service-oriented-architecture.md): a service-oriented monorepo with a TypeScript web app, Python Core API, private Python Analysis Service, asynchronous analysis boundary, and S3-compatible object storage.

## Structure

- `apps/web`: V1 web interface.
- `services/core-api`: protected product-facing API for Workspaces, apiaries, hives, inspections, photos, upload flows, and user-facing analysis status.
- `services/analysis-service`: private analysis runtime boundary for image-analysis jobs, detections, tagged outputs, and model-version traceability.
- `contracts`: shared API/event contract notes and schemas.
- `infra`: local development infrastructure notes.
- `architecture`: architecture decisions and diagrams.
- `requirements`: requirements and product specification artifacts.

## Clean Machine Setup

Install these prerequisites first:

- Python 3.12.
- Node.js 26 or newer.
- pnpm.
- Docker Desktop, for local Postgres metadata persistence.

On macOS with Homebrew, that is typically:

```sh
brew install python@3.12 node pnpm
```

From a fresh clone, install HiveSight dependencies from the repo root:

```sh
cd ~/Projects/hive-sight
python3.12 -m venv services/core-api/.venv
services/core-api/.venv/bin/python -m pip install -e "services/core-api[dev]"
python3.12 -m venv services/analysis-service/.venv
services/analysis-service/.venv/bin/python -m pip install -e "services/analysis-service[dev]"
pnpm install
pnpm --filter @hive-sight/web exec playwright install chromium
```

Start Docker Desktop before using the Postgres-backed persistence path.

## Daily Local Start

Start the local stack from the repo root:

```sh
pnpm dev:all
```

Start the local stack so other devices on the same network can access it:

```sh
pnpm dev:lan
```

Check whether the local servers are already running:

```sh
pnpm dev:status
```

Check the LAN URLs:

```sh
pnpm dev:status:lan
```

Stop the local servers:

```sh
pnpm dev:stop
```

Start local Postgres:

```sh
pnpm db:up
```

Apply migrations:

```sh
pnpm db:migrate
```

Reset and seed the local development database:

```sh
pnpm db:reset
```

Run the Core API against Postgres-backed metadata:

```sh
HIVESIGHT_PERSISTENCE_BACKEND=postgres pnpm dev:all
```

Open the Web UI at:

```text
http://127.0.0.1:5173/
```

When using `pnpm dev:lan`, the terminal prints the LAN Web UI URL, for example:

```text
http://192.168.1.42:5173/
```

Open that URL from another device on the same Wi-Fi network. Your Mac firewall may ask whether to allow incoming connections for Python or Node/Vite; allow them for local testing.

`pnpm dev:all` starts the Core API on `http://127.0.0.1:8000`, the Analysis Service on `http://127.0.0.1:8100`, and the Web UI on `http://127.0.0.1:5173`. Press `Ctrl+C` in that terminal to stop them, or run `pnpm dev:stop` from another terminal.

`pnpm dev:lan` binds the Web UI and Core API to your local network address. This is for trusted home-network testing only. Some browser camera APIs require HTTPS on non-localhost origins, so LAN testing is enough for checking responsive behaviour and photo/file selection, but direct camera integration may need an HTTPS dev setup later.

If you want to run just the Web UI in a separate terminal, use:

```sh
pnpm dev:web
```

## Local Grounding DINO Pre-Labelling

The normal dev stack uses the fast deterministic pre-labeller. To run a real local Grounding DINO model for dataset labelling, first install the optional Core API model dependencies:

```sh
cd ~/Projects/hive-sight
services/core-api/.venv/bin/python -m pip install -e "services/core-api[dev,grounding-dino]"
```

Then start the stack with Grounding DINO enabled:

```sh
pnpm dev:all:grounding-dino
```

For a more permissive "show me whether it sees bees" mode, use:

```sh
pnpm dev:bees
```

For LAN testing:

```sh
pnpm dev:lan:grounding-dino
```

For LAN testing with the more permissive bee thresholds:

```sh
pnpm dev:bees:lan
```

By default this uses the Hugging Face Transformers Grounding DINO model `IDEA-Research/grounding-dino-tiny` with prompt `honey bee . partial honey bee`. The first run may download model files into your local Hugging Face cache. After that, it runs from the local cache.

Useful overrides:

```sh
HIVESIGHT_GROUNDING_DINO_MODEL_ID=IDEA-Research/grounding-dino-base
HIVESIGHT_GROUNDING_DINO_PROMPT="honey bee . partial honey bee"
HIVESIGHT_GROUNDING_DINO_BOX_THRESHOLD=0.35
HIVESIGHT_GROUNDING_DINO_TEXT_THRESHOLD=0.25
HIVESIGHT_GROUNDING_DINO_DEVICE=auto
HIVESIGHT_GROUNDING_DINO_LOCAL_FILES_ONLY=true
```

If the optional packages or model files are unavailable, HiveSight records visible `prelabel_failed` evidence instead of silently falling back to deterministic suggestions.

The first implementation is deliberately a scaffold. It proves the service boundaries before adding persistence, authentication, queues, object-storage signing, and model inference.

## Verification

Run the current slice verification suite from the repo root:

```sh
pnpm verify:slice
```

This runs the Core API tests, Analysis Service tests, Web TypeScript check, and Web browser acceptance tests, then writes a summary report to `reports/slice-verification/latest.md`.

The live Postgres persistence integration test is opt-in so the fast suite still works without Docker. To run it, start Docker Desktop and local Postgres, then provide a test database URL:

```sh
pnpm db:up
HIVESIGHT_TEST_DATABASE_URL=postgresql://hive_sight:hive_sight@localhost:5432/hive_sight_core services/core-api/.venv/bin/python -m pytest services/core-api/tests/test_postgres_persistence_slice.py
```

Run only the Web browser acceptance test:

```sh
pnpm test:acceptance:web
```

Run the browser acceptance test visibly for local debugging:

```sh
pnpm --filter @hive-sight/web test:acceptance:headed
```
