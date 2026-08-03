# Vertical Slice 0015.4: Model Candidate Evaluation And Benchmark Report

Status: planned.

## Purpose

Let a Dataset Curator evaluate one Bee Localisation Model Candidate, currently implemented by the HiveSight Bee Detector, against protected benchmark Dataset Items and produce an honest benchmark report.

This slice answers: "How did this candidate perform against evidence it was not allowed to train on?" It does not promote the model, approve it for user-facing Varroa assessment, or claim production quality. It creates the first repeatable evaluation path and makes weaknesses visible.

## Source Inputs

- `CONTEXT.md`
- `requirements/model-requirements.md`, especially MR-018, MR-018A, MR-027, MR-029, MR-029B, MR-030, MR-031, and MR-032.
- `requirements/ai-assisted-annotation-and-model-training-baseline.md`, especially AIA-012, AIA-016, AIA-017, AIA-018, AIA-019, and AIA-021.
- `requirements/bee-annotation-repository-and-curriculum-training-baseline.md`
- `architecture/domain-model.md`: Dataset Version, Training Run, Model Candidate, Benchmark Evaluation, Model Version.
- `architecture/adr/0002-oriented-ellipse-canonical-bee-annotations.md`
- `architecture/adr/0003-postgres-for-durable-product-and-model-governance-metadata.md`
- `architecture/adr/0006-directed-bee-ellipse-orientation.md`
- `architecture/adr/0007-three-stage-bee-localisation-orientation-and-varroa-pipeline.md`
- `architecture/adr/0008-contribution-withdrawal-quarantine-and-retrain.md`
- `architecture/adr/0009-source-rights-invalidation-quarantine-and-retrain.md`
- `architecture/vertical-slice-0015-yolo-obb-training-baseline.md`
- `architecture/vertical-slice-0015.1-training-run-progress-and-recovery.md`
- `architecture/vertical-slice-0015.2-model-candidate-crop-pre-labelling.md`
- `architecture/vertical-slice-0015.3-dataset-repository-browser.md`
- `architecture/parking-lot.md`, especially PARK-0011, PARK-0014, PARK-0025, PARK-0028, PARK-0035, PARK-0036, and PARK-0037.

## User Path

Given a Dataset Curator has a completed Bee Localisation Model Candidate
And the Workspace has protected benchmark Dataset Items with reviewed directed Oriented Bee Ellipses
When the Dataset Curator runs a benchmark evaluation for that Model Candidate
Then HiveSight runs the candidate against the protected benchmark crop images
And compares predicted bee detections with reviewed benchmark ellipses
And records a Benchmark Evaluation with metrics, warnings, artifacts, and caveats
And shows a benchmark report without promoting the Model Candidate.

## Preconditions

- Slice 0015 can create Dataset Versions, Training Runs, Model Candidates, and model artifacts.
- Slice 0015.1 exposes Training Run progress/recovery enough to avoid confusing evaluation with in-flight training.
- Slice 0015.2 can run a Model Candidate against one Training Crop through the inference adapter seam.
- Slice 0015.3 exposes Dataset Repository counts and benchmark Dataset Items.
- Slice 0015.35 defines `rotation_degrees` as directed bee head orientation; evaluation treats YOLO OBB geometry as body localisation and does not score head-direction prediction in this slice.
- The active user has Dataset Curator capability.
- Workspace Data Use Agreement is accepted.
- At least one completed Bee Localisation Model Candidate exists.
- At least one benchmark Dataset Item exists, or the UI/API returns a clear no-benchmark result.
- Benchmark Dataset Items remain protected from training and routine threshold tuning.
- The Model Candidate, its Training Run, and its training Dataset Version are not quarantined by Contribution Withdrawal or Source Rights Invalidation.
- Benchmark Dataset Items have active eligible Source Rights Records and any applicable Contributor Contribution Permissions for the `evaluation` scope.
- Real adapter evaluation is an explicit local/QA action; fast tests use a deterministic fake adapter.
- No Training Run or Benchmark Evaluation is already queued/running in the local model-job runner.

## End-To-End Behaviour

