# Vertical Slice 0015: YOLO OBB Training Baseline

Status: planned after Slice 0014 live Postgres closeout.

## Purpose

Create the first repeatable local training baseline for the HiveSight Bee Detector using active, reviewed Training Crop evidence exported as YOLO OBB labels.

This slice closes the loop between the Bee Annotation Repository and the first project-owned trainable bee-detection model. It deliberately does not train Varroa detection. Bee detection and Varroa detection remain separate logical model stages so the project can measure denominator quality and mite-detection quality independently.

The first goal is not a good model. The first goal is a reproducible training pipeline with honest governance evidence: what data was used, what was excluded, what was protected, what model family ran, what artifacts were produced, and what the early result can and cannot claim.

This slice also retires Grounding DINO from the active solution. Real-world trial evidence showed that it was not useful for brood-frame bee candidate annotation. HiveSight will proceed with a project-owned Bee Detector behind an adapter seam, using YOLO OBB as the first implementation rather than an irreversible model-family commitment.

## Source Inputs

- `CONTEXT.md`
- `requirements/model-requirements.md`
- `requirements/ai-assisted-annotation-and-model-training-baseline.md`
- `requirements/bee-annotation-repository-and-curriculum-training-baseline.md`
- `requirements/product-spec.md`
- `requirements/decision-log.md`
- `architecture/adr/0002-oriented-ellipse-canonical-bee-annotations.md`
- `architecture/adr/0003-postgres-for-durable-product-and-model-governance-metadata.md`
- `architecture/adr/0004-keep-analysis-service-separate-and-integrate-through-async-workflow.md`
- `architecture/domain-model.md`
- `architecture/postgres-persistence-design.md`
- `architecture/vertical-slice-0011-physical-dataset-export-package.md`
- `architecture/vertical-slice-0014-postgres-backed-bee-annotation-repository-persistence.md`
- External review feedback on two-stage bee/Varroa modelling, automation bias, benchmark realism, and mite-training dependency risk.
- Human review of Grounding DINO output on real brood-frame photos.

## User Path

Given a Dataset Curator has reviewed Training Crops with oriented bee ellipses
And those Dataset Items are assigned to training, validation, benchmark, or excluded roles
When the Dataset Curator creates a Dataset Version and starts a YOLO OBB Bee Detector baseline Training Run
Then HiveSight creates a traceable Dataset Version, Training Run, Model Candidate, export package, preview artifacts, and baseline report
And benchmark Dataset Items are protected from training input
And the report states governance warnings rather than claiming production suitability.

## Preconditions

- Slice 0014 is closed and live Postgres restart verification has passed.
- Docker/Postgres is available before the slice can be fully acceptance-closed.
- Dataset Version, Training Run, Model Candidate, and artifact metadata use the Postgres-backed Core API path.
- A Dataset Curator has internal dataset/model governance capability.
- Workspace Data Use Agreement is accepted for included Dataset Items.
- Active reviewed Dataset Items exist for at least training and validation roles.
- Benchmark Dataset Items, if present, have `source_group_key` and remain protected.
- Reviewed bee geometry uses canonical Oriented Bee Ellipses; YOLO OBB labels are a model-specific projection.
- Ellipse rotation is an undirected bee body-axis alignment, not a head-to-tail direction. Export and training logic must not infer anatomical head direction from the stored rotation.
- Normal application setup and fast tests do not require YOLO or network access.

## End-To-End Behaviour

The Dataset Curator starts from the current Bee Annotation Repository state. HiveSight creates an explicit, durable Dataset Version from active, reviewed Dataset Items in one Workspace.

The Dataset Version freezes the important facts at creation time:

- included Dataset Item ids
- excluded Dataset Item ids and reasons
- Dataset Role distribution
- source evidence type
- Source Image id and Training Crop id
- Hive Configuration and source group traceability
- Curriculum Stage distribution
- image quality and permission/provenance snapshots
- annotation class counts
- annotation source and review method counts
- reviewed ellipse geometry snapshots
- selection criteria and manifest/content hash
- export format version, initially `yolo_obb_v1`

Only active, reviewed Training Crop Dataset Items are eligible for the YOLO OBB trainer-facing export. Withdrawn, superseded, draft, rejected, unreviewed, full-frame, unsupported, missing-image, invalid-geometry, or otherwise ineligible items are recorded as excluded metadata and never exported into trainer-facing folders.

