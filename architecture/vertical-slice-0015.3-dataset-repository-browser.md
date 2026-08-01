# Vertical Slice 0015.3: Dataset Repository Browser

Status: planned.

## Purpose

Let a Dataset Curator see the Bee Annotation Repository they are building across multiple Training Data Collection inspections, including which reviewed Training Crops have been assigned to training, validation, benchmark, or excluded Dataset Roles, and which Dataset Version has frozen them for model training.

This slice exists because HiveSight can already create cross-inspection Dataset Items and Dataset Versions, but the UI does not yet give the curator a coherent way to answer: "What is actually in my dataset?"

## Source Inputs

- `CONTEXT.md`
- `requirements/model-requirements.md`
- `requirements/ai-assisted-annotation-and-model-training-baseline.md`
- `requirements/bee-annotation-repository-and-curriculum-training-baseline.md`
- `architecture/domain-model.md`
- `architecture/domain-model-diagram.md`
- `architecture/postgres-persistence-design.md`
- `architecture/adr/0002-oriented-ellipse-canonical-bee-annotations.md`
- `architecture/adr/0003-postgres-for-durable-product-and-model-governance-metadata.md`
- `architecture/vertical-slice-0010-bee-annotation-repository-and-dataset-export.md`
- `architecture/vertical-slice-0014-postgres-backed-bee-annotation-repository-persistence.md`
- `architecture/vertical-slice-0015-yolo-obb-training-baseline.md`
- `architecture/vertical-slice-0015.2-model-candidate-crop-pre-labelling.md`
- Curator feedback after assigning crops from multiple inspections and needing to see the complete dataset.
- `architecture/parking-lot.md`, especially PARK-0012, PARK-0014, PARK-0015, and PARK-0016.
- Slice 0015.3 grilling decisions on naming, page shape, filters, repository warnings, provenance, Dataset Version membership, and read-only scope.

## User Path

Given a Dataset Curator has assigned reviewed Training Crops from one or more Training Data Collection inspections into Dataset Roles
When the Dataset Curator opens the Bee Annotation Repository page
Then HiveSight shows the active Bee Annotation Repository for the Workspace
And the curator can filter by Dataset Role, inspection, hive, Source Image, Dataset Version membership, review provenance, and bee-class presence
And the curator can inspect each Dataset Item's crop preview, source traceability, reviewed bee counts, and assignment evidence
And the curator can see whether the current Dataset Version contains each item.

## Preconditions

- Slice 0014 Postgres-backed Bee Annotation Repository persistence is implemented.
- Slice 0015 Dataset Versions and Training Runs are implemented.
- Slice 0015.2 Model Candidate crop pre-labelling is implemented or in progress; provenance fields may already distinguish human-from-scratch and human-reviewed-candidate evidence.
- Docker/Postgres is available before the slice can be fully acceptance-closed because the browser is only valuable if repository metadata survives restart.
- The active user is a Dataset Curator or dev persona with equivalent internal capability.
- Workspace Data Use Agreement is accepted.
- At least one Dataset Item exists for the Workspace, or the browser must show a useful empty state.

## Settled Design Decisions