The Dataset Curator opens the model-training/governance area. For a completed Bee Localisation Model Candidate, HiveSight shows a **Run benchmark evaluation** action.

This slice uses the protected benchmark Dataset Items already frozen inside the candidate's Training Run Dataset Version as the first benchmark selection snapshot. It does not introduce a new benchmark-only Dataset Version creation workflow. The report must make this explicit so future readers understand that the benchmark selection is frozen but not yet managed through a separate benchmark-version UI.

Before the run starts, HiveSight checks benchmark readiness:

- benchmark Dataset Item count
- benchmark Source Image and source group diversity
- whether any benchmark item shares a Source Image or source group with the candidate's training or validation Dataset Items
- whether benchmark items are all easy sparse crops
- whether the benchmark selection plan and frozen selection snapshot predate the evaluated Model Candidate run
- whether benchmark image bytes are available
- whether reviewed ellipse geometry is valid
- annotation source and review method distribution, including model-assisted review counts
- Source Rights Record status, required attribution, and evaluation-scope compatibility
- Contributor Contribution Permission status and withdrawal/deletion impact
- whether the Model Candidate, Training Run, training Dataset Version, or benchmark evidence is quarantined
- persistence backend and database purpose

If there are no benchmark Dataset Items, HiveSight blocks the run with a useful message. HiveSight also blocks evaluation when required evidence is withdrawn, rights-invalidated, missing an active `evaluation` Permitted Use Scope, or when the candidate or supporting Dataset Version is quarantined. If there are benchmark quality warnings, HiveSight allows the run but records the warnings in the report. Benchmark leakage warnings are high severity and require acknowledgement before the run starts.

When the curator starts the evaluation, Core API creates a durable Benchmark Evaluation record and runs the candidate against protected benchmark crop images through a `BeeLocalisationEvaluationAdapter` or equivalent inference/evaluation seam.

The first evaluation settings are fixed per run and recorded in the Benchmark Evaluation:

- confidence threshold: `0.10`
- matching rule: `ellipse_match_v1`, unless a small local rotated-IoU helper already exists at implementation time
- adapter: deterministic fake adapter in fast tests, real YOLO OBB inference adapter only in the explicit local/QA path
- maximum runtime handling: asynchronous status, heartbeat, failure message, and report artifact, following the Training Run progress pattern

The first warning thresholds are deterministic but provisional:

- `SMALL_BENCHMARK_SET`: fewer than 20 benchmark Dataset Items
- `BENCHMARK_EASY_ONLY`: every benchmark item has curriculum stage `small_crop`
- `NO_HUMAN_FROM_SCRATCH_BENCHMARK_ITEMS`: no benchmark annotations use human-from-scratch review provenance
- `BENCHMARK_SOURCE_IMAGE_LEAKAGE`: high severity
- `BENCHMARK_SOURCE_GROUP_LEAKAGE`: high severity

Small, easy, or model-assisted benchmark evidence warns but does not block. Source-image and source-group leakage block until the Dataset Curator acknowledges the high-severity warning.

For each benchmark Dataset Item:

- load the crop image through the existing image access path
- load reviewed ellipse snapshots as ground truth
- run the Model Candidate against the crop
- convert raw model detections into HiveSight candidate geometry
- match predictions to reviewed ellipses using a simple documented matching rule
- record per-item counts and match outcomes

Benchmark Evaluation supports only Training Crop Dataset Items in this slice. Full-frame Bee Localisation evaluation is parked separately because it answers a different question from crop-level benchmark smoke testing.

Readiness blocks the run when any benchmark item is missing image bytes, has invalid or missing reviewed ellipse geometry, or includes an unsupported annotation type. Excluded Dataset Items may be counted in readiness/report context but are never evaluated.

The first matching rule should be simple and replaceable:

- start with center-distance plus radius/area overlap approximation, clearly named `ellipse_match_v1`
- park precise rotated-box IoU unless a low-risk helper is already present and tested
- use one prediction per reviewed bee and one reviewed bee per prediction
- count unmatched predictions as false positives
- count unmatched reviewed ellipses as false negatives
- count matched reviewed `complete_visible_bee` and `partial_visible_bee` separately

