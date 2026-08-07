# Vertical Slice 0033: Varroa Photo Analysis Evidence And Adapter Readiness

Status: implemented; focused checks and `pnpm verify:slice` passed on 2026-08-07.

## Purpose

Make the Varroa Detector runtime path safely replaceable and persist auditable Photo Analysis evidence without choosing or training the first real Varroa model in this slice.

HiveSight already has a deterministic stub Varroa Detector adapter and a transient frame mite counting workflow. Slice 0033 adds the configuration, readiness, safety, QA lane, and persistence needed for a later real detector to be plugged into the same analysis path. The first replaceable non-stub shape is a Core API local command adapter: HiveSight sends one Head-Up Normalized Bee Crop plus provenance to a configured local command, validates the returned likely mite detections, and persists the resulting Photo Analysis run and per-bee analysis evidence.

This slice is readiness work for the real beekeeper flow, but it deliberately stops before the full one-click inspection-page workflow. The immediate follow-on slice should build the beekeeper-facing Analyze Photo action that runs Bee Localisation, Bee Orientation, and Varroa Detection as one operation. Slice 0033 makes that follow-on possible without hiding adapter ambiguity or losing evidence history.

## Source Inputs

- `CONTEXT.md`: Varroa Detector, Head-Up Normalized Bee Crop, Likely Varroa Detection, Frame-Level Varroa Result Summary, Model Purpose.
- `requirements/model-requirements.md`: MR-002 Varroa Detection, MR-003 Detection Association, MR-004 Complete Bee Denominator, MR-006 Headline Varroa Numerator, MR-007 Additional Varroa Evidence, MR-030A End-To-End Pipeline Evaluation Before Promotion.
- `requirements/varroa-evidence-methodology.md`: Varroa Detector development and component-evaluation methodology.
- `architecture/domain-model.md`: Varroa Detection and Frame Mite Count domain boundaries.
- `architecture/vertical-slice-0027-varroa-detector-adapter-seam.md`: existing deterministic stub single-bee detector preview seam.
- `architecture/vertical-slice-0028-frame-mite-counting-workflow.md`: existing frame mite count workflow over eligible Head-Up crops.
- `architecture/vertical-slice-0029-advisor-varroa-context-api.md`: downstream context path that consumes model-assisted frame mite count evidence.
- `architecture/acceptance-catalogue-inventory.md`: remaining legacy Gherkin migration debt for the Varroa Detector adapter seam.
- `requirements/roadmap.md`: Legacy Core API Gherkin Catalogue Cleanup and model-evidence direction.

## Draft Acceptance Scenarios

These scenarios were accepted and implemented.

