# Vertical Slice 0027: Varroa Detector Adapter Seam

Status: implemented; acceptance scenarios signed off on 2026-08-05; focused API/BDD, web type, Python style, and browser acceptance checks passed on 2026-08-05.

## Purpose

Add the first replaceable Varroa Detector adapter seam so HiveSight can run a stubbed or later real model against one eligible Head-Up Normalized Bee Crop and return explicit likely visible mite locations.

This slice is a bridge from human Varroa Review evidence to model-assisted mite counting. It proves the contract, provenance, eligibility gates, and UI preview path for Varroa Detection without claiming a user-facing Varroa Assessment, Visible Varroa Rate, treatment trigger, or HiveSight Advisor integration.

It also improves the Varroa Review surface itself: the selected eligible bee is shown as a paired clean and annotated Head-Up view so tiny mite evidence remains visible even when markers or model boxes are drawn.

## Source Inputs

- `CONTEXT.md`: Likely Varroa Detection, Varroa Detector, Head-Up Normalized Bee Crop, Varroa Review Outcome, Varroa Marker, Model Purpose, Model Candidate, Photo-Visible Varroa Evidence Summary.
- `requirements/model-requirements.md`: MR-002 Varroa Detection, MR-009 Varroa Annotation Shape, MR-009A Varroa Review Outcome, MR-018C Separate Varroa Sampling Policies, MR-018D Model-Curation Sampling Method, MR-030A End-To-End Pipeline Evaluation Before Promotion.
- `requirements/varroa-evidence-methodology.md`: separation of model-crop detection, end-to-end evaluation, and inspection-rate estimation.
- `architecture/adr/0007-three-stage-bee-localisation-orientation-and-varroa-pipeline.md`: three logical Model Purposes and the decision that the first Varroa implementation returns explicit mite locations from Head-Up Normalized Bee Crops.
- `architecture/domain-model.md`: Model Candidate, Varroa Detection, Head-Up Normalized Bee Crop, and non-claims around user-facing Varroa estimates.
- `architecture/vertical-slice-0025-varroa-review-outcome-labelling.md`: current Head-Up Normalized Bee Crop generation and human Varroa Review Outcome rules.
- `architecture/vertical-slice-0026-frame-level-varroa-result-summary.md`: derived photo-visible evidence summary that later model-assisted counts will feed.
- `requirements/roadmap.md`: Slice 0027 Varroa Detector Adapter Seam, Slice 0028 Frame Mite Counting Workflow, Slice 0029 Advisor Varroa Context API.

## Grilling Decisions

