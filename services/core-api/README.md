# Core API

The Core API is the protected product-facing service boundary.

Responsibilities:

- Workspace-scoped product data.
- Apiaries, hives, inspections, frame labels, and inspection-photo metadata.
- Workspace Data Use Agreement state.
- User-facing analysis status and summaries.
- Authorization decisions before upload, view, or analysis actions.

The default local mode still uses fast in-memory adapters for ordinary workflow tests. Postgres-backed metadata is available for the Bee Annotation Repository and model-training records.

From the repo root:

```sh
pnpm db:up
pnpm db:migrate
HIVESIGHT_PERSISTENCE_BACKEND=postgres pnpm dev:all
```

Image bytes remain outside Postgres. The database stores source image metadata, object keys, inspection context, Training Crops, oriented bee ellipses, Dataset Items, snapshots, and provenance.

`pnpm db:reset` targets the local test database by default. Use `pnpm db:reset:dev` only when you deliberately want to wipe and reseed the development database.