```gherkin
@api
Feature: Varroa Photo Analysis evidence and adapter readiness

  Scenario: Default development configuration remains deterministic and clearly labelled
    Given HiveSight is using the default Varroa Detector adapter configuration
    When a developer runs a Varroa Detector preview for one eligible Head-Up Normalized Bee Crop
    Then HiveSight uses the deterministic stub Varroa Detector adapter
    And HiveSight returns deterministic stub adapter provenance
    And HiveSight labels the detections as non-user-facing stub evidence

  Scenario: Configuring a real adapter never silently falls back to the stub
    Given HiveSight is configured to use the local command Varroa Detector adapter
    But no runnable Varroa Detector command is configured
    When a developer runs a Varroa Detector preview for one eligible Head-Up Normalized Bee Crop
    Then HiveSight returns a detector preview status of failed
    And HiveSight reports that the configured Varroa Detector adapter is unavailable
    And HiveSight does not return deterministic stub detections

  Scenario: Local command adapter contract is explicit and versioned
    Given HiveSight is configured to use a local command Varroa Detector adapter
    And the command receives a JSON request on stdin with contract version "varroa_detector_command_v1"
    When the command returns a JSON response on stdout without contract version "varroa_detector_command_v1"
    Then HiveSight fails the detector call
    And HiveSight reports a Varroa Detector contract error
    And HiveSight does not treat the response as zero mites

  Scenario: Local command adapter detections flow through the detector response shape
    Given HiveSight is configured to use a local command Varroa Detector adapter
    And the command returns a completed response with two normalized likely Varroa detections for one Head-Up Normalized Bee Crop
    When a developer runs a Varroa Detector preview for that bee
    Then HiveSight reports two Likely Varroa Detections
    And each detection has normalized location, size, confidence, coordinate space, and source
    And HiveSight reports local command adapter provenance instead of deterministic stub provenance

  Scenario: Invalid command detections fail the whole bee detector call
    Given HiveSight is configured to use a local command Varroa Detector adapter
    And the command returns a completed response with one valid detection and one detection outside the normalized bee-crop bounds
    When HiveSight analyses that bee with the Varroa Detector
    Then HiveSight fails the whole bee detector call
    And HiveSight records the invalid adapter response as a detector failure
    And HiveSight does not keep the valid detection as partial bee evidence

  Scenario: Photo Analysis persists frame-level and per-bee evidence
    Given a Varroa assessment photo has three eligible Head-Up Normalized Bee Crops
    And HiveSight is configured to use a local command Varroa Detector adapter
    And two bee detector calls complete
    And one bee detector call times out
    When HiveSight runs Varroa Photo Analysis for that photo
    Then HiveSight persists one Photo Analysis run for the photo
    And HiveSight persists one per-bee analysis record for each attempted eligible bee
    And the Photo Analysis status is partial
    And the result reports total detected bees, eligible bees, analysed bees, failed bees, and mites found

  Scenario: Photo Analysis with no usable bees is not acceptable evidence
    Given a Varroa assessment photo has no bees eligible for Varroa evaluation
    When HiveSight runs Varroa Photo Analysis for that photo
    Then HiveSight persists a Photo Analysis run with status no_usable_bees
    And HiveSight reports zero analysed bees
    And the Photo Analysis cannot be marked accepted
    And the Photo Analysis can be marked rejected or inconclusive with a note

  Scenario: Human review controls Advisor eligibility
    Given a persisted Photo Analysis run has status completed
    And the review status is unreviewed
    When HiveSight checks whether the Photo Analysis can be used as Advisor evidence
    Then HiveSight reports that the Photo Analysis is not eligible
    When the Beekeeper marks the Photo Analysis accepted
    Then HiveSight reports that the Photo Analysis is eligible for later Advisor evidence

  Scenario: Varroa detector readiness explains adapter availability
    Given HiveSight has a configured Varroa Detector adapter
    When a developer checks Varroa Detector readiness
    Then HiveSight reports the configured adapter type, adapter version, model reference, availability, database purpose, and any sanitized unavailable reason
    And HiveSight states whether the configured adapter is deterministic stub evidence or a replaceable non-stub adapter
    And HiveSight does not expose secrets or full local command paths

  Scenario: Explicit QA command exercises the configured Varroa detector path
    Given the Core API is running with a configured Varroa Detector adapter
    When a developer runs the Varroa Detector QA command
    Then the command checks adapter readiness
    And the command runs a single-crop detector contract smoke test through the configured adapter
    And the command runs a Photo Analysis path when suitable fixture data is available
    And the command prints adapter provenance, detection count, failure details, and explicit skip reasons
```

## User Path

Given HiveSight has Varroa assessment photo evidence and eligible Head-Up Normalized Bee Crops,
when HiveSight is configured with either the deterministic stub or a local command Varroa Detector adapter,
then detector preview and Photo Analysis use the configured adapter, report explicit readiness/provenance, persist auditable model evidence, and never pretend stub or malformed evidence is real accepted evidence.

## Preconditions

- Slice 0027 detector preview and Slice 0028 frame mite count are implemented.
- The immediate follow-on slice will add the beekeeper-facing one-click Analyze Photo workflow on the Varroa assessment inspection page.
- The default local/test path remains deterministic and fast.
- Real-adapter execution remains opt-in and outside the default `pnpm verify:slice` lane.
- The local command adapter contract is model-family-neutral; it can later wrap YOLO, PyTorch, ONNX, or another detector without changing HiveSight's Core API response shape.
- One uploaded photo is treated as one Photo Analysis evidence unit for this slice. Frame-side and multi-photo roll-up semantics remain a follow-on workflow/domain decision.

## End-To-End Behaviour

Add a Varroa Detector runtime adapter setting:

```text
HIVESIGHT_VARROA_DETECTOR_ADAPTER=deterministic_stub | local_command
```

