# Vertical Slice 0026: Frame-Level Varroa Result Summary

Status: designed; acceptance scenarios pending signoff.

## Purpose

Produce the first frame/photo-level Varroa evidence summary from reviewed bee-level Varroa Review Outcomes.

This slice turns the reviewed Head-Up Normalized Bee Crop evidence from Slice 0025 into a countable result for one Inspection Photo: bees considered, bees assessed, bees with visible Varroa, visible mite marker count, unresolved bees, hidden/ineligible bees, and coverage. It creates the domain and API shape needed before a stubbed or real Varroa Detector adapter can count mites automatically and before HiveSight can expose treatment-relevant context to HiveSight Advisor.

This is not yet a real model-only Varroa Assessment, treatment trigger, HiveSight Advisor call, sampling-policy claim, or colony-level diagnosis.

## Source Inputs

- `CONTEXT.md`: Varroa Review, Varroa Review Outcome, Varroa Marker, Visible Varroa Rate, Varroa Sampling Plan, Inspection-Rate Sample, Result Evidence Breakdown, Review Completion, Determinate Varroa Coverage.
- `requirements/roadmap.md`: Varroa Detection, Statistical Inference And Beekeeper Results, Treatment And Advisor Integration.
- `requirements/varroa-evidence-methodology.md`: separation of model curation, evaluation, and inspection-rate estimation.
- `architecture/vertical-slice-0025-varroa-review-outcome-labelling.md`: single-bee Varroa Review Outcomes and Head-Up Normalized Bee Crop markers.
- `architecture/vertical-slice-0030-varroa-corpus-governance.md`: later model-curation corpus governance, deliberately not part of this slice.
- `architecture/parking-lot.md`: PARK-0030 Inspection-Rate Sampling Policy, PARK-0031 User-Facing Varroa Coverage Threshold, PARK-0032 Inadequate-Coverage Review Recovery, PARK-0051 Production Inspection-Rate Sampling And Field Calibration Implementation.

## Draft Acceptance Scenarios

Pending acceptance signoff.

```gherkin
Feature: Frame-level Varroa result summary

  Scenario: Dataset Curator sees a frame-level result from reviewed bee outcomes
    Given a Training Data Collection Inspection Photo has completed Training Crops
    And eligible complete bees on those crops have Varroa Review Outcomes
    When the Dataset Curator opens the frame-level Varroa result summary
    Then HiveSight reports reviewed bee count, visible-Varroa bee count, visible mite marker count, active negative count, not-determined count, unreviewed eligible count, and ineligible bee count
    And HiveSight shows review completion and determinate Varroa coverage
    And HiveSight labels the result as reviewed photo-visible evidence, not a treatment recommendation

  Scenario: Visible mite marker count is separated from bee-positive count
    Given one reviewed bee has two Varroa markers
    And another reviewed bee has no visible Varroa
    When HiveSight calculates the frame-level Varroa result summary
    Then HiveSight reports one visible-Varroa bee
    And HiveSight reports two visible mite markers
    And HiveSight does not treat marker count and positive bee count as the same measure

  Scenario: Unresolved or unreviewed bees reduce coverage
    Given a frame has eligible complete bees without determinate Varroa outcomes
    When HiveSight calculates the frame-level Varroa result summary
    Then HiveSight includes those bees in the eligible denominator
    And HiveSight reports review completion and determinate Varroa coverage below 100%
    And HiveSight shows a coverage warning

  Scenario: Ineligible bees are excluded from the visible Varroa denominator
    Given a frame has partial visible bees or bees with unreliable orientation
    When HiveSight calculates the frame-level Varroa result summary
    Then HiveSight reports them as ineligible or not assessed for Varroa
    And HiveSight excludes them from the eligible complete-bee denominator
    And HiveSight keeps their count visible in the evidence breakdown

  Scenario: Advisor context remains unavailable until a frame-level result exists
    Given an Inspection Photo has no calculated frame-level Varroa result summary
    When an integration client requests Advisor-ready Varroa context for that photo
    Then HiveSight returns that no treatment-relevant Varroa result is available
    And HiveSight does not produce a treatment recommendation
```

## User Path

Given a Dataset Curator has reviewed Varroa evidence for bees on a selected Training Data Collection Inspection Photo,
When they open the frame-level Varroa result summary,
Then HiveSight shows the current countable Varroa evidence for that photographed frame and the coverage caveats needed before any later detector or Advisor integration consumes it.

## Preconditions

- The selected User has Dataset Curator capability.
- Workspace Data Use Agreement requirements remain enforced for training-data evidence.
- The source Inspection has intent `training_data_collection`.
- The source Inspection Photo has at least one completed Training Crop with bee annotations.
- Varroa Review Outcomes may be human-created from Slice 0025. A later slice may add model-created or AI-assisted-reviewed outcomes.
- Only eligible complete visible bees with reliable head orientation count in the primary Varroa denominator.
- `no_visible_varroa` is an active negative outcome.
- `not_determined` counts as reviewed for review-completion purposes but not as determinate evidence.

## End-To-End Behaviour

Core API exposes a frame-level Varroa result summary for one Inspection Photo. The result is derived from current completed Training Crops attached to that photo and their current Varroa Review Outcomes.

The summary reports:

- source Inspection Photo id and human-readable filename;
- total completed Training Crops considered;
- eligible complete visible bee count;
- reviewed eligible bee count;
- determinate eligible bee count;
- visible-Varroa bee count;
- active negative bee count;
- not-determined bee count;
- unreviewed eligible bee count;
- ineligible or not-assessed bee count;
- visible mite marker count;
- review completion percentage;
- determinate Varroa coverage percentage;
- evidence source: `human_reviewed_model_curation` in this slice;
- result caveat and readiness state.

The Web UI shows this summary inside the Training Inspection Workflow near Varroa Review. The first UI may be a compact summary card rather than a separate page. It should make the evidence breakdown visible without implying treatment advice.

The result has an Advisor-facing shape, but this slice does not call HiveSight Advisor. If an integration client asks whether this photo has treatment-relevant Varroa context, HiveSight can answer with the summary and caveats when present, or with "not available" when no frame-level result exists.

The first calculation is derived on demand. It is not yet an immutable, signed-off Varroa Assessment record. A later slice may persist model-only or human-reviewed result revisions.

## Layers Touched

- Web UI: Add a frame-level Varroa result summary card for the selected Inspection Photo or selected Training Crop's source photo, showing counts, coverage, and caveat language.
- Core API: Add a read endpoint to calculate the current frame-level Varroa result summary for one Inspection Photo.
- Analysis Service: Not touched.
- Storage: No new durable table in this slice; derived from Training Crops, Bee Annotations, and Varroa Review Outcomes already persisted.
- Queue or async boundary: Not touched.
- Contracts: Add `FrameLevelVarroaResultSummary` response shape and an Advisor-ready availability flag without calling Advisor.
- Observability: Log summary calculation with workspace id, inspection photo id, eligible bee count, determinate coverage, and readiness state.

## Test Seams

- Seam: Frame-level Varroa summary calculation
- Behaviour verified: positive bees, marker count, active negatives, not-determined, unreviewed, ineligible, review completion, and determinate coverage are counted correctly.
- Test style: focused Core API/service tests and API-level BDD.

- Seam: Advisor-ready availability contract
- Behaviour verified: the API distinguishes "summary available with caveats" from "no treatment-relevant Varroa context yet" without generating treatment advice.
- Test style: focused Core API tests.

- Seam: Web result summary
- Behaviour verified: Dataset Curator can see the summary and caveat from the selected Training Inspection Workflow without confusing it with a treatment recommendation.
- Test style: Playwright browser acceptance.

## Data Shape

Minimum response model:

- `FrameLevelVarroaResultSummary`
  - `workspace_id`
  - `inspection_id`
  - `inspection_photo_id`
  - `source_image_filename`
  - `source_intent`
  - `completed_training_crop_count`
  - `eligible_complete_bee_count`
  - `reviewed_eligible_bee_count`
  - `determinate_eligible_bee_count`
  - `visible_varroa_bee_count`
  - `active_negative_bee_count`
  - `not_determined_bee_count`
  - `unreviewed_eligible_bee_count`
  - `ineligible_or_not_assessed_bee_count`
  - `visible_mite_marker_count`
  - `review_completion_percent`
  - `determinate_varroa_coverage_percent`
  - `evidence_source`
  - `readiness_state`: `not_available` | `partial_evidence` | `complete_reviewed_evidence`
  - `advisor_context_available`
  - `caveats`

Derived rules:

- `reviewed_eligible_bee_count = visible_varroa_bee_count + active_negative_bee_count + not_determined_bee_count`
- `determinate_eligible_bee_count = visible_varroa_bee_count + active_negative_bee_count`
- `review_completion_percent = reviewed_eligible_bee_count / eligible_complete_bee_count`
- `determinate_varroa_coverage_percent = determinate_eligible_bee_count / eligible_complete_bee_count`
- `visible_mite_marker_count` is the sum of Varroa Markers on `visible_varroa_present` outcomes.

## Out Of Scope

- Running a Varroa Detector adapter.
- Creating model-generated Varroa Review Outcomes.
- Training or benchmarking a Varroa Detector.
- Varroa Corpus Governance and Varroa Corpus Curation Decisions.
- Gold-Standard Full-Frame Corpus construction.
- Sampling-plan selection, confidence intervals, sequential stopping, or a statistically defended Visible Varroa Rate.
- Persisted Varroa Assessment result revisions.
- HiveSight Advisor remote call, treatment recommendation, treatment course, or treatment history.
- Beekeeper-facing treatment/action thresholds.

## Acceptance Criteria

- [ ] The Core API can calculate a frame/photo-level Varroa result summary from existing Varroa Review Outcomes.
- [ ] The summary separates visible-Varroa bee count from visible mite marker count.
- [ ] The summary reports active negatives, `not_determined`, unreviewed eligible bees, and ineligible/not-assessed bees separately.
- [ ] The summary reports Review Completion and Determinate Varroa Coverage.
- [ ] The Web UI shows the summary and caveat for the selected Training Inspection photo.
- [ ] HiveSight exposes whether the summary is Advisor-context available without calling HiveSight Advisor.
- [ ] The UI and API state that this is photo-visible evidence, not treatment advice.
- [ ] Focused Core API tests, API-level BDD, browser acceptance, Web type-check, and `pnpm verify:slice` pass before implementation closeout.

## Open Questions

- Should the first summary be scoped to one Inspection Photo only, or also roll up across all photos in the Inspection in the same slice?
- Should `advisor_context_available` require full determinate coverage, or merely at least one determinate positive/negative result with caveats?
- Should this slice use the term `frame-level` in UI copy, or should user-facing copy say `photo-level` until real frame identity is modelled more strongly?