Training and validation Dataset Items become YOLO OBB input. Benchmark Dataset Items are recorded as protected metadata and may have protected preview artifacts, but are not included in `data.yaml` or trainer-facing train/validation folders. Excluded Dataset Items remain metadata only.

The export package is freshly generated from the selected Dataset Version for each Training Run. It copies image inputs into a self-contained package under the run artifact folder, generates YOLO OBB labels normalized to the Training Crop image dimensions, writes `data.yaml`, and includes HiveSight metadata sidecars such as manifests and source maps. The original reviewed ellipse remains canonical; the YOLO OBB label records `conversion_version=ellipse_to_yolo_obb_v1`.

The Dataset Curator starts a local asynchronous Training Run from a selected Dataset Version. The run uses a `BeeDetectorTrainingAdapter` seam inside Core API:

- default fast tests use a deterministic fake adapter
- the explicit real path uses a pinned Ultralytics YOLO OBB base model, initially `yolo11n-obb.pt`
- real YOLO training is opt-in through setup and training commands

After the run completes, HiveSight records:

- Dataset Version
- Training Run
- Model Candidate
- model artifact manifest
- artifact references and hashes where practical
- training settings
- data counts and split counts
- source, hive configuration, review method, and curriculum distributions
- warning codes and severities
- basic validation metrics if the model runner produced them
- Markdown and structured JSON reports

The resulting Model Candidate has `model_purpose=bee_detector`, `promotion_status=not_evaluated`, and is not user-facing. It cannot be used for Varroa assessment, inspection analysis, or candidate annotation generation in this slice.

## Governance Decisions Embedded In The Slice

### Two-Stage Model Pipeline

Slice 0015 trains only the HiveSight Bee Detector.

Bee detection and Varroa detection remain separate logical model stages because they have different image scales, labels, review ergonomics, and failure modes. Bee detection works at frame/crop level with oriented bee geometry. Varroa detection will later work at mite/per-bee scale with tighter mite labels and bee association evidence.

The baseline report and UI must say that the run trains only bee localisation. It must not be presented as a Varroa assessment, infestation result, product diagnosis, or approved analysis model.

### Candidate Annotations And Human Review

The active domain language is Candidate Annotation, not "AI guess" or unqualified "pre-label".

A Candidate Annotation is untrusted proposed evidence awaiting review. It may come from a model candidate, imported public dataset, previous draft, or future helper. Only reviewed annotation evidence can enter a Dataset Version.

Candidate annotation source vocabulary should support:

- `human_from_scratch`
- `model_candidate`
- `imported_public_dataset`
- `unknown_legacy`

Review method vocabulary should support:

- `human_from_scratch`
- `human_reviewed_candidate`
- `imported_reviewed`

Slice 0015 must prevent unreviewed Candidate Annotations from entering Dataset Versions. Candidate-only items are excluded with reason `annotation_not_reviewed`.

### Automation Bias

Human-reviewed annotations remain the trust boundary, but human review of candidate annotations is not assumed to remove automation bias.

The report must separate review method and annotation source counts. It must warn when all reviewed annotations came from candidate-assisted review and there are no human-from-scratch examples. The warning is not a hard block in Slice 0015.

Blind-review comparison remains a future workflow: a reviewer annotates a small sample without seeing candidate annotations, and the result is compared against the candidate-assisted-then-reviewed path. The need for that workflow is recorded in requirements, but Slice 0015 only needs to expose the gap.

### Benchmark Protection And Realism

Benchmark Dataset Items must not enter training, validation, routine threshold tuning, prompt tuning, pre-labelling optimisation, or `data.yaml`.

The baseline report must show benchmark Dataset Item counts by:

- Dataset Role
- Curriculum Stage
- image quality status
- source group key
- Hive Configuration

If the benchmark set is empty, contains only easy sparse `small_crop` examples, lacks dense/occluded/poor-light examples, or shares a Source Image with training/validation data, the report must warn that benchmark evidence is not representative enough for serious model-quality claims.

### Dataset Leakage

Slice 0015 warns rather than blocks on obvious training/validation leakage, such as shared Source Image ids or source group keys across roles. Benchmark leakage is a high-severity warning.

Stricter leakage prevention remains a future dataset-quality gate.

### Varroa Training Dependency Risk

This slice does not train the Varroa Detector, but it must record the future risk:

If mite-training crops are created only from bees found by the Bee Detector, the Varroa Detector may inherit the Bee Detector's blind spots. Future Varroa training and benchmark slices should include independently sampled human-drawn bee crops, especially for shadowed, occluded, dense, or otherwise difficult bees.

