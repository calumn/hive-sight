# Vertical Slice 0013.5: Domain Model Persistence Stability Gate

Status: implemented.

## Purpose

Harden the HiveSight domain model before implementing durable persistence.

This is a design slice, not a runtime feature slice. It exists because once Slice 0014 introduces Postgres migrations, domain-model mistakes become more expensive to unwind. The slice should look for edges that could distort the first durable schema, especially around source image provenance, hive equipment history, dataset split leakage, consent snapshots, and Dataset Item correction/supersession.

The outcome should be a small set of accepted model adjustments and an updated Slice 0014 persistence plan.

## Source Inputs

- `CONTEXT.md`
- `requirements/model-requirements.md`
- `requirements/ai-assisted-annotation-and-model-training-baseline.md`
- `requirements/bee-annotation-repository-and-curriculum-training-baseline.md`
- `architecture/domain-model.md`
- `architecture/domain-model-diagram.md`
- `architecture/postgres-persistence-design.md`
- `architecture/vertical-slice-0010-bee-annotation-repository-and-dataset-export.md`
- `architecture/vertical-slice-0013-review-recommendations-architecture-decision-pass.md`
- `architecture/vertical-slice-0014-postgres-backed-bee-annotation-repository-persistence.md`
- `architecture/parking-lot.md`

## User Path

Given HiveSight is about to introduce durable Postgres metadata
When the team reviews the domain model for persistence stability
Then the team knows which records are safe to persist now
And which records need snapshots, provenance, grouping, or deferral
And Slice 0014 can be implemented without knowingly baking in a brittle domain shape.

## Preconditions

- Slice 0013 has accepted Postgres as the durable metadata direction.
- Slice 0014 has not yet implemented migrations.
- The review is allowed to reshape Slice 0014 if the domain model is not stable enough.
- The review should preserve existing product intent unless the team explicitly changes it.

## End-To-End Behaviour

The team reviews the current domain model against likely future HiveSight uses:

- project-owned training photos
- public or externally sourced bootstrap images
- imported annotation datasets
- source/hive/frame provenance for bias analysis
- Hive Configuration changes over time
- multiple photos of the same frame or near-duplicate source images
- training, validation, benchmark, and excluded Dataset Roles
- user consent, Workspace Data Use Agreement withdrawal, and deletion requests
- future Training Runs, Model Candidates, Model Versions, and Benchmark Evaluations
- future Varroa annotation and Varroa assessment workflows

For each risky edge, the team decides whether to:

- adjust the domain model before persistence
- add a field or snapshot requirement to the first Postgres design
- explicitly defer the concept from Slice 0014
- park the risk with a revisit trigger

The slice ends when `architecture/domain-model.md`, `architecture/postgres-persistence-design.md`, and `architecture/vertical-slice-0014-postgres-backed-bee-annotation-repository-persistence.md` agree on the first durable shape.

## Review Focus

### Source Image Abstraction

Current risk:

`Training Crop` is currently derived from an `Inspection Photo`. That is correct for project-owned hive photos, but it may force public/bootstrap/imported images to masquerade as ordinary inspection photos.

Question to answer:

Should HiveSight introduce a more general `Source Image` or `Evidence Image` concept before persistence, with `Inspection Photo` as one source type?

Expected decision:

Introduce `Source Image` now. `Inspection Photo` is the beekeeper/product-facing role a Source Image plays when attached to an Inspection.

Locked decisions:

- Add `Source Image` to `CONTEXT.md`.
- Keep product language as `Inspection Photo`.
- Slice 0014 persists two tables: `source_images` and `inspection_photos`.
- Slice 0014 implements only `source_type = inspection_photo`, but the model allows future public/imported/bootstrap source types.
- `Source Image` owns object key, filename, media type, file size, dimensions, content hash, provenance, permission status, metadata status, and evidence lifecycle status.
- `Inspection Photo` owns inspection/product context and points to one `Source Image`.
- `source_images.workspace_id` is required for `inspection_photo` source images in Slice 0014, while future non-Workspace/imported ownership remains possible.
- `Source Image` is strictly image-only for now.
- Source Image, Training Crop, and Dataset Item each receive stable immutable human-readable ids with prefixed strings such as `HS-SI-000001`, `HS-TC-000001`, and `HS-DI-000001`.