- The first adapter is a deterministic stub.
- In normal local dev and browser acceptance stub lanes, the default stub returns one predictable fake detection for every eligible bee.
- The fake detection is a small axis-aligned box at a fixed normalized Head-Up crop location, such as around `x=0.52`, `y=0.34`.
- The stub is visibly labelled as deterministic stub output, not user-facing, and not eligible for promotion.
- The adapter protocol lives in Core API for Slice 0027, behind an explicit injected `VarroaDetectorAdapter` seam, with the contract kept portable enough to move behind Analysis Service later.
- The detector preview is view-only. It does not copy boxes into human markers, save Varroa Review Outcomes, update Varroa Review Outcomes, or update the Slice 0026 photo-visible evidence summary.
- Copying model detections into human markers is deferred to a separately named AI-assisted human review workflow, if wanted later.
- The detector preview is shown inside the existing Varroa Review stage for the selected eligible bee, not in Model Governance.
- The selected eligible bee uses a paired clean and annotated Head-Up Normalized Bee Crop view.
- The paired view replaces the existing single Head-Up crop for eligible bees.
- The clean view is visual reference only and remains unmarked.
- The annotated view shows human markers and model-preview boxes at the same time, visually distinct.
- Human markers remain point markers; model detections are thin boxes with a distinct model-preview style.
- Confidence is shown in the detector preview panel/list, not as text on top of the tiny crop image.
- The paired views share one zoom control and one pan state.
- Dragging or panning either view moves both views together.
- A small mode control switches between `Place marker` and `Pan`.
- Marker placement still happens only on the annotated view.
- Model boxes respond to pan and zoom using the same coordinate mapping as human markers.
- Ineligible bees do not show the full paired review surface in Slice 0027; they keep the explicit not-assessed explanation.
- Detector preview can be run before or after a saved human Varroa Review Outcome, including `visible_varroa_present`, `no_visible_varroa`, or `not_determined`, as long as the bee remains eligible.
- Running the preview clears any previous preview when the selected crop or bee changes.
- The preview runs only manually when the Dataset Curator presses `Run detector preview`.
- If a new preview run fails, old preview boxes are cleared and the failure is shown.
- The detector preview is available only when the source Training Crop is `review_complete`.
- The request and response include `workspace_id` for traceability.
- The adapter receives normalized image bytes plus dimensions, transform metadata, source ids, and a compact source geometry snapshot.
- No durable database migration or table is added for `LikelyVarroaDetection` in Slice 0027.
- The photo-visible evidence summary card is not changed to mention detector preview output.
- The detector preview endpoint uses `POST`.
- Ineligible bees return HTTP `200` with `status: not_assessed`.
- Expected adapter failures return HTTP `200` with `status: failed`; authorization, not-found, malformed request, and system faults remain HTTP errors.
- The response includes elapsed time in milliseconds.
- Browser acceptance covers both the detector preview and the paired clean/annotated review surface.

## Acceptance Scenarios

Acceptance signoff given on 2026-08-05.

```gherkin
Feature: Varroa Detector adapter seam

  Scenario: Dataset Curator previews likely Varroa detections on one eligible bee crop
    Given a completed Training Crop contains a reliable complete visible bee
    And HiveSight can generate a Head-Up Normalized Bee Crop for that bee
    When the Dataset Curator runs the Varroa Detector preview for the bee
    Then HiveSight sends the Head-Up Normalized Bee Crop through the configured Varroa Detector adapter
    And HiveSight shows one deterministic Likely Varroa Detection as a model-preview box
    And HiveSight shows the detection location, size, confidence, and elapsed time in the preview details
    And HiveSight labels the result as model preview evidence only
    And HiveSight does not save a Varroa Review Outcome

  Scenario: The Varroa Review surface keeps clean and marked evidence visible together
    Given a Dataset Curator has selected an eligible bee for Varroa Review
    When HiveSight opens the Head-Up Normalized Bee Crop review surface
    Then HiveSight shows a clean Head-Up view and an annotated Head-Up view side by side
    And the clean view has no human markers or model-preview boxes
    And the annotated view shows human markers and model-preview boxes when they exist
    And one shared zoom control changes both views together
    And panning either view moves both views together
    And the Dataset Curator can switch between Place marker mode and Pan mode

  Scenario: The stub adapter is visibly replaceable and non-promotable
    Given HiveSight is using the deterministic stub Varroa Detector adapter
    When the Dataset Curator runs the Varroa Detector preview
    Then HiveSight returns adapter provenance including workspace, model purpose, adapter type, adapter version, model reference, and input transform version
    And HiveSight labels the detections as deterministic stub output
    And HiveSight marks the output as not user-facing and not eligible for promotion

  Scenario: Ineligible bees are not sent to the Varroa Detector adapter
    Given a Training Crop contains a partial visible bee or an unreliable-orientation bee
    When the Dataset Curator tries to run the Varroa Detector preview for that bee
    Then HiveSight returns a detector preview status of not_assessed
    And HiveSight does not call the Varroa Detector adapter
    And HiveSight explains why the bee is not assessed for Varroa Detection
    And HiveSight does not treat the bee as a negative Varroa result

  Scenario: Model preview detections do not overwrite human review evidence
    Given a bee already has a saved human Varroa Review Outcome
    When the Dataset Curator runs the Varroa Detector preview for that bee
    Then HiveSight shows the model preview separately from the saved human outcome
    And HiveSight leaves the human Varroa Review Outcome and markers unchanged
    And HiveSight does not change the photo-visible Varroa evidence summary

  Scenario: Adapter failure is visible without creating evidence
    Given the configured Varroa Detector adapter cannot process the Head-Up Normalized Bee Crop
    When the Dataset Curator runs the Varroa Detector preview
    Then HiveSight clears any previous model-preview boxes
    And HiveSight returns a detector preview status of failed
    And HiveSight reports the adapter failure reason
    And HiveSight records no Likely Varroa Detections
    And HiveSight does not create or change a Varroa Review Outcome

  Scenario: Changing bee or crop clears stale model preview output
    Given the Dataset Curator has run a Varroa Detector preview for one eligible bee
    When the Dataset Curator selects a different bee or Training Crop
    Then HiveSight clears the previous model-preview detections
    And HiveSight waits for the Dataset Curator to manually run a new detector preview
```