This risk is ADR-worthy before the first Varroa Detector training slice, before creating a mite benchmark Dataset Version, or before using Bee Detector output as the sole source of mite-training crops.

### Grounding DINO Retirement

Grounding DINO is removed from the active solution. Active setup commands, adapter registration, tests, and docs should no longer describe it as a supported local pre-labelling path.

Historical Slice 0007 documentation may remain as a record of what was tried, but active architecture and setup docs should point to Candidate Annotations and the HiveSight-owned Bee Detector direction.

An ADR should record:

- Grounding DINO was tried as a local pre-labelling adapter.
- It performed poorly for brood-frame bee candidate annotation.
- HiveSight is retiring it from active code and dependencies.
- The replacement direction is a HiveSight-owned Bee Detector behind an adapter seam.
- YOLO OBB is the first implementation candidate, not an irreversible commitment.

## Local Database Purpose Separation

Slice 0015 introduces or documents purpose-specific local databases:

- `hive_sight_core_dev`: manual development and curator UI experiments.
- `hive_sight_core_test`: automated tests that may reset freely.
- `hive_sight_core_qa`: slower real-adapter QA checks and model-training smoke runs.

One Postgres server/container may host all three databases.

Rules:

- Normal automated fake-adapter tests use the test database and may reset it.
- `pnpm db:reset` should target only the test database by default.
- Dev and QA reset commands, if added, must be explicit and visibly destructive.
- `pnpm db:migrate` targets dev by default, with explicit test/QA/all variants.
- Dev startup may migrate the dev database automatically.
- YOLO training commands may migrate their target database automatically.
- QA commands may migrate but must not reset the QA database automatically.
- Real YOLO training is refused against the test database unless an explicit override is added later.
- Fake adapter training is allowed against dev, QA, and test databases, but fake Model Candidates are clearly labelled and ineligible for promotion.
- Health/readiness responses and reports include persistence backend and database purpose without exposing credentials.

## Layers Touched

- Web UI: Add a small Dataset Curator model-training/governance view to create Dataset Versions, inspect warnings/previews, start a Training Run, poll status, and open reports/artifacts. Show adapter type and database purpose. Keep fake Model Candidates visibly fake.
- Core API: Add `/v1/model-training/...` endpoints for readiness, Dataset Versions, Training Runs, Model Candidates, and artifacts. Enforce Dataset Curator capability, high-severity-warning acknowledgement, active-run lock, test-database real-adapter restriction, and artifact-serving safety.
- Analysis Service: Not touched. The first training adapter lives inside Core API behind `BeeDetectorTrainingAdapter`; it may move later if training becomes heavier.
- Storage: Persist metadata in Postgres. Store export packages, copied images, label files, preview images, logs, trained weights, Markdown reports, JSON reports, and artifact manifests under a configurable local artifact root, defaulting to repo-level `var/model-runs`.
- Queue or async boundary: Training is asynchronous with an in-process local background runner. One queued/running Training Run is allowed at a time.
- Contracts: Add Core API request/response shapes for readiness, Dataset Version create/list/detail, Training Run start/list/detail, Model Candidate list/detail, report summary, and artifact records.
- Observability: Emit structured logs for Dataset Version creation and Training Run completion/failure with ids, counts, adapter type, status, warning count, artifact ids, and failure details.
- Developer tooling: Add memorable commands for YOLO setup/training and QA verification; update README after implementation so commands are truthful.

## Test Seams

- Seam: Dataset Version workflow
- Behaviour verified: only active reviewed Training Crop Dataset Items are frozen into a Dataset Version; benchmark and excluded items remain protected metadata; ineligible items are excluded with stable reasons.
- Test style: Core API workflow tests and API-level BDD.

- Seam: YOLO OBB export package
- Behaviour verified: copied crop images, `data.yaml`, labels, sidecar metadata, hashes, preview artifacts, class order, and ellipse-to-OBB conversion are generated from a Dataset Version; benchmark files are not included in trainer-facing paths.
- Test style: unit/API tests using deterministic fixture images.

- Seam: model-training adapter
- Behaviour verified: fake adapter records deterministic artifacts, fake weights, settings, metrics, status transitions, and failures without requiring YOLO in fast tests; real adapter remains opt-in and records dependency/base-weight evidence.
- Test style: dependency-injected fake adapter tests plus explicit real-adapter QA lane.

