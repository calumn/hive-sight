# Vertical Slice 0028: Frame Mite Counting Workflow

Status: designed; grilling decisions incorporated; acceptance scenarios formally accepted on 2026-08-06.

## Purpose

Run the Varroa Detector path across all currently eligible bees in one photographed frame and return the first model-assisted visible mite count with explicit caveats.

This slice turns the single-bee detector preview from Slice 0027 into a frame-level counting workflow. It proves that HiveSight can enumerate eligible Head-Up Normalized Bee Crops for a selected Inspection Photo, invoke the configured Varroa Detector adapter for each one, aggregate the detections, disclose losses and failures, and show a non-user-facing frame mite count that can later become the input to the HiveSight Advisor context API.

This is still not a user-facing Varroa Assessment, Visible Varroa Rate, treatment trigger, sampling-policy claim, or HiveSight Advisor call.

## Source Inputs

- `CONTEXT.md`: Varroa Detector, Head-Up Normalized Bee Crop, Frame-Level Varroa Result Summary, Varroa Review, Likely Varroa Detection, Varroa Assessment, Varroa Sampling Plan.
- `requirements/roadmap.md`: Slice 0028 Frame Mite Counting Workflow, Slice 0029 Advisor Varroa Context API, Slice 0030 Varroa Corpus Governance.
- `requirements/model-requirements.md`: MR-002 Varroa Detection, MR-003 Detection Association, MR-004 Complete Bee Denominator, MR-006 Headline Varroa Numerator, MR-007 Additional Varroa Evidence, MR-018C Separate Varroa Sampling Policies, MR-030A End-To-End Pipeline Evaluation Before Promotion.
- `requirements/varroa-evidence-methodology.md`: separation of detector output, end-to-end pipeline evaluation, and future inspection-rate estimation.
- `architecture/adr/0007-three-stage-bee-localisation-orientation-and-varroa-pipeline.md`: the staged Bee Localisation, Bee Orientation, and Varroa Detection pipeline; no Varroa inference on guessed orientation.
- `architecture/domain-model.md`: Varroa Detection, Varroa Annotation, Frame-Level Varroa Result Summary, Varroa Sampling Plan, non-claims around treatment and rate estimation.
- `architecture/vertical-slice-0026-frame-level-varroa-result-summary.md`: human-reviewed photo-visible evidence summary.
- `architecture/vertical-slice-0027-varroa-detector-adapter-seam.md`: injected Varroa Detector adapter seam and deterministic single-bee stub preview.
- `architecture/parking-lot.md`: PARK-0030 Inspection-Rate Sampling Policy, PARK-0031 User-Facing Varroa Coverage Threshold, PARK-0032 Inadequate-Coverage Review Recovery, PARK-0051 Production Inspection-Rate Sampling And Field Calibration Implementation.

## Grilling Decisions

- Slice 0028 counts over the current reviewed frame evidence, not the future fully automated raw-photo pipeline.
- The counted population is the eligible complete visible bee annotations from completed, non-excluded Training Crops for one selected Inspection Photo.
- The workflow is scoped to exactly one selected Inspection Photo, not the whole Inspection.
- All eligible bees are processed in Slice 0028; no sampling, random selection, strata, or sample size policy is introduced.
- Eligibility matches the Slice 0027 detector gate:
  - `complete_visible_bee`;
  - Orientation Reliability is `reliable`;
  - source image bytes and Head-Up Normalized Bee Crop transform are available;
  - source Training Crop is `review_complete`.