- UI name: **Bee Annotation Repository**. Use supporting text such as "Dataset items for training, validation, benchmark, and excluded evidence" where helpful.
- Page shape: a separate page experience behind an internal view switch, not a URL router in this slice.
- Layout: hybrid list with detail panel.
- Scope: read-only repository browser. No Dataset Item deletion, Dataset Role changes, Dataset Item reassignment, Dataset Item supersession, bulk actions, or Dataset Version creation from repository filters.
- Default scope: Workspace-wide active Dataset Items across all Hives, with Apiary/Hive filters available.
- Default ordering: group by Dataset Role, then newest assignment first within each role.
- Dataset Version membership: show latest Dataset Version membership in the list; show all known memberships in the detail panel when available.
- Provenance: annotation source and review method counts are required at repository, item, and Dataset Version summary level.
- Bee classes: complete visible bee and partial visible bee counts are shown separately.
- Benchmark evidence: visible in the same browser, with clear protected-benchmark treatment.
- Warnings: repository quality warnings are computed live and non-blocking. Dataset Version warnings remain frozen with Dataset Versions.
- Dataset Version creation: existing Dataset Version selection rules are unchanged; repository filters do not affect Dataset Version creation.
- Navigation: include `Open crop in editor` only if it restores the full inspection/photo/crop context automatically. Otherwise omit it and park the action.
- Empty states: distinguish no crops, completed-but-unassigned crops, and assigned Dataset Items.
- Unassigned completed crops: show a count and link/list if implementation cost stays small.
- Images: show small crop thumbnails in the list and a larger crop preview in detail. If image bytes are unavailable, keep the Dataset Item visible with an image-unavailable state and warning.
- Source context: crop preview is required; a small Source Image context thumbnail with crop rectangle is optional if cheap.
- Identifiers: human-readable ids first; raw UUIDs in detail for debugging and traceability.
- Diversity visibility: show simple distribution chips and concrete warnings, not a health score.
- Search and filters: include simple search and filters; no pagination in this slice.
- Persistence visibility: show small backend/database-purpose status on the repository page.
- Responsive support: basic responsive layout only.
- Documentation: user guide update is required acceptance evidence.

## End-To-End Behaviour

The Dataset Curator opens a new **Bee Annotation Repository** page from the current local development UI. The first implementation uses an internal view switch or tab-style navigation rather than full URL routing. The page preserves the selected User and Workspace context.

HiveSight fetches a Workspace-level repository summary from Core API. The summary includes:

- active Dataset Item counts by Dataset Role
- unassigned completed crop count, if cheap to compute
- new-since-latest-Dataset-Version count
- reviewed annotation counts by class
- annotation source counts
- review method counts
- curriculum stage distribution
- image quality distribution
- hive configuration distribution
- source group distribution
- diversity distribution chips, such as inspection count, hive count, Source Image count, and frame standard count
- Dataset Version count and latest Dataset Version summary
- small persistence backend/database purpose status

The page shows four primary Dataset Role bands or filters:

- Training
- Validation
- Benchmark
- Excluded

The page defaults to Workspace-wide active Dataset Items across all Hives. It groups items by Dataset Role and orders newest assignments first inside each role.

Each Dataset Item row or compact card shows a small crop thumbnail and enough information to understand provenance without opening database records:

- human-readable Dataset Item id, if available, falling back to short UUID
- Dataset Role
- status, initially active only
- Source Image / Inspection Photo filename or short id
- Inspection date and intent, where available
- Apiary, Hive, and Hive Configuration snapshot summary, where available
- Training Crop index or crop id
- crop dimensions and curriculum stage
- complete visible bee count
- partial visible bee count
- review method and annotation source summary
- model-assisted provenance badge when any reviewed ellipse came from a Model Candidate
- assigned by, assigned at, and assignment note
- source group key, if present
- benchmark protected flag, if applicable
- exclusion reason, if applicable
- export eligibility badge, such as `eligible for training export`, `validation export`, `protected benchmark`, `excluded`, or `not exportable: image unavailable`
- Dataset Version membership badge for the latest Dataset Version
- `New since latest version` badge when the item is not in the latest Dataset Version

The UI includes filters for:

- Dataset Role
- active Dataset Version membership: latest, any, none
- new since latest Dataset Version
- Inspection
- Inspection Intent
- Hive
- Source Image / Inspection Photo
- Curriculum Stage
- annotation source / review method
- image quality
- has complete visible bees
- has partial visible bees
- text search across human-readable ids, filenames, hive names, and assignment notes

The browser supports a compact detail panel for a selected Dataset Item. The detail panel shows:

- crop preview with reviewed Oriented Bee Ellipses rendered over the crop
- image-unavailable state if preview bytes cannot be loaded
- optional Source Image context thumbnail with crop rectangle, if implementation cost stays small
- Source Image traceability
- Inspection and Hive Configuration provenance
- reviewed ellipse snapshots
- Dataset Role assignment evidence
- raw UUIDs for Dataset Item, Training Crop, Inspection Photo, Source Image, Inspection, Hive, and Apiary where available
- all available Dataset Version memberships for the item
- optional Training Run / Model Candidate consumption trace if cheap

If the Dataset Item belongs to a Training Crop, the detail panel may include **Open crop in editor**. This action is included only if it restores the full Apiary/Hive/Inspection/Inspection Photo/Training Crop context automatically. A half-built button that merely tells the curator to find the crop manually is out of scope.

The page has distinct empty states:

- no Training Crops exist: tell the curator to create and annotate Training Crops first
- completed Training Crops exist but none are assigned: tell the curator to assign completed crops to training, validation, benchmark, or excluded roles
- assigned Dataset Items exist: show the repository browser

The browser also makes the current training pipeline more legible. Near the Dataset Version controls, the curator can open the repository browser filtered to:

- all active items eligible for the next Dataset Version
- all items in the latest Dataset Version
- items excluded from the latest Dataset Version with reasons
- benchmark-protected items

Repository warnings are concrete and non-blocking. Examples:

- no benchmark items yet
- validation set is small
- all Dataset Items come from one Inspection, Hive, or Source Image
- training and validation share Source Images
- benchmark shares Source Image or source group with training/validation
- non-Training Data Collection Inspection Intent appears in active Dataset Items
- thumbnail or detail preview image bytes are unavailable

This slice is read-only. It does not introduce Dataset Item reassignment, edit, supersession, deletion, consent withdrawal, public dataset import, blind-review comparison, model promotion workflows, or any repository-filter-driven Dataset Version creation.

## Layers Touched

- Web UI: Add a separate Bee Annotation Repository page via internal view switch, with counts, filters, simple search, item list, item detail, crop thumbnails, crop preview, Dataset Version membership badges, repository warnings, backend/database status, and navigation back to the Training Crop editor only when context restoration is complete.
- Core API: Add read-side endpoints for repository summary, Dataset Item list, and Dataset Item detail. Include filters as query parameters. Reuse existing dev auth and Dataset Curator capability checks. Do not let repository filters change Dataset Version creation semantics.
- Analysis Service: Not touched.
- Storage: No new write model required. Query existing Postgres-backed Dataset Items, Training Crops, Source Images, Inspection Photos, Inspections, Hives, Apiaries, and Dataset Versions. Dev-store support remains needed for fast tests.
- Queue or async boundary: Not touched.
- Contracts: Add response shapes for Bee Annotation Repository summary, Dataset Item list entries, Dataset Item detail, Dataset Version membership summaries, repository warnings, export eligibility badges, and preview metadata.
- Observability: Log repository summary/list/detail requests with workspace id, filter fields, item count, and failure code. Do not log filenames or sensitive image metadata unnecessarily.

## Test Seams

- Seam: Dataset Repository read model
- Behaviour verified: Dataset Items from multiple Inspections in the same Workspace are listed together with correct Dataset Role counts and provenance.
- Test style: Core API route/workflow tests using deterministic fixture data.

- Seam: Dataset Version membership projection
- Behaviour verified: list responses show latest Dataset Version membership and new-since-latest status; detail responses show all available memberships when cheap.
- Test style: Core API tests.

- Seam: Workspace and capability boundary
- Behaviour verified: a Dataset Curator can browse repository items for their Workspace; another Workspace cannot see them; a user without internal dataset capability is blocked.
- Test style: Core API route tests and, if already covered elsewhere, focused regression assertions.

- Seam: Crop preview evidence
- Behaviour verified: item detail includes enough crop geometry and reviewed ellipse snapshot data for the UI to render the crop preview without mutating repository evidence.
- Test style: Core API tests plus browser acceptance.