Default remains `deterministic_stub`.

When `local_command` is selected, HiveSight requires a configured command path:

```text
HIVESIGHT_VARROA_DETECTOR_COMMAND=/path/to/varroa-detector-command
HIVESIGHT_VARROA_DETECTOR_MODEL_REFERENCE=<human-readable model/package reference>
```

The local command adapter writes the Head-Up Normalized Bee Crop bytes to a temporary file, sends a compact JSON request to the command over stdin, reads a JSON response from stdout, validates detections, and maps them into the existing `LikelyVarroaDetection` response shape. Stderr is diagnostic only.

The command adapter input includes:

- `contract_version = varroa_detector_command_v1`;
- workspace id;
- inspection photo id;
- training crop id;
- bee annotation id;
- Head-Up image path;
- image width and height;
- transform version and metadata;
- source geometry snapshot.

The command response includes:

- `contract_version = varroa_detector_command_v1`;
- `status = completed | failed`;
- adapter version;
- model reference;
- optional adapter answer id;
- detections with normalized `x`, `y`, `width`, `height`, `confidence`;
- optional failure code/message.

If `local_command` is selected but unavailable, HiveSight reports the configured adapter as unavailable and does not fall back to deterministic stub output. Detector preview returns `failed`; Photo Analysis records affected bee failures or whole-photo failure according to the rules in this slice.

Zero detections is only valid when the command returns an explicit successful completed response with the correct contract version, model provenance, and `detections: []`. Empty output, invalid JSON, missing contract version, invalid provenance, non-zero process exit, timeout, or malformed detections are adapter failures.

The local command adapter uses a short fixed per-bee timeout. A timed-out bee detector call is recorded as a per-bee failure. A Photo Analysis may complete as `partial` when every eligible bee was attempted and one or more bee detector calls failed. A Photo Analysis is `failed` when the photo analysis itself aborts or cannot produce a usable result. A Photo Analysis is `no_usable_bees` when analysis ran but no bees were eligible for Varroa evaluation.

Every Photo Analysis run is persisted as a separate evidence record. Reruns create new Photo Analysis runs rather than replacing previous evidence. Each run stores frame/photo-level counts, status, review status, note, timestamp, adapter/model provenance, command contract version, and per-bee analysis records. Per-bee analysis records store attempted/completed/failed status, detector detections, failure details, and the same structured model provenance.

Human review is deliberately photo-level only in this slice. Review status is separate from job status:

- `unreviewed`
- `accepted`
- `rejected`
- `inconclusive`
- `needs_expert_review`

Only `accepted` Photo Analysis evidence is eligible for a later Advisor/treatment evidence chain. Completed zero-mite results are not auto-accepted. Partial runs with recorded per-bee failures may be accepted, but the failed-bee count and incomplete-result warning remain part of the evidence forever. Failed or aborted runs and `no_usable_bees` runs cannot be accepted. If multiple accepted runs exist for the same photo, the user must explicitly select which one is used later; HiveSight must not silently choose the latest run.

Add a readiness endpoint, for example:

```text
GET /v1/model-runtime/varroa-detector/readiness
```

The readiness response reports adapter type, adapter version, model reference, availability, database purpose, whether output is deterministic-stub evidence, and any sanitized unavailable reason. It must not expose secrets or full local command paths.

Add a developer QA command:

```text
pnpm model:qa:varroa:detect
```

The command assumes the Core API is already running, checks readiness, runs a single-crop detector contract smoke test through the configured adapter, and runs a Photo Analysis path when suitable fixture data is available. Missing fixture data is reported as an explicit skip, not as a vague success. The command prints adapter provenance, detection count, failure details, and skip reasons, and exits non-zero if the configured adapter is unavailable or the detector path fails.

The default `pnpm verify:slice` continues to use deterministic stub behaviour and fake-command tests for strict contract handling. Real/non-stub adapter QA is explicit and opt-in, like the existing Bee Training real-adapter QA lanes.

## Layers Touched