- Seam: Postgres persistence and local database purpose
- Behaviour verified: Dataset Version, Training Run, Model Candidate, report, and artifact metadata survive restart; automated tests use/reset only test database; real YOLO training refuses test database by default.
- Test style: opt-in live Postgres integration tests using Docker.

- Seam: artifact serving
- Behaviour verified: known artifact records can be opened/downloaded by opaque id; raw paths and traversal attempts fail.
- Test style: API tests.

- Seam: Web UI
- Behaviour verified: Dataset Curator can create/inspect a Dataset Version, acknowledge high-severity warnings, start a fake baseline run, see status/report caveats, and view preview artifacts; ordinary Beekeeper cannot access model-training actions.
- Test style: Playwright acceptance test.

## Data Shape

### Dataset Version

Minimum fields:

- `dataset_version_id`
- `workspace_id`
- `human_readable_id`: `HS-DV-000001`
- `purpose`: `bee_detector_training_baseline`
- `model_purpose`: `bee_detector`
- `status`: `active`, `obsolete`
- `export_format`: `yolo_obb_v1`
- `selection_criteria`
- `manifest_hash`
- `dataset_item_snapshot`
- `included_dataset_item_ids`
- `training_dataset_item_ids`
- `validation_dataset_item_ids`
- `protected_benchmark_dataset_item_ids`
- `excluded_dataset_items`: id plus reason/code
- `source_group_distribution`
- `hive_configuration_distribution`
- `curriculum_stage_distribution`
- `image_quality_distribution`
- `annotation_class_counts`
- `annotation_source_counts`
- `review_method_counts`
- `warnings`
- `preview_artifact_ids`
- `report_artifact_id`
- `created_by_user_id`
- `created_at`

### Training Run

Minimum fields:

- `training_run_id`
- `workspace_id`
- `human_readable_id`: `HS-TR-000001`
- `dataset_version_id`
- `model_purpose`: `bee_detector`
- `model_family`: `yolo_obb`
- `model_size`: `nano` or `small`
- `base_weights`: initially `yolo11n-obb.pt`
- `base_weights_source`: `local_cache`, `downloaded`, or `configured_path`
- `status`: `queued`, `running`, `completed`, `failed`, `cancelled`
- `phase`: `queued`, `exporting`, `training`, `recording_artifacts`, `completed`, `failed`
- `adapter_type`: `fake` or `ultralytics_yolo_obb`
- `database_purpose`: `dev`, `test`, or `qa`
- `training_settings`
- `random_seed`
- `dataset_export_id`
- `artifact_root`
- `artifact_manifest_id`
- `git_commit_sha`
- `git_dirty_status`: `clean`, `dirty`, or `unknown`
- `environment_summary`
- `warning_acknowledgement`
- `started_at`
- `completed_at`
- `failure_code`
- `failure_message`
- `artifact_ids`
- `metrics_summary`
- `created_by_user_id`
- optional `purpose_notes`
- optional `retry_of_training_run_id`

### Model Candidate

Minimum fields:

- `model_candidate_id`
- `workspace_id`
- `human_readable_id`: `HS-MC-000001`
- `display_name`
- `training_run_id`
- `model_purpose`: `bee_detector`
- `model_family`: `yolo_obb`
- `adapter_type`: `fake` or `ultralytics_yolo_obb`
- `artifact_id`
- `status`: `created`, `failed`, `withdrawn`
- `created_at`
- `promotion_status`: `not_evaluated`
- `not_user_facing_reason`: `baseline_training_only`

### Artifact Record

Minimum fields:

- `artifact_id`
- `owner_type`: `dataset_version` or `training_run`
- `owner_id`
- `artifact_type`
- `relative_path`
- `content_type`
- `size_bytes`
- `sha256`
- `required_or_diagnostic`
- `created_at`
- `availability_status`

### Baseline Report

Minimum sections:

- database purpose and persistence backend
- adapter type and real-adapter availability
- Dataset Version id, status, manifest hash, and selection criteria
- data volume by Dataset Role
- data volume by Curriculum Stage
- class distribution using fixed class order: `0 complete_visible_bee`, `1 partial_visible_bee`
- annotation source counts
- review method counts
- source group and Hive Configuration distributions
- included/excluded counts and exclusion reasons
- benchmark protection statement
- benchmark realism and leakage warnings
- automation-bias warning or evidence summary
- training settings, random seed, model size, base weights, device, and environment summary
- artifact manifest with sizes/hashes where practical
- validation metrics if available, labelled as smoke-run metrics when data is tiny
- explicit caveat: not production suitable, not a Varroa Detector, not a user-facing Model Version