The evaluator uses one-to-one matching only: one prediction may match at most one reviewed bee, and one reviewed bee may match at most one prediction.

The benchmark report includes:

- Model Candidate id and human-readable id
- Training Run id and Dataset Version id that produced the candidate
- Benchmark Evaluation id and human-readable id
- protected benchmark Dataset Item ids
- benchmark Dataset Version or benchmark selection snapshot
- predeclared benchmark sampling plan and frozen-at timestamp
- adapter type and model artifact used
- evaluation settings, including confidence threshold and matching rule
- complete visible bee precision and recall
- partial visible bee precision and recall, if there is enough evidence
- total reviewed complete and partial bees
- predicted complete and partial counts
- false positive and false negative counts
- per-item summary rows
- crop-level caveat when the benchmark contains only Training Crop Dataset Items
- metrics by image quality, source group, Hive Configuration, and curriculum stage where available
- annotation source and review method distributions
- Source Rights Record and Contributor Contribution Permission compatibility summary
- required attribution summary for benchmark evidence and any report artifact
- quarantine/withdrawal/source-rights-impact summary
- benchmark leakage and representativeness warnings
- explicit caveat that this is Bee Localisation only
- explicit caveat that head-direction prediction is not evaluated
- explicit caveat that Varroa detection is not evaluated
- plain-English caveat when fewer than 20 benchmark items are present, stating the metrics are workflow evidence only and not a reliable model-quality claim
- raw predictions in the JSON artifact, including both model-native output and normalized HiveSight geometry

The Markdown report remains human-readable and does not dump every raw prediction by default. The JSON artifact preserves raw model-native values, normalized geometry, match outcomes, per-item metrics, and settings for debugging and future metric recalculation. Raw predictions are derived artifacts, not canonical reviewed evidence.

After completion, the UI shows the latest completed Benchmark Evaluation for each Model Candidate and lets the curator explicitly open the Markdown report or download the JSON artifact. Failed, cancelled, queued, and running evaluations remain visible in a recent run history but do not replace the latest completed summary. Every row shows adapter type, and the on-screen caveat states: "Bee Localisation only. Does not evaluate head direction, Varroa detection, or user-facing readiness."

The UI should also show a short proof-of-life state while the run is active: queued/running/completed/failed/cancelled, last heartbeat, elapsed time, benchmark item count, and current activity message.

The Dataset Curator can cancel a queued or running Benchmark Evaluation after a lightweight confirmation. Cancellation is cooperative: the worker checks cancellation state between benchmark items, records `cancelled`, cancel reason, and logs, and does not publish partial metrics as benchmark evidence. Completed or failed evaluations cannot be cancelled. Normal UI deletion of Benchmark Evaluation records is out of scope; terminal records remain in history.

The Model Candidate moves only to a non-user-facing evaluation status such as `benchmark_reported` after completed evaluation. Fake-adapter evaluations may update this status, but the fake label must be unavoidable in UI and reports. This slice must not create a user-facing Model Version or promotion approval workflow.

Fake-adapter Benchmark Evaluations are allowed in fast automated tests and local development only when they are visibly labelled as fake. They must not be confused with real YOLO QA evidence.

Evaluation must not create Candidate Annotations or alter Training Crop annotation state. It observes and scores predictions only. Turning predictions into reviewable Candidate Annotations remains the Slice 0015.2 pre-labelling workflow.

## Layers Touched