## User Path

Given a Dataset Curator is reviewing an eligible bee in the Varroa Review stage,
When they inspect the paired clean/annotated Head-Up crop and run the Varroa Detector preview,
Then HiveSight shows model-produced likely mite boxes on the annotated crop view with adapter provenance and clear non-assessment caveats, while the clean crop view remains available for unobscured visual checking.

## Preconditions

- The selected User has Dataset Curator capability.
- Workspace Data Use Agreement requirements remain enforced.
- The source Inspection has intent `training_data_collection`.
- The source Training Crop is `review_complete`, not excluded, and linked to available source image bytes.
- The selected bee is eligible for Head-Up Normalized Varroa work:
  - `annotation_type` is `complete_visible_bee`;
  - Orientation Reliability is `reliable`;
  - the Head-Up Normalized Bee Crop transform can be generated.
- The configured adapter is the deterministic stub in Slice 0027.
- Adapter output is preview evidence only in this slice.

## End-To-End Behaviour

The Varroa Review stage replaces the single eligible-bee Head-Up crop view with a paired view:

- Clean Head-Up view: unmarked reference image.
- Annotated Head-Up view: same image and viewport, plus human Varroa Markers and model-preview boxes.

The paired views have one shared zoom state and one shared pan state. Panning either view moves both. A compact interaction mode control lets the curator choose `Place marker` or `Pan`. Marker placement remains allowed only in the annotated view and only while `Place marker` mode is active.

The Varroa Review stage also gains a compact `Detector preview` section for the currently selected eligible bee:

- button: `Run detector preview`;
- result status;
- adapter/version/model reference;
- detection count;
- confidence list;
- elapsed time;
- caveat: deterministic stub preview only, not user-facing, not eligible for promotion.

When the preview is invoked, Core API:

1. applies the same access, Workspace Data Use Agreement, inspection intent, crop-completion, source-image, and bee-eligibility gates used by Varroa Review;
2. generates the Head-Up Normalized Bee Crop through the existing transform path;
3. sends normalized image bytes, dimensions, transform metadata, source ids, `workspace_id`, and source geometry snapshot to the injected `VarroaDetectorAdapter`;
4. normalizes adapter output into a stable `LikelyVarroaDetection` response;
5. returns detections, adapter provenance, input provenance, elapsed time, and caveats.

The first adapter is deterministic and local. For every eligible bee in normal local dev and browser acceptance stub lanes, it returns one fixed-location, small axis-aligned fake detection box in the Head-Up Normalized Bee Crop coordinate frame. It exists to prove the seam and the UI, not model quality. A later real adapter can replace it through dependency injection without changing the Web UI contract.

The UI overlays model-preview boxes on the annotated Head-Up view using a distinct visual treatment from human Varroa Markers. Human markers and model boxes may be shown together for comparison. Confidence appears in the detector preview panel/list rather than on the crop image.

Detector preview can be run before or after the bee has a saved human Varroa Review Outcome, including positive, active negative, or `not_determined`, provided the bee remains eligible. The saved human outcome remains separate and unchanged.