- Partial visible bees, unreliable-orientation bees, unfinished crops, excluded crops, failed transforms, and adapter failures are reported as not assessed or failed, not as negatives.
- Partial visible bees are disclosed as out of scope for the first frame mite count, not counted as supplementary Varroa evidence in this slice.
- The workflow uses the same injected `VarroaDetectorAdapter` as Slice 0027.
- The endpoint uses the configured Varroa Detector adapter only; there is no request-level adapter or model override.
- With the deterministic stub adapter, every eligible bee returns one likely visible mite detection.
- A bee with zero model detections is still a completed model inference with `detection_count = 0`; it is not a human active negative.
- The result is derived/run on demand in Slice 0028. It is current/transient, not stored as a durable signed Varroa Assessment revision, Analysis Result, latest result, or result history.
- Re-running the frame mite count clears the previous transient result and replaces it with the new run result.
- The visible frame mite count is scoped to the selected Inspection Photo. It remains visible while switching crops or bees on that photo, and clears when the selected photo changes.
- The Web UI exposes a manual `Run frame mite count` action in the existing `Varroa Review` stage, near the photo-visible evidence summary.
- `Run frame mite count` is available only to Dataset Curators in the Training Inspection Workflow.
- The frame mite count remains inside Training Data Collection inspections only.
- The result is a model-assisted frame count card, separate from the human-reviewed `Photo-visible Varroa evidence` summary from Slice 0026.
- The frame mite count card appears immediately below or next to the human-reviewed photo-visible evidence card, before the selected-crop bee review UI.
- The UI shows aggregate counts first, plus a compact per-bee breakdown with `Crop N / Bee M`, status, detection count, and failure/not-assessed reason where applicable.
- Per-bee result rows may select the corresponding crop/bee in the existing Varroa Review surface if that is cheap to implement; full per-bee image previews in the result list are out of scope.
- The UI shows processed/eligible counts and model determinate coverage percent.
- The UI uses `Frame mite count` for the section and `Run frame mite count` for the action. Evidence fields use `Likely visible Varroa detections` and `Bees with likely Varroa`.
- The UI has one running state for the whole frame count request. Per-bee statuses appear only after the result returns.
- Human Varroa Review Outcomes are not created, changed, or overwritten by this workflow.
- Human Varroa Review Outcomes are not used as overrides or validation inputs for the model-assisted count in Slice 0028.
- The Slice 0026 human-reviewed evidence summary remains human-reviewed only and is not silently mixed with model-only counts.
- Running the frame mite count does not update, mutate, or refresh the human-reviewed photo-visible evidence card except through normal unrelated page refresh behaviour.
- The result is explicitly labelled deterministic stub/model-assisted evidence only, not user-facing, not promotable, and not treatment advice.
- A zero-detection model run is displayed as `0 likely detections`, never as `No visible Varroa`.
- The result includes enough shape for Slice 0029 to expose Advisor context later, but Slice 0028 does not call HiveSight Advisor.
- Slice 0028 includes caveat wording that this is not Advisor context yet; the formal Advisor availability contract remains Slice 0029.
- No threshold, high/medium/low warning, risk band, treatment implication, or Advisor trigger is shown.
- The response includes `inspection_id`, `hive_id`, and `inspection_date`; `apiary_id` may be included only if cheap and non-invasive.
- API per-bee results include detection coordinates and Head-Up Normalized crop/transform metadata; the UI keeps transform provenance compact rather than prominent.
- Completed, unfinished, and excluded Training Crop counts are reported separately.
- The count is over eligible bee annotations from completed crops, not deduplicated physical bees across overlapping source-frame regions; overlapping crops are explicitly caveated.
- `completed_with_warnings` is a first-class status whenever at least one eligible bee was processed but some bee/crop evidence was not assessed or failed.
- `completed` means all eligible evidence was processed, including the case where the detector returned zero detections.
- `not_available` is returned with reasons when there are no completed crops, no eligible bees, or no processable bees; this is not an HTTP error.
- `failed` is reserved for whole-frame or system-level faults that prevent a meaningful domain result.
- The API response uses one `caveats` field for the non-user-facing, non-Advisor, non-treatment caveat text.
- No database migration or durable `FrameMiteCount` table is added.
- No special live Postgres verification gate is required unless implementation unexpectedly changes durable persistence/query behaviour beyond existing seams.
- Observability logs one aggregate frame-count run event, not one event per bee.
- Implementation closeout updates `docs/user-guide.md` and adds a lightweight `Frame Mite Count` section to `architecture/domain-model.md`.