### Warning Codes

Stable warning codes should include:

- `NO_BENCHMARK_ITEMS`
- `SMALL_TRAINING_SET`
- `SMALL_VALIDATION_SET`
- `CLASS_MISSING`
- `AUTOMATION_BIAS_RISK`
- `SOURCE_GROUP_IMBALANCE`
- `BENCHMARK_SOURCE_LEAKAGE`
- `FULL_FRAME_EXPORT_UNSUPPORTED`
- `REAL_ADAPTER_UNAVAILABLE`
- `IMAGE_METADATA_MISMATCH`
- `INVALID_LABEL_GEOMETRY`

Warning severities are `info`, `warning`, and `high`.

Suggested adequacy warning defaults:

- fewer than 20 training items: smoke-run warning
- fewer than 5 validation items: validation adequacy warning
- 0 benchmark items: no protected benchmark warning
- any class with 0 examples: class coverage warning

## Commands To Add During Implementation

- `pnpm model:setup:yolo`: install/check pinned optional YOLO dependencies in `services/core-api/.venv` and verify the pinned base weights are cached or resolvable.
- `pnpm model:train:bee:yolo`: migrate/check the dev database, verify readiness, and start a real local YOLO OBB Bee Detector training attempt against dev data.
- `pnpm dev:all:yolo-training`: start the app stack with the real YOLO training adapter enabled.
- `pnpm model:qa:bee:yolo`: run the explicit QA real-adapter lane against `hive_sight_core_qa` without resetting it.

Normal verification must continue to run without YOLO installed. The real-adapter QA lane may be documented as not run at closeout if dependencies or reviewed data are unavailable, but that gap must be explicit.

## Out Of Scope

- Varroa Detector training.
- Mite annotation tooling.
- Per-bee mite crop generation.
- Bee-to-mite association modelling.
- Protected Benchmark Evaluation for model promotion.
- Automatic model promotion.
- Approved user-facing Model Version creation.
- Production model serving or inference adoption.
- Selecting the trained Bee Detector as a candidate-annotation generator.
- Public USDA/XML annotation import; planned as Slice 0015.1.
- Full-frame or tiled YOLO export; parked for a later model-data slice.
- Cloud/GPU training infrastructure.
- Durable external queue orchestration.
- Production auth, object storage provider, queue provider, or deployment decisions.
- Full blind-review UI/workflow.
- Serious model-quality claims.
- Automated artifact retention or cleanup.
- UI-level Gherkin; API-level BDD and Playwright remain the acceptance paths for this slice.

## Acceptance Criteria