- Seam: Web UI browser
- Behaviour verified: Dataset Curator can open the Bee Annotation Repository page, see counts across multiple inspections, filter by Dataset Role, search, select a Dataset Item, inspect provenance, see latest Dataset Version membership, and see non-blocking warnings.
- Test style: Playwright acceptance using fake/local data.

- Seam: empty and unavailable states
- Behaviour verified: no-crop, completed-unassigned, assigned-item, and image-unavailable states are distinct and understandable.
- Test style: Core API tests for response shape and Playwright acceptance for visible states where cheap.

- Seam: Live Postgres restart
- Behaviour verified: Dataset Repository Browser still shows the same assigned Dataset Items and latest Dataset Version after restarting Core API against Postgres.
- Test style: existing Postgres persistence test pattern or focused live Postgres verification.

## Data Shape

### Dataset Repository Summary

- `workspace_id`
- `dataset_item_count`
- `active_dataset_item_count`
- `unassigned_completed_crop_count`
- `new_since_latest_dataset_version_count`
- `role_counts`: training, validation, benchmark, excluded
- `annotation_class_counts`
- `annotation_source_counts`
- `review_method_counts`
- `curriculum_stage_distribution`
- `image_quality_distribution`
- `hive_configuration_distribution`
- `source_group_distribution`
- `inspection_distribution`
- `inspection_intent_distribution`
- `hive_distribution`
- `source_image_distribution`
- `latest_dataset_version`: optional summary
- `persistence_backend`
- `database_purpose`
- `warnings`: live computed non-blocking repository warnings

### Dataset Repository Item List Entry

- `dataset_item_id`
- `human_readable_id`
- `workspace_id`
- `dataset_role`
- `status`
- `source_evidence_type`
- `inspection_id`
- `inspection_date`
- `inspection_intent`
- `inspection_photo_id`
- `source_image_id`
- `source_filename`
- `apiary_id`
- `apiary_name`
- `hive_id`
- `hive_name`
- `hive_configuration_summary`
- `training_crop_id`
- `crop_x`
- `crop_y`
- `crop_width`
- `crop_height`
- `crop_image_width_px`
- `crop_image_height_px`
- `curriculum_stage`
- `complete_visible_bee_count`
- `partial_visible_bee_count`
- `annotation_source_counts`
- `review_method_counts`
- `source_group_key`
- `image_quality_status`
- `assigned_by_user_id`
- `assigned_at`
- `assignment_note`
- `exclusion_reason`
- `benchmark_protected`
- `export_eligibility`
- `latest_dataset_version_membership`
- `dataset_version_memberships`: compact list
- `is_new_since_latest_dataset_version`
- `preview_status`
- `thumbnail_url` or content endpoint metadata, if available

### Dataset Repository Item Detail

All list-entry fields plus:

- `reviewed_ellipse_snapshots`
- `provenance`
- `permission_status`
- `dataset_version_memberships`
- `training_run_consumption`: optional if cheap
- `model_candidate_consumption`: optional if cheap
- `preview`: crop/source image render metadata sufficient for the Web UI

### Dataset Version Membership Summary

- `dataset_version_id`
- `human_readable_id`
- `purpose`
- `status`
- `membership`: `included`, `training`, `validation`, `protected_benchmark`, `excluded`, or `not_in_version`
- `excluded_reason`, if applicable
- `created_at`

### Repository Warning

- `code`
- `severity`: initially `info` or `warning`; never blocking in this slice
- `message`
- `affected_dataset_item_ids`: optional, capped or omitted for large lists

## Out Of Scope

- Dataset Item reassignment or editing.
- Dataset Item supersession workflow.
- Dataset Item audit-event table.
- Dataset Item deletion.
- Bulk actions or multi-select.
- Consent withdrawal or deletion enforcement.
- Public dataset import.
- Full-frame or tiled YOLO export.
- Strict training/validation leakage blocking.
- Benchmark quality scoring beyond displaying existing warnings and source distribution.
- Repository health score.
- Repository report, PDF, CSV, or Markdown export.
- Server-side pagination unless implementation discovers an existing low-cost pattern.
- Model promotion or user-facing Varroa Assessment.
- Replacing the current Training Crop editor.
- Full URL routing or polished global navigation.
- Creating Dataset Versions from repository filters or visible item selections.
- Changing existing Dataset Version creation selection rules.