## User Path

Given a Dataset Curator has a Training Data Collection Inspection Photo with completed Training Crops and reliable complete bee annotations,
When they open the Varroa Review stage and run the frame mite count,
Then HiveSight runs the configured Varroa Detector against each eligible Head-Up Normalized Bee Crop and shows a model-assisted frame mite count with processed-bee, detection, coverage, provenance, and caveat details.

## Preconditions

- The selected User has Dataset Curator capability.
- Workspace Data Use Agreement requirements remain enforced.
- The source Inspection has intent `training_data_collection`.
- The selected Inspection Photo has at least one completed Training Crop.
- At least one completed Training Crop has bee annotations.
- The configured Varroa Detector adapter is the deterministic stub by default.
- The source evidence is current Training Crop evidence; it may be project-owned training evidence, not beekeeper-facing production assessment evidence.

## End-To-End Behaviour

The Varroa Review stage gains a manual model-assisted frame counting section for the selected Inspection Photo:

- button: `Run frame mite count`;
- status: not run, running, completed, completed with warnings, or failed;
- wording: `Model-assisted frame count from this run`;
- source photo filename;
- completed Training Crops considered;
- unfinished and excluded Training Crops not counted;
- eligible complete bees processed;
- bees not assessed;
- bee-level detector failures;
- likely visible Varroa detections;
- bees with one or more likely detections;
- processed/eligible model determinate coverage percentage;
- adapter provenance;
- elapsed time;
- caveat text.

When the Dataset Curator runs the count, Core API:

1. applies access, Workspace Data Use Agreement, inspection intent, and source-photo gates;
2. loads completed Training Crops for the selected Inspection Photo;
3. enumerates complete reliable Bee Annotations from those crops;
4. excludes partial, unreliable, ineligible, unfinished, or transform-unavailable evidence with reasons;
5. generates a Head-Up Normalized Bee Crop for each eligible bee;
6. invokes the injected `VarroaDetectorAdapter` for each eligible bee;
7. aggregates detections into a frame-level result;
8. returns aggregate counts, per-bee summaries, adapter provenance, elapsed time, and caveats.

The first implementation is synchronous and stub-backed. This is acceptable because the initial data volume is tiny and the stub is deterministic. A future real model or larger photo may require queueing and progress tracking.

The result separates:

- `eligible_bee_count`: complete reliable bees that should be assessed;
- `processed_bee_count`: eligible bees successfully sent through the detector;
- `bee_with_likely_varroa_count`: processed bees with one or more likely detections;
- `likely_varroa_detection_count`: total likely detections across processed eligible bees;
- `not_assessed_bee_count`: eligible or visible bees that could not be assessed, grouped by reason;
- `failed_bee_count`: adapter or transform failures;
- `model_determinate_coverage_percent`: processed eligible bees divided by eligible bees.

The first stub result should be predictable: if a selected photo has three eligible bees across completed crops, the deterministic adapter reports three processed bees, three bees with likely detections, and three likely detections.

The UI shows aggregates first and a compact per-bee breakdown second. Per-bee rows use human labels such as `Crop 3 / Bee 8`; ids remain in API details and stable test hooks rather than primary display text. A row may select the corresponding crop and bee in the existing Varroa Review surface, but the result list does not become a multi-bee image review workbench.

The result is transient. Clicking `Run frame mite count` again replaces the visible result. Switching crops or bees on the same Inspection Photo leaves it visible; switching selected Inspection Photo clears it. The UI must not call it the latest or official result.

The UI must not merge this model-assisted count into the human-reviewed photo-visible evidence summary. The two cards can sit near each other, but their provenance and claim boundaries remain separate. The count is over eligible bee annotations from completed crops, not deduplicated physical bees across overlapping source-frame regions.