- [ ] Grounding DINO is removed from active adapter registration, setup/run commands, active docs, and Grounding DINO-only dependencies.
- [ ] An ADR records the Grounding DINO retirement and replacement direction.
- [ ] A Dataset Curator can create an explicit Dataset Version from active reviewed Dataset Items in a Workspace.
- [ ] Dataset Version creation requires at least one training and one validation Dataset Item.
- [ ] Dataset Version creation stores a frozen snapshot, selection criteria, manifest hash, export format version, included items, protected benchmark metadata, excluded metadata, warnings, report artifact, and preview artifacts.
- [ ] Dataset Version creation includes only active reviewed Training Crop evidence and excludes unsupported/unreviewed/withdrawn/superseded/missing/invalid items with stable reason codes.
- [ ] Benchmark Dataset Items are included only as protected metadata and are excluded from training/validation export input and `data.yaml`.
- [ ] YOLO OBB export uses fixed class order: `0 complete_visible_bee`, `1 partial_visible_bee`.
- [ ] YOLO OBB labels are normalized against copied Training Crop image dimensions.
- [ ] Original reviewed ellipse geometry is preserved in HiveSight metadata sidecars while model-specific OBB labels record `conversion_version=ellipse_to_yolo_obb_v1`.
- [ ] Export packages include copied images, labels, `data.yaml`, metadata sidecars, hashes, and visual preview artifacts.
- [ ] Dataset Version detail/report shows included/excluded counts, warning codes/severities, role/class/source/hive/curriculum distributions, and preview artifacts.
- [ ] A Dataset Curator can start an asynchronous YOLO OBB Bee Detector Training Run from a selected Dataset Version.
- [ ] Training Run start returns `202 Accepted` with a Training Run id and enforces one active run at a time.
- [ ] High-severity Dataset Version warnings require explicit acknowledgement at the Core API before Training Run start.
- [ ] Fast tests use a fake `BeeDetectorTrainingAdapter` that consumes the physical YOLO OBB package shape and writes deterministic fake weights, metrics, logs, reports, and artifact manifests.
- [ ] The real adapter seam can run pinned Ultralytics YOLO OBB locally when `pnpm model:setup:yolo` has prepared optional dependencies and enough data exists.
- [ ] Real adapter completion requires usable trained weights; missing weights fail the Training Run and do not create a Model Candidate.
- [ ] Training Run records model purpose, model family, adapter type, database purpose, settings, base weights/source, device, random seed, dataset version, export package, status, phase, timing, git state, environment summary, artifacts, metrics, logs, report, and failure details.
- [ ] A completed Training Run creates a Model Candidate with `model_purpose=bee_detector`, `promotion_status=not_evaluated`, and `not_user_facing_reason=baseline_training_only`.
- [ ] Failed Training Runs do not create Model Candidates.
- [ ] Model Candidate records are separate from approved user-facing Model Versions and cannot be used for inspection analysis or candidate annotation generation in this slice.
- [ ] UI/API labels use Candidate Annotation language on active surfaces rather than "AI guess" or unqualified "pre-label".
- [ ] Core API enforces Dataset Curator/internal capability access for Dataset Version creation and Training Run start.
- [ ] API-level BDD covers curator authorization, ordinary-user rejection, Dataset Version inclusion/exclusion governance, benchmark protection, high-severity warning acknowledgement, and Model Candidate creation.
- [ ] Playwright acceptance covers the Dataset Curator-visible baseline workflow and report caveats using the fake adapter.
- [ ] Artifact-serving endpoints expose only known artifact records by opaque id and reject raw paths/traversal attempts.
- [ ] Local database purpose separation is implemented or, if too broad, split into a prior `Slice 0014.6: Local Database Purpose Separation` before Slice 0015 can close.
- [ ] Automated tests do not touch dev or QA databases; destructive reset defaults to the test database only.
- [ ] Readiness/health surfaces expose adapter type, persistence backend, database purpose, active-run lock status, eligible counts, and headline warnings without leaking credentials.
- [ ] `var/model-runs` or the configured artifact root is gitignored.
- [ ] `pnpm verify:slice` includes fake-adapter model-training checks and generated verification report coverage.
- [ ] Live Postgres verification passes for Dataset Version, Training Run, Model Candidate, report, and artifact metadata restart survival.
- [ ] Real YOLO QA lane command exists and is either run successfully or explicitly recorded as not run with dependencies/data reason.

## Planning Decisions Resolved

- Dataset Version is a durable first-class record, not only an export manifest.
- Dataset Version and Training Run are separate so the same frozen dataset can be retrained with different settings.
- Dataset Versions become immutable once referenced by a Training Run; changed selections create a new Dataset Version.
- Training Runs and Model Candidates are not deleted in this slice.
- Completed/failed/cancelled Training Runs are immutable except for derived artifact availability.
- Real YOLO dependencies are optional and pinned; normal app startup/tests do not require them.
- The first real base weights are pinned, not "latest".
- CPU is the default real-adapter device; selected device is recorded.
- Model size selector supports nano/small, default nano.
- Training settings are limited to model size, epochs, image size, batch size, random seed, and optional notes.
- Dataset Version creation is synchronous; Training Run execution is asynchronous with UI polling.
- Training progress is coarse-grained; raw logs are artifacts rather than live UI noise.
- Dataset Versions and Model Candidates have human-readable ids. Model Candidates also have curator-facing display names.
- Reports store structured JSON and Markdown artifacts.
- Artifact metadata uses relative paths from a configurable artifact root.
- Artifact reports avoid raw personal/location metadata such as EXIF GPS, local source paths, device identifiers, or personal notes.
- Public dataset annotation import is planned as Slice 0015.1.
- Full-frame/tiling export is parked for a later model-data slice.

## Open Questions

- If local database purpose separation expands beyond commands/settings/docs/safety checks, should it be split into `Slice 0014.6` before implementation starts?
- How much existing Grounding DINO code can be removed cleanly inside Slice 0015 before it becomes a separate cleanup slice?
- What exact pinned Ultralytics version should `pnpm model:setup:yolo` install?
- Should `model:qa:bee:yolo` be implemented in Slice 0015 as an automated smoke command only, or as a small guided manual QA script plus command?