- Web UI: add only minimal Photo Analysis evidence/review surfacing if needed to prove persisted run review; the full one-click inspection-page Analyze Photo workflow belongs in the immediate follow-on slice.
- Core API: add Varroa Detector adapter settings, adapter registry/wiring, local command adapter, readiness endpoint, Photo Analysis run persistence, per-bee analysis persistence, review updates, and validation around command responses.
- Analysis Service: not touched; local command is a replaceable first runtime boundary before a later service/queue boundary.
- Storage: add persisted Photo Analysis run and per-bee analysis evidence records.
- Queue or async boundary: not touched; the command adapter is synchronous for the first readiness slice.
- Contracts: add local command request/response contract, readiness response model, Photo Analysis run response model, per-bee analysis response model, and photo-level review update model; existing detector preview API response shape remains stable.
- Observability: log adapter readiness checks and command-adapter failures with adapter type/version/model reference, workspace id where available, elapsed time, and failure code.
- Developer tooling: add `pnpm model:qa:varroa:detect`.
- Roadmap: keep remaining legacy Core API Gherkin cleanup visible; migrate only Varroa Detector/Photo Analysis Gherkin scenarios impacted by this slice.

## Test Seams

- Seam: adapter registry and settings
- Behaviour verified: default config selects deterministic stub; `local_command` selects the command adapter; unavailable configured adapters do not fall back to stub.
- Test style: focused Core API/settings tests.

- Seam: local command adapter
- Behaviour verified: command request is JSON on stdin and includes Head-Up crop path, provenance, and contract version; command response is JSON on stdout and must include the matching contract version; detections are validated and mapped into `LikelyVarroaDetection`; malformed output becomes an adapter failure.
- Test style: focused workflow tests with a temporary fake command.

- Seam: detector preview
- Behaviour verified: preview uses the configured adapter and preserves adapter provenance; unavailable real adapter returns failed with no stub detections.
- Test style: API-level BDD and focused API tests.

- Seam: Photo Analysis persistence
- Behaviour verified: a photo run persists status, counts, review state, provenance, per-bee outcomes, and rerun history; per-bee failures produce partial photo results when every eligible bee was attempted.
- Test style: focused Core API tests and API-level BDD.

- Seam: Photo Analysis review
- Behaviour verified: accepted is the only Advisor-eligible review status; partial runs can be accepted with permanent failure evidence; failed and no_usable_bees runs cannot be accepted.
- Test style: API-level BDD and focused workflow tests.

- Seam: readiness and QA command
- Behaviour verified: readiness reports adapter availability and caveats; QA command prints adapter provenance/detection count and fails clearly when unavailable.
- Test style: focused API tests and Node script tests; real adapter execution remains opt-in/manual until an actual model package exists.

- Seam: acceptance catalogue migration
- Behaviour verified: impacted Varroa Detector/Photo Analysis behaviours live in the capability-based acceptance catalogue and run through the supported seam tags.
- Test style: catalogue feature plus Core API binding.

## Data Shape

New settings:

- `HIVESIGHT_VARROA_DETECTOR_ADAPTER`: `deterministic_stub` | `local_command`
- `HIVESIGHT_VARROA_DETECTOR_COMMAND`: required when adapter is `local_command`
- `HIVESIGHT_VARROA_DETECTOR_MODEL_REFERENCE`: optional human-readable model/package reference for non-stub adapters

New readiness response:

- `VarroaDetectorReadinessResponse`
  - `adapter_type`
  - `adapter_version`
  - `model_reference`
  - `available`
  - `unavailable_reason`
  - `database_purpose`
  - `deterministic_stub_evidence`
  - `replaceable_non_stub_adapter`
  - sanitized `last_validation_error`

Local command request:

- `contract_version`
- `workspace_id`
- `inspection_photo_id`
- `training_crop_id`
- `bee_annotation_id`
- `head_up_normalized_image_path`
- `image_width_px`
- `image_height_px`
- `transform_version`
- `transform_metadata`
- `source_geometry_snapshot`

Local command response:

- `contract_version`
- `status`
- `adapter_version`
- `model_reference`
- `answer_id`
- `detections`
- `failure_code`
- `failure_message`

Detection item:

- `x`
- `y`
- `width`
- `height`
- `confidence`
- `source`

Validation rules:

- coordinates and sizes must be finite normalized numbers in the expected range;
- confidence must be a finite normalized number;
- malformed output is an adapter failure, not an empty negative result;
- any invalid detection fails the whole bee detector call;
- zero detections is valid completed model output, not a human active negative.
- zero detections requires explicit `status = completed`, matching contract version, model provenance, and `detections: []`.

