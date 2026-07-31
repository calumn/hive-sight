# Core API

The Core API is the protected product-facing service boundary.

Responsibilities:

- Workspace-scoped product data.
- Apiaries, hives, inspections, frame labels, and inspection-photo metadata.
- Workspace Data Use Agreement state.
- User-facing analysis status and summaries.
- Authorization decisions before upload, view, or analysis actions.

The default local mode still uses fast in-memory adapters for ordinary workflow tests. Slice 0014 adds an opt-in Postgres-backed metadata path for the Bee Annotation Repository records.

From the repo root:

```sh
pnpm db:up
pnpm db:reset
HIVESIGHT_PERSISTENCE_BACKEND=postgres pnpm dev:all
```

Image bytes remain outside Postgres. The database stores source image metadata, object keys, inspection context, Training Crops, oriented bee ellipses, Dataset Items, snapshots, and provenance.