- Web UI: Add benchmark readiness, **Run benchmark evaluation**, evaluation status, latest completed benchmark summary, recent evaluation history, warning display, cancel action, explicit Markdown/JSON report actions, and report artifact links near the existing model-training/governance area. Hide evaluation controls for ordinary beekeeper/workspace-owner UI. Keep it visibly separate from Training Runs.
- Core API: Add first-class benchmark evaluation readiness, start/list/detail/report/cancel endpoints. Enforce Dataset Curator capability, Workspace access, data-use agreement, Model Candidate eligibility, benchmark protection, `evaluation` Permitted Use Scope compatibility, quarantine status, no threshold tuning against benchmark, and local active model-job lock.
- Analysis Service: Not touched unless implementation proves the existing model-runtime adapter must move there. For this slice, evaluation can remain in Core API behind an adapter seam, matching the current local model-training and pre-labelling implementation.
- Storage: Persist Benchmark Evaluation metadata and report artifacts. Existing Postgres-backed repository record storage can be used initially; add projection tables only if the current pattern requires them for restart-safe listing.
- Queue or async boundary: Use asynchronous local background execution, matching Training Run behaviour. A fake adapter may complete immediately in tests. Slice 0015.4 has a local one-model-job-at-a-time constraint: a queued/running Benchmark Evaluation blocks another Benchmark Evaluation and blocks Training Run start; a queued/running Training Run blocks Benchmark Evaluation start. This is a local resource-safety constraint, not a permanent product rule.
- Contracts: Add request/response shapes for benchmark readiness, Benchmark Evaluation start/list/detail, per-item metric summaries, warning records, and artifact references.
- Observability: Log evaluation start/completion/failure with workspace id, model candidate id, benchmark item count, adapter type, matching rule, metrics summary, warning count, artifact ids, and failure code. Do not log filenames or sensitive image metadata unnecessarily.
- Developer tooling: Add `pnpm dev:all:yolo` as a clearer alias for the existing real YOLO model-work stack while keeping `pnpm dev:all:yolo-training`; add `pnpm dev:lan:yolo` while keeping `pnpm dev:lan:yolo-training`; add `pnpm model:qa:bee:evaluate` for explicit local real-adapter proof-of-life outside normal CI.
- User guide: Add a task-oriented section for Dataset Curators: "Evaluate a Bee Localisation Model Candidate." It must distinguish internal model-governance evaluation from normal beekeeper inspection work.

## Implementation Defaults

- Benchmark source: protected benchmark Dataset Items frozen in the candidate's existing Training Run Dataset Version.
- Separate benchmark-only Dataset Version: out of scope; park until benchmark curation needs its own lifecycle.
- Default confidence threshold: `0.10`, recorded on every run.
- `SMALL_BENCHMARK_SET` cutoff: fewer than 20 benchmark Dataset Items, provisional.
- Matching rule: `ellipse_match_v1`, a replaceable approximation.
- High-severity benchmark leakage warnings: block until acknowledged.
- Fake adapter: allowed in fast tests and dev, clearly labelled.
- Real YOLO adapter: opt-in QA/developer path only, not part of normal CI.
- Adapter selection: follows environment configuration, not a UI toggle.
- Real-adapter readiness: readiness includes `real_adapter_available` and `real_adapter_unavailable_reason` even when the configured run uses fake adapter.
- Real candidate artifact use: real evaluation requires a candidate artifact manifest with usable trained weights; it must not guess from folder names and must not fall back to base YOLO weights or fake outputs.
- Adapter compatibility: fake-trained candidates cannot be evaluated with the real YOLO adapter; real-trained candidates may be evaluated with the fake adapter only in tests/dev with unavoidable fake labelling.
- Evaluation records: multiple Benchmark Evaluations are allowed per Model Candidate; latest completed drives the summary while all statuses remain in history.
- Cancellation: cooperative only while queued/running; no partial metrics artifact.
- Deletion: out of scope for normal UI.
- Storage: reuse the existing model artifact root and Postgres-backed metadata pattern from Slice 0015/0015.1.
- Report artifacts: stored under the existing model-runs artifact root and retrieved only through known artifact ids, never raw filesystem paths.
- QA command: `pnpm model:qa:bee:evaluate` uses the latest completed real YOLO Model Candidate by default, requires existing benchmark Dataset Items, waits for completion, prints the Benchmark Evaluation id and report artifact id/path, has a default 10-minute timeout, and cancels the run it started on timeout.

## Test Seams

