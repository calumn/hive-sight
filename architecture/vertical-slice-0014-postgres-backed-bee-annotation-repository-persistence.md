# Vertical Slice 0014: Postgres-Backed Bee Annotation Repository Persistence

Status: closed. Implemented, fast-suite verified, browser-verified, and live Postgres restart verified.

## Purpose

Introduce durable Postgres-backed metadata persistence for the Bee Annotation Repository path that feeds future model training.

This slice makes reviewed bee evidence durable before Slice 0015 YOLO OBB Training Baseline records Training Runs and Model Candidates. It replaces the in-memory dev store as the acceptance-test persistence path for the selected records while keeping image bytes outside Postgres.

## Source Inputs

- `architecture/vertical-slice-0013-review-recommendations-architecture-decision-pass.md`
- `architecture/vertical-slice-0013.5-domain-model-persistence-stability-gate.md`
- `architecture/adr/0003-postgres-for-durable-product-and-model-governance-metadata.md`
- `architecture/postgres-persistence-design.md`
- `architecture/current-system-architecture.md`
- `architecture/proposed-system-architecture.md`
- `architecture/review-remediation-0001-extract-domain-rules-out-of-dev-store.md`
- `architecture/codebase-design.md`
- `CONTEXT.md`

## User Path

Given a Dataset Curator creates reviewed bee evidence
When HiveSight records Training Crops, Oriented Bee Ellipses, Dataset Items, and provenance
Then the metadata survives API restarts and can feed future dataset export and model training workflows
And local dev acceptance tests exercise the Postgres-backed path.

## Preconditions

- Slice 0013 has accepted Postgres for durable metadata.
- Slice 0013 has produced the Postgres persistence design.
- Slice 0013.5 has reviewed and hardened the domain model for persistence stability.
- Slice 0013.5 has classified domain records into stable records, version/history-sensitive records, and volatile/deferred records before schema implementation starts.
- Docker is available for local Postgres development.
- The existing local object-storage adapter remains available for image bytes.
- Dev auth remains explicitly dev-only through `x-hivesight-dev-user-id`.

## End-To-End Behaviour

The developer starts the HiveSight stack locally with Postgres available. Migrations create the first durable schema and a seed/reset command creates deterministic dev personas, Workspace Memberships, and Internal Capabilities.

Core API uses Postgres-backed repositories for the Bee Annotation Repository path:

- User
- Workspace
- Workspace Membership
- Internal Capability
- Apiary
- Hive
- Hive Configuration
- Inspection
- Source Image metadata and object key
- Inspection Photo product context
- Training Crop
- Oriented Bee Ellipse
- Dataset Item
- Dataset Item ellipse snapshot
- Dataset Item provenance snapshot

Image bytes remain in the existing local object-storage adapter. Postgres stores object keys and metadata only.

The implementation should treat the schema as deliberately narrow rather than final. Stable records can be persisted directly, history-sensitive records should preserve snapshots or provenance where needed, and volatile/deferred records should stay out of the first migration.

API-level BDD and browser acceptance tests run against the Postgres-backed Core API path once the slice is complete. Fast workflow/unit tests may still use in-memory adapters.

Local network/mobile UI testing must remain available after Postgres is introduced.

## Layers Touched

- Web UI: no product workflow changes; may need environment/dev command documentation updates.
- Core API: add Postgres repository adapters, migration integration, seed/reset support, and route wiring for the selected persistence path.
- Analysis Service: not touched.
- Storage: add Postgres for metadata; keep image bytes outside Postgres.
- Queue or async boundary: not touched.
- Contracts: no public API shape changes expected.
- Observability: preserve existing `DomainError` codes; add clear startup/config errors for missing database if needed.

## Test Seams

- Seam: repository contract tests
- Behaviour verified: Postgres repositories preserve the same behaviour expected by Core API workflows for selected records.
- Test style: integration tests against test Postgres.

- Seam: Core API
- Behaviour verified: Bee Annotation Repository path works across app restart or fresh API client while using Postgres-backed metadata.
- Test style: API tests and API-level BDD.

- Seam: Web browser acceptance
- Behaviour verified: existing acceptance workflows still pass against Postgres-backed Core API.
- Test style: Playwright.

- Seam: developer workflow
- Behaviour verified: local reset/seed command applies migrations and creates deterministic dev personas/capabilities.
- Test style: script test or documented command verification.

## Data Shape

Postgres stores metadata, relationships, status, object keys, provenance, and timestamps.

Slice 0014 must persist `Source Image` and `Inspection Photo` separately:

- `Source Image` owns image/file evidence, dimensions, content hash, provenance, permission status, metadata minimisation status, lifecycle status, and object key.
- `Inspection Photo` owns beekeeper/product inspection context and points to one Source Image.
- Slice 0014 implements only `source_type = inspection_photo`, while preserving the future ability to add public/imported/bootstrap source image types.
- Training Crop points to Source Image directly and may also reference Inspection Photo when the source type is `inspection_photo`.
- Training Crop and Dataset Item keep direct `workspace_id`, matching Source Image workspace for Slice 0014.
- Source Image, Training Crop, and Dataset Item have immutable generated human-readable ids.
- Accepted Source Images require dimensions, `content_hash`, and `content_hash_algorithm`.
- Raw EXIF/image metadata is not stored in Postgres; only metadata minimisation status is stored.
- Hive Configuration is effective-dated history with one active configuration per Hive.
- Dataset Items are immutable after assignment and include supersession/withdrawal shape.
- Benchmark Dataset Items require `source_group_key`.
- Dataset Role assignment hard-blocks benchmark conflicts for the same Source Image or same `source_group_key`.