## Layers Touched

- Web UI: Add a manual frame mite count section to the Varroa Review stage for the selected Inspection Photo, with aggregate counts, caveats, and adapter provenance separate from human-reviewed evidence.
- Core API: Add a frame-level Varroa detector workflow and endpoint that enumerates eligible bees, invokes the injected detector adapter for each eligible Head-Up crop, and aggregates the result.
- Analysis Service: Not touched in Slice 0028; a later real-model or long-running adapter can move behind an async service boundary.
- Storage: No new durable table in Slice 0028; result is returned on demand and not persisted as a Varroa Assessment revision.
- Queue or async boundary: Not touched; synchronous in the first stub-backed slice.
- Contracts: Add `FrameMiteCountRequest`, `FrameMiteCountResponse`, `FrameMiteCountBeeResult`, and structured not-assessed/failure reason fields.
- Observability: Log one aggregate frame-count run with workspace id, inspection photo id, crop count, eligible bee count, processed bee count, detection count, not-assessed count, failure count, adapter type/version, elapsed time, and status.

## Test Seams

- Seam: Frame mite count workflow
- Behaviour verified: enumerates eligible complete reliable bees from completed Training Crops for one Inspection Photo, invokes the adapter for each eligible bee, and aggregates detection counts.
- Test style: focused Core API/service tests.

- Seam: Eligibility and loss accounting
- Behaviour verified: partial bees, unreliable-orientation bees, unfinished crops, excluded crops, unavailable transforms, and adapter failures are reported as not assessed or failed and are not treated as negatives.
- Test style: focused Core API tests and API-level BDD.

- Seam: Human evidence separation
- Behaviour verified: running a model-assisted frame count does not create or change Varroa Review Outcomes and does not change the human-reviewed photo-visible Varroa evidence summary.
- Test style: API tests and browser acceptance.

- Seam: Web frame count action
- Behaviour verified: Dataset Curator can run the count from the Varroa Review stage, see processed bees, likely detections, coverage, provenance, caveats, and no-treatment-advice language.
- Test style: Playwright browser acceptance.

## Data Shape

Minimum endpoint:

- `POST /v1/inspection-photos/{inspection_photo_id}/frame-mite-count`

Minimum request body:

- `workspace_id`

Minimum response model:

- `FrameMiteCountResponse`
  - `workspace_id`
  - `inspection_id`
  - `hive_id`
  - `apiary_id`, optional
  - `inspection_photo_id`
  - `inspection_date`
  - `source_image_filename`
  - `source_intent`
  - `status`: `completed` | `completed_with_warnings` | `failed` | `not_available`
  - `model_purpose`: `varroa_detection`
  - `adapter_type`
  - `adapter_version`
  - `model_reference`
  - `completed_training_crop_count`
  - `unfinished_training_crop_count`
  - `excluded_training_crop_count`
  - `eligible_bee_count`
  - `processed_bee_count`
  - `bee_with_likely_varroa_count`
  - `likely_varroa_detection_count`
  - `not_assessed_bee_count`
  - `failed_bee_count`
  - `model_determinate_coverage_percent`
  - `elapsed_ms`
  - `bee_results`
  - `not_assessed_reasons`
  - `failure_reasons`
  - `not_user_facing_reason`
  - `caveats`

- `FrameMiteCountBeeResult`
  - `training_crop_id`
  - `bee_annotation_id`
  - `status`: `completed` | `not_assessed` | `failed`
  - `not_assessed_reason`
  - `failure_code`
  - `failure_message`
  - `detection_count`
  - `detections`
  - `head_up_normalized_crop`
  - `transform_version`
  - `transform_metadata`

Derived rules:

- `processed_bee_count` counts only bee results with `status = completed`.
- `bee_with_likely_varroa_count` counts processed bees with `detection_count > 0`.
- `likely_varroa_detection_count` is the sum of detections across processed bees.
- `model_determinate_coverage_percent = processed_bee_count / eligible_bee_count`, with zero when `eligible_bee_count` is zero.
- `completed_with_warnings` is returned when at least one eligible bee was processed but some visible bee evidence was not assessed or failed.
- `completed` is returned when all eligible evidence was processed, including when the detector returns zero detections.
- `not_available` is returned when no completed crops, no eligible bees, or no processable bees are available.
- `failed` is reserved for whole-frame or system-level faults that prevent a meaningful domain result.
- A model count with zero detections is a model output, not a human active negative Varroa Review Outcome.
- A model count with zero detections is displayed as `0 likely detections`, not `No visible Varroa`.

## Acceptance Scenarios

Acceptance signoff given on 2026-08-06.

```gherkin
Feature: Frame mite counting workflow

  Scenario: Dataset Curator runs a model-assisted mite count for one photographed frame
    Given a Training Data Collection Inspection Photo has completed Training Crops with reliable complete bees
    And HiveSight is using the deterministic stub Varroa Detector adapter
    When the Dataset Curator runs the frame mite count for that photo
    Then HiveSight sends each eligible Head-Up Normalized Bee Crop through the configured Varroa Detector adapter
    And HiveSight reports the eligible bee count, processed bee count, bees with likely Varroa, and likely Varroa detection count
    And HiveSight reports model determinate coverage
    And HiveSight shows adapter provenance and elapsed time
    And HiveSight labels the result as model-assisted frame evidence from this run only

  Scenario: The frame count excludes bees and crops that cannot support Varroa detection
    Given a Training Data Collection Inspection Photo has complete reliable bees, partial bees, unreliable-orientation bees, and unfinished Training Crops
    When HiveSight runs the frame mite count for that photo
    Then HiveSight runs the Varroa Detector only for eligible complete reliable bees from completed Training Crops
    And HiveSight reports not-assessed bees, unfinished crops, and excluded crops separately
    And HiveSight does not treat not-assessed bees as negative Varroa results
    And HiveSight returns completed with warnings when at least one eligible bee was processed

  Scenario: Model-assisted frame counts do not overwrite human Varroa evidence
    Given a Training Data Collection Inspection Photo already has human Varroa Review Outcomes
    When the Dataset Curator runs the frame mite count for that photo
    Then HiveSight shows the model-assisted frame count separately from the human-reviewed photo-visible evidence summary
    And HiveSight leaves the human Varroa Review Outcomes and markers unchanged
    And HiveSight leaves the human-reviewed photo-visible evidence summary unchanged

  Scenario: The transient frame count is scoped to the selected photo
    Given the Dataset Curator has run a frame mite count for one Inspection Photo
    When the Dataset Curator selects another crop or bee from the same photo
    Then HiveSight keeps the frame mite count visible
    When the Dataset Curator selects a different Inspection Photo
    Then HiveSight clears the previous frame mite count
    And HiveSight waits for the Dataset Curator to manually run a new count

  Scenario: The per-bee result list stays compact and navigable
    Given a model-assisted frame mite count has completed
    When the Dataset Curator reviews the per-bee result list
    Then HiveSight shows Crop number, Bee number, status, and detection count for each bee result
    And HiveSight shows any not-assessed or failure reason for the affected bee
    And HiveSight can select the corresponding crop and bee in the existing Varroa Review surface
    And HiveSight does not show per-bee image previews inside the frame count result list

  Scenario: The frame count is unavailable when no eligible bee can be processed
    Given a Training Data Collection Inspection Photo has no eligible complete reliable bees on completed Training Crops
    When the Dataset Curator runs the frame mite count for that photo
    Then HiveSight returns a frame count status of not_available
    And HiveSight explains why no bee was processed
    And HiveSight does not report a zero-mite result

  Scenario: Per-bee adapter failures are visible without hiding successful counts
    Given the configured Varroa Detector adapter fails for one eligible bee and succeeds for another
    When HiveSight runs the frame mite count for the photo
    Then HiveSight reports the successful detection counts
    And HiveSight reports the failed bee count and failure reason
    And HiveSight returns completed with warnings
    And HiveSight does not create or change a Varroa Review Outcome

  Scenario: The frame mite count does not trigger treatment advice
    Given a model-assisted frame mite count has likely visible Varroa detections
    When the Dataset Curator reviews the count
    Then HiveSight states that the result is not a Varroa Assessment, Visible Varroa Rate, treatment recommendation, Advisor context, or HiveSight Advisor trigger
    And HiveSight does not call HiveSight Advisor

  Scenario: Zero model detections remain model output rather than human negative evidence
    Given an eligible bee is processed by a Varroa Detector adapter that returns zero detections
    When HiveSight includes that bee in the frame mite count
    Then HiveSight counts the bee as processed
    And HiveSight reports zero likely detections for that bee
    And HiveSight does not create or imply a no-visible-Varroa human review outcome
```