Detector preview is manual only. Selecting a different bee or crop clears previous model-preview output and waits for the curator to run a new preview. If a new run fails, old preview boxes are cleared and the failure is shown.

Ineligible bees return `status: not_assessed` and are not sent to the adapter. A `not_assessed` response is not a negative Varroa result. Expected adapter failures return `status: failed`; authorization, not-found, malformed request, and system faults remain HTTP errors.

The model preview result is not persisted as a Varroa Review Outcome, Dataset Item, Dataset Version item, Benchmark Evaluation, user-facing Varroa Assessment, Photo-Visible Varroa Evidence Summary input, or Advisor context. Slice 0028 may consume the same adapter seam for model-assisted frame counting, but this slice only proves single-bee invocation.

## Layers Touched

- Web UI: Replace the eligible-bee single Head-Up crop view with paired clean/annotated Head-Up views; add shared zoom and pan; add `Place marker` / `Pan` modes; add a `Detector preview` section for the selected eligible bee; display model-preview boxes distinctly from human markers; clear stale preview output on selected bee/crop change.
- Core API: Add an injected `VarroaDetectorAdapter`, deterministic stub implementation, workflow, and `POST` endpoint to run Varroa Detection preview for one Training Crop bee candidate and return normalized detection output.
- Analysis Service: Not touched in Slice 0027; the seam stays in Core API for synchronous single-bee preview and may move behind Analysis Service later.
- Storage: No durable persistence and no database migration for model-preview detections in this slice.
- Queue or async boundary: Not touched; preview inference is synchronous and local/stubbed.
- Contracts: Add request/response contracts and public Core API response models for `VarroaDetectorPreviewResponse` and `LikelyVarroaDetection`.
- Observability: Log detector preview attempts with workspace id, inspection photo id, training crop id, bee annotation id, adapter type/version, detection count, elapsed time, status, and failure code when applicable.

## Test Seams

- Seam: Varroa Detector adapter protocol
- Behaviour verified: deterministic stub receives normalized crop input and provenance, and returns one stable likely mite box with confidence, elapsed time, and stub provenance.
- Test style: focused service/workflow tests with a generated fixture image.

- Seam: Core API detector preview endpoint
- Behaviour verified: `POST` request enforces access and eligibility gates; successful responses include detections, input provenance, adapter provenance, caveats, elapsed time, and no human outcome mutation.
- Test style: focused API tests and API-level BDD.

- Seam: Not-assessed and failure normalization
- Behaviour verified: ineligible bees return `status: not_assessed` without calling the adapter; expected adapter errors return `status: failed`; neither path creates detections or changes Varroa Review Outcomes.
- Test style: focused API/service tests.

- Seam: Paired Head-Up review surface
- Behaviour verified: eligible bees show clean and annotated paired views, overlays appear only on the annotated view, and shared zoom/pan controls are present.
- Test style: Playwright browser acceptance plus focused frontend checks where practical.

- Seam: Web detector preview
- Behaviour verified: Dataset Curator can manually run the preview, see model detections overlaid distinctly from human markers, see non-user-facing stub provenance, and avoid stale boxes when changing crop/bee or after failure.
- Test style: Playwright browser acceptance.

## Data Shape

Minimum endpoint:

- `POST /v1/training-crops/{training_crop_id}/varroa-review-candidates/{bee_annotation_id}/detector-preview`

Minimum request body:

- `workspace_id`

Internal adapter request contract:

- `VarroaDetectorRequest`
  - `workspace_id`
  - `inspection_photo_id`
  - `training_crop_id`
  - `bee_annotation_id`
  - `head_up_normalized_image_bytes`
  - `image_width_px`
  - `image_height_px`
  - `transform_version`
  - `transform_metadata`
  - `source_geometry_snapshot`

Minimum response model:

- `VarroaDetectorPreviewResponse`
  - `workspace_id`
  - `inspection_photo_id`
  - `training_crop_id`
  - `bee_annotation_id`
  - `model_purpose`: `varroa_detection`
  - `adapter_type`: `deterministic_stub` initially
  - `adapter_version`
  - `model_reference`
  - `status`: `completed` | `failed` | `not_assessed`
  - `failure_code`
  - `failure_message`
  - `not_assessed_reason`
  - `elapsed_ms`
  - `not_user_facing_reason`
  - `detections`
  - `detection_count`
  - `head_up_normalized_crop`
  - `caveat`

- `LikelyVarroaDetection`
  - `detection_id`
  - `x`
  - `y`
  - `width`
  - `height`
  - `confidence`
  - `coordinate_space`: `head_up_normalized_crop`
  - `source`: `deterministic_stub` initially

Rules:

- Detection geometry is normalized to the Head-Up Normalized Bee Crop coordinate frame.
- The first detector output uses a small axis-aligned box around likely mites; segmentation and oriented mite boxes are deferred.
- `detection_count` counts model detections, not human Varroa Markers.
- A completed zero-detection preview is not an active negative Varroa Review Outcome.
- `not_assessed` is used when the bee is ineligible or the normalized crop cannot be generated; it is not a negative Varroa result.
- `failed` is used for expected adapter-processing failures; the UI clears stale model-preview boxes.
- A detector preview result creates no detections in storage and changes no human evidence.

## Out Of Scope

- Training a Varroa Detector.
- Selecting, freezing, or governing a Varroa model-curation Dataset Version.
- Persisting model-preview detections as durable evidence.
- Auto-creating, updating, or copying model detections into Varroa Review Outcomes.
- AI-assisted human review provenance and workflow.
- Batch or frame-level mite counting across all eligible bees.
- Running Bee Localisation or Bee Orientation inference.
- Changing the Slice 0026 Photo-Visible Varroa Evidence Summary.
- Sampling-plan selection, confidence intervals, sequential stopping, Visible Varroa Rate calculation, or beekeeper-facing thresholds.
- HiveSight Advisor integration or treatment recommendation.
- Varroa Detector benchmark evaluation, promotion, or real model QA lane.
- Model Governance UI for Varroa Detection.
- Body-mask containment validation for model detections.

## Acceptance Criteria

- [ ] The Core API exposes a `POST` detector-preview endpoint for one Training Crop bee candidate.
- [ ] The Core API can run the injected deterministic stub Varroa Detector adapter for one eligible Head-Up Normalized Bee Crop.
- [ ] The deterministic stub returns one stable Likely Varroa Detection box with normalized location, size, confidence, elapsed time, and provenance in normal local dev and browser acceptance stub lanes.
- [ ] The response identifies workspace, model purpose, adapter type/version, model reference, input crop provenance, transform version, and non-user-facing caveats.
- [ ] Ineligible bees and unavailable normalized crops are not sent to the adapter and are reported as `not_assessed`, not negative.
- [ ] Expected adapter failure returns `status: failed`, clears stale preview output, and does not create detections or mutate human review evidence.
- [ ] Existing human Varroa Review Outcomes remain unchanged after running the model preview.
- [ ] Running the model preview does not change the photo-visible Varroa evidence summary.
- [ ] The Web UI shows paired clean and annotated Head-Up views for eligible bees, with shared zoom and shared pan.
- [ ] The Web UI provides explicit `Place marker` and `Pan` modes.
- [ ] Human markers and model-preview boxes appear only on the annotated view and use visually distinct styles.
- [ ] The Web UI lets a Dataset Curator manually run the preview for the selected eligible bee and clears stale preview output when the selected bee or crop changes.
- [ ] The UI and API make no Varroa Assessment, Visible Varroa Rate, treatment, Advisor, benchmark, Model Governance, or promotion claim.
- [ ] Focused service/API tests, API-level BDD, browser acceptance, Web type-check, and `pnpm verify:slice` pass before implementation closeout.

## Open Questions

- None after Slice 0027 grilling and acceptance signoff.