- Seam: benchmark readiness
- Behaviour verified: no benchmark items blocks evaluation; withdrawn, rights-invalidated, scope-incompatible, or quarantined evidence blocks evaluation; benchmark items with leakage or weak representativeness produce warnings; Dataset Curator capability is required.
- Test style: Core API route/workflow tests.

- Seam: Model Candidate eligibility
- Behaviour verified: only completed Bee Localisation Model Candidates with available artifacts can be evaluated; fake/test candidates remain labelled as such; candidates from another Workspace are blocked; fake-trained candidates cannot run through the real adapter; missing trained weights fail readiness or fail durably if discovered at runtime.
- Test style: Core API tests with deterministic records.

- Seam: evaluation adapter
- Behaviour verified: fake adapter returns deterministic predictions; real adapter remains opt-in and not part of normal CI; real adapter uses trained candidate weights from artifact metadata and never base weights fallback.
- Test style: dependency-injected fake adapter tests plus explicit QA lane for real YOLO.

- Seam: prediction-to-ground-truth matching
- Behaviour verified: matched predictions count as true positives; unmatched predictions count as false positives; unmatched reviewed ellipses count as false negatives; complete and partial bees are summarized separately.
- Test style: pure unit tests around the matching function plus workflow tests.

- Seam: Benchmark Evaluation persistence
- Behaviour verified: Benchmark Evaluation metadata and artifact references survive Core API restart against Postgres.
- Test style: opt-in live Postgres integration test using Docker.

- Seam: report artifacts
- Behaviour verified: Markdown and JSON reports include model, dataset, metric, warning, and caveat evidence and can be retrieved only through known artifact ids.
- Test style: API tests.

- Seam: Web UI
- Behaviour verified: Dataset Curator can see benchmark readiness, run a fake benchmark evaluation, see metrics/warnings, and open report links; ordinary users cannot run evaluation.
- Test style: Playwright acceptance.

- Seam: API-level BDD acceptance
- Behaviour verified: no benchmark blocks evaluation; completed candidate produces a benchmark report without promotion.
- Test style: two focused Gherkin scenarios mapped to Core API tests.

- Seam: local model-job coordination
- Behaviour verified: a queued/running Training Run blocks Benchmark Evaluation start; a queued/running Benchmark Evaluation blocks Training Run start and another Benchmark Evaluation start; cancellation transitions only queued/running evaluations.
- Test style: Core API workflow tests.

## Data Shape

### Benchmark Evaluation

Minimum fields:

- `benchmark_evaluation_id`
- `workspace_id`
- `human_readable_id`: `HS-BE-000001`
- `model_candidate_id`
- `model_candidate_human_readable_id`
- `training_run_id`
- `training_dataset_version_id`
- `benchmark_dataset_version_id` or `benchmark_selection_snapshot`
- `benchmark_sampling_plan_snapshot`
- `benchmark_frozen_at`
- `model_purpose`: existing API value `bee_detector`, documented and reported as Bee Localisation; contract renaming is out of scope for this slice.
- `adapter_type`
- `status`: `queued`, `running`, `completed`, `failed`, `cancelled`
- `phase`
- `database_purpose`
- `evaluation_settings`
- `matching_rule`
- `benchmark_dataset_item_ids`
- `benchmark_item_count`
- `started_at`
- `completed_at`
- `last_heartbeat_at`
- `failure_code`
- `failure_message`
- `cancel_reason`
- `metrics_summary`
- `warning_summary`
- `scope_compatibility_summary`
- `rights_impact_summary`
- `attribution_summary`
- `artifact_ids`
- `report_artifact_id`
- `json_artifact_id`
- `prediction_artifact_id`
- `created_by_user_id`
- `created_at`

### Metrics Summary

Minimum fields:

- `complete_visible_bee_precision`
- `complete_visible_bee_recall`
- `partial_visible_bee_precision`
- `partial_visible_bee_recall`
- `complete_true_positive_count`
- `complete_false_positive_count`
- `complete_false_negative_count`
- `partial_true_positive_count`
- `partial_false_positive_count`
- `partial_false_negative_count`
- `reviewed_complete_visible_bee_count`
- `reviewed_partial_visible_bee_count`
- `predicted_complete_visible_bee_count`
- `predicted_partial_visible_bee_count`
- `overall_true_positive_count`
- `overall_false_positive_count`
- `overall_false_negative_count`
- `overall_precision`
- `overall_recall`
- `per_item_metrics`
- distribution summaries by image quality, source group, Hive Configuration, and curriculum stage where available