## Out Of Scope

- Running the full Bee Localisation and Bee Orientation model pipeline from raw photos.
- Real Varroa Detector model inference, training, benchmarking, or promotion.
- Persisted model-only Varroa Assessment revisions.
- Durable frame mite count history, comparison, or latest-result lifecycle.
- Creating, updating, or approving human Varroa Review Outcomes from model detections.
- AI-assisted human review of model mite boxes.
- Copying model detections into human Varroa Markers.
- Frame-level duplicate bee reconciliation across overlapping Training Crops.
- Source image or source crop overlays for all model mite detections.
- Per-bee image gallery or review workbench inside the frame count result list.
- Inspection-rate sampling, stratification, sequential stopping, confidence intervals, or a statistically defended Visible Varroa Rate.
- User-facing treatment thresholds, risk bands, advice language, or HiveSight Advisor calls.
- HiveSight Advisor Varroa Context API; that remains Slice 0029.
- Varroa Corpus Governance; that remains Slice 0030.

## Acceptance Criteria

- [ ] The Core API can run a frame mite count for one selected Inspection Photo using the configured Varroa Detector adapter.
- [ ] The workflow sends only eligible complete reliable bees from completed Training Crops through the adapter.
- [ ] The response reports eligible bees, processed bees, bees with likely Varroa, likely detection count, not-assessed bees, failed bees, crop inclusion/exclusion counts, model determinate coverage, elapsed time, adapter provenance, and caveats.
- [ ] Ineligible or unavailable evidence is not treated as a negative Varroa result.
- [ ] Running the count does not create or mutate Varroa Review Outcomes, Varroa Markers, Dataset Items, Dataset Versions, or the human-reviewed photo-visible evidence summary.
- [ ] The Web UI exposes a manual `Run frame mite count` action and result card in the Varroa Review stage for the selected photo.
- [ ] The UI and API state that the result is model-assisted frame evidence only, not a Varroa Assessment, Visible Varroa Rate, treatment recommendation, or Advisor trigger.
- [ ] The UI labels the result as transient output from the current run, keeps it scoped to the selected Inspection Photo, and clears it when the selected photo changes.
- [ ] The UI includes a compact per-bee result list with human-readable Crop/Bee labels and no per-bee image previews.
- [ ] The API includes `inspection_id`, `hive_id`, `inspection_date`, per-bee detection boxes, and Head-Up transform metadata.
- [ ] The result caveats state that eligible bee annotations are not deduplicated physical bees across overlapping crops.
- [ ] `architecture/domain-model.md` and `docs/user-guide.md` are updated at implementation closeout.
- [ ] Focused Core API tests, API-level BDD, browser acceptance, Web type-check, and `pnpm verify:slice` pass before implementation closeout.

## Open Questions For Grilling

- None after grilling and acceptance scenario signoff.