Photo Analysis run:

- `id`
- `workspace_id`
- `inspection_id`
- `inspection_photo_id`
- `status`: `running` | `completed` | `partial` | `failed` | `no_usable_bees`
- `review_status`: `unreviewed` | `accepted` | `rejected` | `inconclusive` | `needs_expert_review`
- `review_note`
- `total_detected_bees`
- `eligible_bees`
- `analysed_bees`
- `failed_bees`
- `mites_found`
- `mite_ratio_basis = analysed_eligible_bees`
- `adapter_type`
- `adapter_version`
- `model_reference`
- `command_contract_version`
- `started_at`
- `completed_at`
- `failure_code`
- `failure_message`

Per-bee Photo Analysis record:

- `id`
- `photo_analysis_run_id`
- `bee_annotation_id`
- `status`: `completed` | `failed`
- `mites_found`
- detections in normalized Head-Up crop coordinates
- `adapter_type`
- `adapter_version`
- `model_reference`
- `command_contract_version`
- optional detector `answer_id`
- `failure_code`
- `failure_message`
- capped sanitized raw response/error payload only for failed or invalid adapter calls

## Out Of Scope

- Training a Varroa Detector.
- Selecting the final Varroa model architecture.
- Adding a real bundled model dependency.
- Benchmarking or promoting a Varroa Detector.
- Per-bee human correction of Varroa Detector outputs.
- Adding missed-mite correction markers from the beekeeper UI.
- Combining multiple photos into a colony, hive, frame, or inspection-level Varroa estimate.
- Defining frame-side semantics such as Frame 1 Side A versus Frame 1 Side B.
- Building the full one-click inspection-page Analyze Photo workflow; this is the immediate follow-on slice.
- Triggering HiveSight Advisor.
- Moving the Varroa Detector runtime behind Analysis Service or a queue.
- Completing the full legacy Core API Gherkin migration.

## Acceptance Criteria

- [x] Default configuration still uses deterministic stub Varroa Detector output and labels it as non-user-facing stub evidence.
- [x] `HIVESIGHT_VARROA_DETECTOR_ADAPTER=local_command` selects a non-stub command adapter when a runnable command is configured.
- [x] A configured but unavailable local command adapter reports unavailable/failure and does not fall back to deterministic stub output.
- [x] Detector preview can return detections from a fake local command adapter through the existing `LikelyVarroaDetection` shape.
- [x] Local command request/response uses JSON over stdin/stdout with `contract_version = varroa_detector_command_v1` in both directions.
- [x] Malformed command output, invalid detections, missing provenance, non-zero exit, and timeout are reported as adapter failures, not as zero detections.
- [x] Zero detections is valid only from an explicit completed response with matching contract version, provenance, and `detections: []`.
- [x] Varroa Photo Analysis persists one run record and per-bee analysis records, including structured adapter/model provenance.
- [x] Rerunning Photo Analysis creates a new evidence run rather than replacing previous evidence.
- [x] Partial Photo Analysis runs record analysed bees, failed bees, and a permanent incomplete-result warning.
- [x] `no_usable_bees` Photo Analysis runs cannot be marked accepted.
- [x] Only accepted Photo Analysis runs are eligible for later Advisor evidence.
- [x] Readiness endpoint reports adapter type, version, model reference, availability, database purpose, and stub/non-stub caveat without exposing secrets or full command paths.
- [x] `pnpm model:qa:varroa:detect` checks readiness, runs a single-crop contract smoke test, and runs a Photo Analysis path when fixture data is available.
- [x] Default fast tests and `pnpm verify:slice` do not require a real Varroa model, external model dependencies, or network access.
- [x] Impacted Varroa Detector/Photo Analysis Gherkin scenarios are migrated into the capability-based acceptance catalogue.
- [x] Roadmap keeps the remaining legacy Core API Gherkin catalogue cleanup visible.

## Open Questions

None blocking design signoff.

The slice intentionally chooses a local command adapter boundary rather than a model-family-specific implementation. A later Varroa model slice can decide whether the command wraps YOLO, PyTorch, ONNX, or another detector.