Postgres does not store:

- image bytes
- raw EXIF/image metadata
- dataset export package file contents
- Training Run records
- Model Candidate records
- Model Version records
- Benchmark Evaluation records
- production auth provider identities
- Analysis Service-owned result store records

The first migration should follow `architecture/postgres-persistence-design.md` and may refine naming during implementation if the design doc is updated in the same slice.

## Developer Commands

Slice 0014 should add or update commands for:

- starting local Postgres through Docker Compose
- applying migrations
- resetting local/test database state
- seeding deterministic dev personas and Internal Capabilities
- running acceptance verification against the Postgres-backed path

The exact command names should follow existing repo conventions, but the expected developer experience is one-command reset and one-command stack startup.

## Out Of Scope

- Storing image bytes in Postgres.
- Selecting production object storage provider.
- Selecting production auth provider.
- Selecting durable queue technology.
- Selecting deployment platform.
- Persisting Training Runs or Model Candidates.
- Persisting Model Versions or Benchmark Evaluations.
- Implementing Analysis Service persistence.
- Implementing dev persona switcher UI.
- Implementing UI-level Gherkin.

## Acceptance Criteria

- [ ] Postgres is available in local development through Docker.
- [ ] Database migrations are introduced and run from a documented command.
- [ ] The first schema follows the Slice 0013 domain stability classification and does not persist volatile/deferred records.
- [ ] A reset/seed command rebuilds the schema and creates deterministic dev personas and Internal Capabilities.
- [ ] Core API uses Postgres-backed persistence for the selected Bee Annotation Repository metadata path.
- [ ] Source Image and Inspection Photo are separate persisted records, with Inspection Photo referencing Source Image.
- [ ] Training Crop references Source Image directly.
- [ ] Source Image, Training Crop, and Dataset Item have immutable generated human-readable ids.
- [ ] Accepted Source Images store mandatory dimensions, content hash, and content hash algorithm.
- [ ] Raw EXIF/image metadata is not stored in Postgres.
- [ ] Hive Configuration persistence is effective-dated and enforces one active configuration per Hive.
- [ ] Dataset Item assignment snapshots permission, provenance, reviewed ellipses, source group key, and resolved Hive Configuration.
- [ ] Dataset Items are immutable after assignment and include `active`, `superseded`, and `withdrawn` status shape.
- [ ] Benchmark Dataset Item assignment requires `source_group_key`.
- [ ] Benchmark leakage conflicts are hard-blocked for same Source Image and same `source_group_key`.
- [ ] Image bytes remain outside Postgres and are referenced by object key.
- [ ] Existing public Core API request/response shapes remain unchanged.
- [ ] Existing API-level BDD scenarios pass against the Postgres-backed path.
- [ ] Existing Playwright browser acceptance tests pass against the Postgres-backed path.
- [ ] Fast workflow/unit tests can still use in-memory adapters where appropriate.
- [ ] Local network/mobile UI testing remains documented and viable.
- [ ] Slice 0015 remains blocked until this slice is complete.
- [ ] `pnpm verify:slice` passes.

## Open Questions

- Which Python migration tool will be used? Recommendation: Alembic unless implementation context suggests otherwise.
- Should Postgres test setup use one shared test database with schema reset, or per-test temporary schemas?
- Should deterministic dev personas be seeded by migration, separate seed script, or reset command? Recommendation: separate seed/reset command so production migrations do not contain dev data.
- Should repository protocols be formalized before implementation or introduced as each adapter is written?
- Should training-vs-validation `source_group_key` sharing produce only export/report warnings in Slice 0014, or also API response warnings during assignment?

## Implementation Notes

- Implemented SQL migrations through repo-local migration files and `hive_sight_core_api.db` commands rather than Alembic. This keeps Slice 0014 dependency weight low while preserving migration discipline from day one.
- Added local commands: `pnpm db:up`, `pnpm db:migrate`, `pnpm db:seed`, and `pnpm db:reset`.
- Added opt-in Core API Postgres mode through `HIVESIGHT_PERSISTENCE_BACKEND=postgres`.
- Added a write-through Postgres store adapter for the selected Bee Annotation Repository path while keeping the in-memory adapter for fast workflow/unit tests.
- Added `source_images` and `inspection_photos` as separate persisted records; image bytes remain in object storage.
- Added source-image dimensions and content hash capture during photo intake; raw image metadata is not stored.
- Added immutable human-readable id generation shape for Source Images, Training Crops, and Dataset Items.
- Enforced benchmark Dataset Item `source_group_key` for both dataset-labelling and Training Crop assignment paths.
- Added a browser UI field for benchmark Training Crop source group assignment.
- Added an always-on migration contract test and an opt-in real Postgres restart integration test controlled by `HIVESIGHT_TEST_DATABASE_URL`.
- `pnpm verify:slice` passed after implementation.
- Live Postgres closeout verification passed on 2026-07-31:
  - Docker was available.
  - `docker compose up -d postgres` confirmed the local Postgres container was running.
  - `docker compose exec -T postgres pg_isready -U hive_sight` confirmed Postgres was accepting connections.
  - `pnpm db:reset` rebuilt and seeded the local schema.
  - `HIVESIGHT_TEST_DATABASE_URL=postgresql://hive_sight:hive_sight@localhost:5432/hive_sight_core services/core-api/.venv/bin/python -m pytest services/core-api/tests/test_postgres_persistence_slice.py -p no:cacheprovider` passed with `2 passed`.