### Hive Configuration History

Current risk:

Hive Configuration is model context, and training data should preserve what was known when the Source Image was captured or reviewed. A mutable "current configuration" model may corrupt historical interpretation.

Question to answer:

Should Hive Configuration be append-only or effective-dated from the first persisted schema?

Expected decision:

Define whether Slice 0014 stores Hive Configuration history directly, stores Dataset Item snapshots only, or does both.

Locked decisions:

- Hive Configuration is effective-dated history, not a mutable single truth.
- Store `effective_from` and `effective_to`.
- Enforce one active Hive Configuration per Hive from Slice 0014.
- Inspection creation requires an active Hive Configuration.
- Dataset Item snapshots capture-time Hive Configuration when resolvable, otherwise assignment-time fallback, otherwise unknown.
- `box_use` stays on Hive Configuration for Slice 0014 and is snapshotted on Dataset Item.
- Detailed Hive Component / Box configuration is parked.

### Dataset Split Leakage

Current risk:

Requirements warn that frame-level, near-duplicate, inspection-level, hive-level, or source-level leakage can invalidate benchmark claims. The first schema does not yet name durable grouping fields.

Question to answer:

Which manual grouping fields must exist before assigning `training`, `validation`, or `benchmark` roles durably?

Expected decision:

Decide whether Slice 0014 includes fields such as `source_group_key`, `frame_group_key`, `duplicate_group_key`, or `leakage_group_key`, and where they live.

Locked decisions:

- Add one broad `source_group_key` for Slice 0014.
- Store `source_group_key` on Source Image and snapshot it onto Dataset Item.
- Require `source_group_key` for benchmark Dataset Items.
- Hard-block benchmark conflicts by same Source Image and same `source_group_key`.
- Allow training/validation to share `source_group_key` in Slice 0014, but exports/reports must flag it as a leakage warning.
- Same Hive/Inspection leakage policy is parked for later.

### Dataset Item Identity And Supersession

Current risk:

Slice 0010 allows one Dataset Item per Training Crop and defers supersession. Once Dataset Items are persisted, mutating evidence could undermine training reproducibility.

Question to answer:

Is a Dataset Item immutable after assignment, with correction handled by superseding records, or can it be edited until a Dataset Version is created?

Expected decision:

Define the first persisted posture for Dataset Item mutation, correction, and supersession.

Locked decisions:

- Dataset Items are immutable after assignment.
- Corrections use supersession or withdrawal rather than in-place mutation.
- Slice 0014 includes status values `active`, `superseded`, and `withdrawn`.
- Slice 0014 includes supersession fields, but does not implement the full supersession workflow.
- Training Crop and Oriented Bee Ellipses are mutable during review but locked once a Dataset Item is created.

### Consent And Permission Snapshot

Current risk:

Workspace Data Use Agreement status is traceable through Workspace ownership, but withdrawal, deletion, prior uploads, and already-trained artifacts remain unresolved.

Question to answer:

What exact permission and data-use fields must be snapshotted on Dataset Item assignment in Slice 0014?

Expected decision:

Define the minimum Dataset Item permission snapshot for local/project-owned data without pretending the legal/policy workflow is complete.

Locked decisions:

- Source Image has its own provenance and permission status.
- Dataset Item snapshots Workspace Data Use Agreement eligibility at assignment time.
- Slice 0014 `inspection_photo` Source Images use Workspace Data Use Agreement eligibility.
- Source Image may exist without dataset eligibility, but Dataset Item creation requires eligible permission.
- Consent withdrawal after assignment does not automatically remove Dataset Items from future training/export in Slice 0014.
- Withdrawal and deletion enforcement remain parked.
- Source Image records metadata minimisation status only.
- Slice 0014 must not store raw EXIF/image metadata in Postgres.
- Image metadata is treated as potentially personally identifiable information.

### Annotation Geometry Future-Proofing

Current risk:

Bee annotations are canonical oriented ellipses, but future Varroa labels, uncertainty flags, and possibly segmentation/keypoint experiments should not force a rewrite of bee evidence.

Question to answer:

Should Slice 0014 persist `Oriented Bee Ellipse` as its own narrow table, or introduce a more generic annotation table with geometry type?

Expected decision:

Choose the narrower first shape unless there is a strong reason to persist a generic annotation table now.

Locked decision:

Slice 0014 persists a narrow `Oriented Bee Ellipse` table, not a generic annotation table.

## Layers Touched

- Web UI: not touched.
- Core API: not touched.
- Analysis Service: not touched.
- Storage: no runtime storage changes; Postgres design may change.
- Queue or async boundary: not touched.
- Contracts: no public API changes; schema design only.
- Observability: not touched.

## Test Seams

- Seam: domain model review
- Behaviour verified: risky future-use cases are classified as stable, snapshot/history-sensitive, volatile/deferred, or parked.
- Test style: document review checklist.

- Seam: persistence design
- Behaviour verified: proposed Slice 0014 schema reflects the accepted stability decisions.
- Test style: artifact inspection.

- Seam: parking lot
- Behaviour verified: deferred risks have explicit revisit triggers.
- Test style: artifact inspection.

## Data Shape

This slice may add or refine planning-only data concepts:

- Source Image or Evidence Image
- Inspection Photo as product context for one Source Image
- source type
- source provenance
- source permission status
- source group key
- content hash and content hash algorithm
- source image dimensions
- metadata minimisation status
- Hive Configuration effective history
- Dataset Item permission snapshot
- Dataset Item supersession fields

No database migration is created in this slice.

## Out Of Scope

- Implementing Postgres.
- Writing migrations.
- Adding repository adapters.
- Changing runtime API behaviour.
- Importing public/bootstrap datasets.
- Implementing automatic duplicate or near-duplicate detection.
- Implementing consent withdrawal, deletion, or purge workflows.
- Implementing Dataset Versions, Training Runs, Model Candidates, Model Versions, or Benchmark Evaluations.
- Implementing Varroa detection or Varroa annotation workflows.

## Acceptance Criteria

- [x] The review explicitly decides whether `Source Image` / `Evidence Image` is needed before Slice 0014 persistence.
- [x] Hive Configuration history or snapshot semantics are decided before migration work starts.
- [x] Durable manual grouping needs for source/frame/duplicate/leakage risk are decided.
- [x] Dataset Item mutation and supersession posture is decided.
- [x] Dataset Item permission/data-use snapshot fields are decided.
- [x] The review decides whether Slice 0014 should persist a narrow `Oriented Bee Ellipse` table or a generic annotation table.
- [x] `architecture/domain-model.md` is updated with accepted model changes.
- [x] `architecture/domain-model-diagram.md` is updated if relationships change materially.
- [x] `architecture/postgres-persistence-design.md` is updated with the final Slice 0014 schema classification.
- [x] `architecture/vertical-slice-0014-postgres-backed-bee-annotation-repository-persistence.md` is updated to reflect any changes or new prerequisites.
- [x] Any deferred but important risks are captured in `architecture/parking-lot.md`.
- [x] `requirements/ai-sdlc-observations.md` records the persistence stability gate outcome.

## Open Questions

- Resolved: use `Source Image`.
- Resolved: model future source types now, but Slice 0014 implements only `inspection_photo`.
- Resolved: use one broad `source_group_key`.
- Resolved: include supersession shape in Slice 0014, but park full workflow.
- Resolved: one Dataset Item per Training Crop remains acceptable before Dataset Version creation.

## Closeout Decisions

- Slice 0014 may proceed after this stability gate.
- Slice 0014 must persist `source_images` and `inspection_photos` separately.
- Slice 0014 must implement only `inspection_photo` Source Images while preserving future source types.
- Slice 0014 must keep Training Crop and Dataset Item tied directly to Source Image.
- Slice 0014 must persist effective-dated Hive Configuration history and one active Hive Configuration per Hive.
- Slice 0014 must include the first manual leakage hook through `source_group_key`.
- Slice 0014 must treat Dataset Items as immutable evidence with supersession/withdrawal shape.
- Full Dataset Item audit events, Dataset Versions, detailed Hive Component/Box configuration, consent withdrawal enforcement, and stricter split leakage policy remain parked.
