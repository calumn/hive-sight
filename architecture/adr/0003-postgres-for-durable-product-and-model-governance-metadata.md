# Postgres For Durable Product And Model-Governance Metadata

Status: accepted

## Context

HiveSight has reached the point where the in-memory Core API store is no longer enough for the next tranche of work. The Bee Annotation Repository path now needs durable metadata so reviewed bee evidence can survive restarts, feed physical dataset export, and later support Training Run and Model Candidate records.

The project also needs a persistence choice before the first trainable YOLO OBB baseline. Without durable metadata, model-training evidence would be difficult to audit, reproduce, or compare over time.

Image bytes, dataset package files, and future model artifacts are not good fits for relational storage. They remain object-storage concerns.

## Decision

HiveSight will use Postgres as the first durable metadata store for Core API product data and model-governance metadata.

Postgres will store:

- ownership and identity metadata
- Workspace Membership and Internal Capability records
- apiary, hive, Hive Configuration, inspection, and Inspection Photo metadata
- object keys that reference image bytes outside Postgres
- Training Crop metadata
- reviewed oriented bee ellipse metadata
- Dataset Item metadata, role assignment, provenance snapshots, and reviewed ellipse snapshots
- later Training Run, Model Candidate, Model Version, and Benchmark Evaluation metadata when those slices arrive

Postgres will not store original image bytes, generated image files, physical dataset package files, or model artifact files.

The first implementation slice should persist one narrow path: Bee Annotation Repository metadata needed before the YOLO OBB Training Baseline. API-level BDD and browser acceptance should move to the Postgres-backed path when that slice lands. Fast workflow/unit tests may continue to use in-memory adapters.

## Considered Options

- **Keep only the in-memory store**: fastest for prototyping, but no durable audit trail, restart survival, or trustworthy model-training evidence.
- **SQLite**: simple local durability, but less representative of production concurrency, migration, and operational patterns.
- **Document database**: flexible for evolving shapes, but weaker fit for Workspace ownership, dataset role constraints, provenance, and relational model-governance queries.
- **Postgres**: strong relational integrity, mature migrations, local Docker support, production-ready path, and flexible JSON support where needed.

## Rationale

Postgres gives the project durable relational integrity without forcing a premature production deployment stack. HiveSight's near-term persistence needs are relationship-heavy: Workspace ownership, inspection/photo provenance, reviewed annotations, dataset roles, and audit snapshots.

Choosing Postgres now does not settle object storage, durable queue technology, production auth provider, deployment platform, or Analysis Store ownership. Those remain parked with explicit triggers.

## Consequences

- Slice 0014 should introduce local Postgres through Docker, migrations, repository adapters, and deterministic seed/reset commands.
- Domain and workflow rules must stay in workflows or policy services, not in Postgres adapters.
- Repository protocols should be shaped around workflow needs rather than table layouts.
- The first schema must classify records into stable, history-sensitive, and volatile/deferred groups before migration work starts.
- Image bytes continue to live behind an object-storage seam.
- Migration tooling is required from the first durable schema.
- Future schema changes must preserve provenance for reviewed evidence and model-governance records.