### Per-Item Metrics

Minimum fields:

- `dataset_item_id`
- `training_crop_id`
- `source_image_id`
- `source_group_key`
- `curriculum_stage`
- `hive_configuration_summary`
- `reviewed_complete_visible_bee_count`
- `reviewed_partial_visible_bee_count`
- `predicted_complete_visible_bee_count`
- `predicted_partial_visible_bee_count`
- `true_positive_count`
- `false_positive_count`
- `false_negative_count`
- `warning_codes`
- `artifact_ids`

### Prediction Artifact

Minimum fields:

- `dataset_item_id`
- `model_candidate_id`
- `evaluation_settings`
- `adapter_type`
- `model_native_predictions`
- `normalized_hivesight_geometry`
- `match_outcomes`
- `created_at`

Rules:

- Prediction artifacts are derived diagnostics, not Candidate Annotations and not reviewed evidence.
- JSON artifacts include raw predictions; Markdown reports summarize them rather than listing every model-native value by default.

### Benchmark Warning

Minimum fields:

- `code`
- `severity`: `info`, `warning`, `high`
- `message`
- `affected_dataset_item_ids`

Suggested warning codes:

- `NO_BENCHMARK_ITEMS`
- `SMALL_BENCHMARK_SET`
- `BENCHMARK_EASY_ONLY`
- `BENCHMARK_SOURCE_IMAGE_LEAKAGE`
- `BENCHMARK_SOURCE_GROUP_LEAKAGE`
- `MODEL_ASSISTED_BENCHMARK_REVIEW`
- `NO_HUMAN_FROM_SCRATCH_BENCHMARK_ITEMS`
- `MISSING_BENCHMARK_IMAGE_BYTES`
- `INVALID_BENCHMARK_GEOMETRY`
- `UNSUPPORTED_BENCHMARK_ANNOTATION_TYPE`
- `EVALUATION_SCOPE_NOT_PERMITTED`
- `CONTRIBUTION_PERMISSION_WITHDRAWN`
- `SOURCE_RIGHTS_INVALIDATED`
- `SOURCE_RIGHTS_PENDING_REVIEW`
- `MODEL_ARTIFACT_QUARANTINED`
- `ATTRIBUTION_REQUIRED`
- `FAKE_EVALUATION`
- `REAL_ADAPTER_UNAVAILABLE`
- `REAL_WEIGHTS_MISSING`
- `HEAD_DIRECTION_NOT_EVALUATED`
- `VARROA_NOT_EVALUATED`

## Out Of Scope

- Model promotion.
- Human approval workflow.
- User-facing Model Version creation.
- Beekeeper-facing Varroa assessment or inspection analysis.
- Varroa Detector evaluation.
- Head-direction prediction evaluation.
- Threshold tuning against the benchmark set.
- Active-learning candidate selection from benchmark failures.
- Writing Candidate Annotations from evaluation predictions.
- Durable rejected Candidate Annotation audit history.
- Second-review or adjudication workflow for benchmark labels.
- Duplicate or near-duplicate image detection beyond obvious Source Image/source group warnings.
- Full confusion-matrix dashboards or model-comparison leaderboards.
- Production model registry integration.
- Contribution Withdrawal, Source Rights Invalidation, or model-artifact quarantine workflows themselves.
- Formal public-source licence compatibility review for release, sharing, publication, commercial use, or user-facing deployment.
- Separate benchmark-only Dataset Version lifecycle or benchmark curation UI.
- Precise rotated-IoU geometry scoring if `ellipse_match_v1` is sufficient for the first proof point.
- Full-frame Bee Localisation evaluation.
- Side-by-side Model Candidate comparison.
- Normal UI deletion of Benchmark Evaluation records.
- UI adapter switching.
- Fixed numeric model-quality pass/fail thresholds.