## Acceptance Criteria

- [ ] Dataset Curator can open a separate **Bee Annotation Repository** page from the local training workflow using internal view switching.
- [ ] Browser shows active Dataset Item counts by Dataset Role across multiple Training Data Collection inspections in one Workspace.
- [ ] Browser lists Dataset Items from at least two different Inspections in the same repository view.
- [ ] Browser defaults to Workspace-wide active Dataset Items across all Hives, grouped by Dataset Role and newest assignment first inside each role.
- [ ] Browser can filter by Dataset Role, Hive, Inspection, Inspection Intent, Source Image, Dataset Version membership, new-since-latest-version, review provenance, image quality, and bee-class presence where data is available.
- [ ] Browser includes simple text search without adding pagination in this slice.
- [ ] Browser shows each Dataset Item's Source Image / Inspection Photo, Inspection, Hive, Hive Configuration snapshot summary, Training Crop, reviewed bee counts, source group key, assignment note, and assigned timestamp where available.
- [ ] Browser shows complete visible bee and partial visible bee counts separately.
- [ ] Browser shows annotation source and review method distributions at summary and item level.
- [ ] Browser shows model-assisted provenance at summary and item level when present.
- [ ] Browser shows latest Dataset Version summary and whether each Dataset Item is included, protected, excluded, new since latest version, or not yet versioned.
- [ ] Detail panel shows all available Dataset Version memberships for the selected item when available.
- [ ] Selecting a Dataset Item opens a detail view with larger crop preview and reviewed Oriented Bee Ellipse snapshots.
- [ ] List entries include small crop thumbnails; missing image bytes show an image-unavailable state rather than hiding the item.
- [ ] Browser shows non-blocking repository warnings for obvious concentration, leakage hints, missing benchmark, small validation, non-training Inspection Intent, and unavailable previews.
- [ ] Browser shows simple diversity chips and concrete warnings, not a repository health score.
- [ ] Benchmark Dataset Items are visible in the same browser and clearly marked as protected.
- [ ] Empty states distinguish no crops, completed-but-unassigned crops, and assigned Dataset Items.
- [ ] Browser shows unassigned completed crop count, with a link/list if cheap.
- [ ] Browser shows small persistence backend/database-purpose status.
- [ ] `Open crop in editor` is included only if it restores Apiary, Hive, Inspection, Inspection Photo, and Training Crop context automatically.
- [ ] Cross-Workspace access is blocked.
- [ ] Users without Dataset Curator capability cannot access the repository browser data.
- [ ] Source filenames may appear in the UI, but repository request logging does not log filenames unnecessarily.
- [ ] Existing Dataset Version creation and Training Run behaviour remains unchanged.
- [ ] Repository filters do not affect Dataset Version creation.
- [ ] Core API tests cover repository summary/list/detail and Dataset Version membership projection.
- [ ] Core API tests cover cross-Workspace isolation.
- [ ] Playwright acceptance covers opening the browser, filtering by role, and inspecting an item.
- [ ] Basic responsive checks prove the page stacks without overlap on narrow screens.
- [ ] Live Postgres verification proves repository items and Dataset Version membership survive restart.
- [ ] `docs/user-guide.md` gains a task-oriented entry for reviewing the Bee Annotation Repository.

## Open Questions

- Can `Open crop in editor` restore full context cleanly with current UI state, or should it be omitted until a smaller navigation slice?
- Can unassigned completed crop counts be computed cheaply through the existing read model, or should the first implementation show only assigned Dataset Items?
- Can Source Image context thumbnails be added cheaply, or should the first implementation show crop preview only?
- Can Training Run / Model Candidate consumption traces be projected cheaply, or should Dataset Version membership be the only required consumption evidence?