## Acceptance Criteria

- [ ] Dataset Curator can check benchmark readiness for a completed Bee Localisation Model Candidate.
- [ ] Evaluation is blocked with a clear message when there are no benchmark Dataset Items.
- [ ] Benchmark Dataset Items are not used for training or threshold tuning as part of this slice.
- [ ] Dataset Curator can run a fake/local Benchmark Evaluation for a completed Model Candidate.
- [ ] Multiple Benchmark Evaluations are allowed per Model Candidate, with latest completed shown as the summary and failed/running/cancelled records retained in history.
- [ ] Evaluation records model candidate, training Dataset Version, protected benchmark evidence, adapter type, settings, matching rule, metrics, warnings, artifacts, actor, and timestamps.
- [ ] Evaluation records training adapter type, evaluation adapter type, database purpose, model artifact id, report artifact id, JSON artifact id, and prediction artifact id.
- [ ] Evaluation is blocked when required evidence is withdrawn, rights-invalidated, outside the `evaluation` Permitted Use Scope, or depends on a quarantined Dataset Version or Model Candidate.
- [ ] Evaluation is blocked when benchmark image bytes are missing, benchmark reviewed geometry is invalid/missing, unsupported benchmark annotation types are present, or the active local model-job lock is held.
- [ ] Fake-trained candidates cannot be evaluated with the real YOLO adapter; real YOLO evaluation uses trained candidate weights from artifact metadata and fails clearly if they are missing.
- [ ] Report includes Source Rights Record, Contributor Contribution Permission, attribution, and scope-compatibility summaries.
- [ ] Complete visible bee and partial visible bee metrics are reported separately.
- [ ] Report includes per-item summary rows, benchmark representativeness, source-group, Hive Configuration, curriculum-stage, review-method, and leakage warnings.
- [ ] Benchmarks with fewer than 20 items warn with `SMALL_BENCHMARK_SET` and a plain-English caveat that metrics are workflow evidence only.
- [ ] Benchmark source-image/source-group leakage is high severity and must be acknowledged before the run starts.
- [ ] Report clearly states that only Bee Localisation is evaluated.
- [ ] Report clearly states that Varroa detection and head-direction prediction are not evaluated.
- [ ] Report clearly states Training Crop benchmark only when full-frame evaluation is not included.
- [ ] Raw model-native predictions and normalized HiveSight geometry are stored in JSON/prediction artifacts but are not written as Candidate Annotations.
- [ ] Model Candidate remains non-user-facing after evaluation and may move only to `benchmark_reported`.
- [ ] Running Benchmark Evaluations show proof-of-life status and can be cooperatively cancelled; cancelled runs retain status/reason/logs without partial metrics.
- [ ] Benchmark Evaluation metadata and artifacts survive Postgres restart.
- [ ] Web UI shows latest completed Benchmark Evaluation status/summary, recent run history, adapter type, caveats, explicit Markdown report action, JSON download action, and hides evaluation controls from ordinary beekeeper UI.
- [ ] `pnpm dev:all:yolo` and `pnpm dev:lan:yolo` aliases are available while preserving existing `*-yolo-training` commands.
- [ ] `pnpm model:qa:bee:evaluate` runs the latest completed real YOLO candidate by default, waits for completion, prints the Benchmark Evaluation id and report artifact reference, and cancels its run on timeout.
- [ ] User guide includes "Evaluate a Bee Localisation Model Candidate" and states it is a Dataset Curator/model-governance task, not normal beekeeper inspection work.
- [ ] API-level BDD includes focused scenarios for no-benchmark blocking and completed candidate report creation without promotion.
- [ ] API tests cover readiness, eligibility, matching, persistence, and artifact retrieval.
- [ ] Browser acceptance covers the curator-visible evaluation path.
- [ ] `pnpm verify:slice` passes.
- [ ] Live Postgres verification passes, or the slice remains implemented but not acceptance-closed.

## Open Questions

None before implementation. Metric formulas and JSON field refinements can be resolved during TDD while preserving the behaviours and gates above.
