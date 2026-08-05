# Vertical Slice 0026: Frame-Level Varroa Result Summary

Status: designed; acceptance scenarios signed off on 2026-08-05.

## Purpose

Produce the first photo-visible Varroa evidence summary from reviewed bee-level Varroa Review Outcomes.

This slice turns the reviewed Head-Up Normalized Bee Crop evidence from Slice 0025 into a countable result for one Inspection Photo: bees considered, bees assessed, bees with visible Varroa, visible mite marker count, unresolved bees, hidden/ineligible bees, completed crops included, unfinished crops excluded, and coverage. It creates the domain and API shape needed before a stubbed or real Varroa Detector adapter can count mites automatically and before HiveSight can expose treatment-relevant context to HiveSight Advisor.

This is not yet a real model-only Varroa Assessment, treatment trigger, HiveSight Advisor call, sampling-policy claim, or colony-level diagnosis.

## Source Inputs

- `CONTEXT.md`: Varroa Review, Varroa Review Outcome, Varroa Marker, Visible Varroa Rate, Varroa Sampling Plan, Inspection-Rate Sample, Result Evidence Breakdown, Review Completion, Determinate Varroa Coverage.
- `requirements/roadmap.md`: Varroa Detection, Statistical Inference And Beekeeper Results, Treatment And Advisor Integration.
- `requirements/varroa-evidence-methodology.md`: separation of model curation, evaluation, and inspection-rate estimation.
- `architecture/vertical-slice-0025-varroa-review-outcome-labelling.md`: single-bee Varroa Review Outcomes and Head-Up Normalized Bee Crop markers.
- `architecture/vertical-slice-0030-varroa-corpus-governance.md`: later model-curation corpus governance, deliberately not part of this slice.
- `architecture/parking-lot.md`: PARK-0030 Inspection-Rate Sampling Policy, PARK-0031 User-Facing Varroa Coverage Threshold, PARK-0032 Inadequate-Coverage Review Recovery, PARK-0051 Production Inspection-Rate Sampling And Field Calibration Implementation.

## Acceptance Scenarios

Acceptance signoff given on 2026-08-05.

```gherkin
Feature: Photo-visible Varroa evidence summary

  Scenario: Dataset Curator sees a photo-visible result from reviewed bee outcomes
    Given a Training Data Collection Inspection Photo has completed Training Crops
    And eligible complete bees on those crops have Varroa Review Outcomes
    When the Dataset Curator opens the Varroa Review stage
    Then HiveSight reports reviewed bee count, visible-Varroa bee count, visible mite marker count, active negative count, not-determined count, unreviewed eligible count, and ineligible bee count
    And HiveSight shows review completion and determinate Varroa coverage
    And HiveSight labels the result as photo-visible evidence, not a treatment recommendation

  Scenario: Visible mite marker count is separated from bee-positive count
    Given one reviewed bee has two Varroa markers
    And another reviewed bee has no visible Varroa
    When HiveSight calculates the photo-visible Varroa evidence summary
    Then HiveSight reports one visible-Varroa bee
    And HiveSight reports two visible mite markers
    And HiveSight does not treat marker count and positive bee count as the same measure

  Scenario: Unresolved or unreviewed bees reduce coverage
    Given a photo has eligible complete bees without determinate Varroa outcomes
    When HiveSight calculates the photo-visible Varroa evidence summary
    Then HiveSight includes those bees in the eligible denominator
    And HiveSight reports review completion and determinate Varroa coverage below 100%
    And HiveSight shows a coverage warning

  Scenario: Ineligible bees are excluded from the visible Varroa denominator
    Given a photo has partial visible bees or bees with unreliable orientation
    When HiveSight calculates the photo-visible Varroa evidence summary
    Then HiveSight reports them as ineligible or not assessed for Varroa
    And HiveSight excludes them from the eligible complete-bee denominator
    And HiveSight keeps their count visible in the evidence breakdown

  Scenario: Unfinished crops are disclosed but not counted
    Given a Training Data Collection Inspection Photo has one completed Training Crop
    And the same photo has one unfinished Training Crop
    When HiveSight calculates the photo-visible Varroa evidence summary
    Then HiveSight includes the completed crop in the evidence counts
    And HiveSight excludes the unfinished crop from bee, marker, positive, negative, and coverage counts
    And HiveSight shows that one unfinished crop was not included

  Scenario: Advisor context is available only as evidence, not advice
    Given a photo has a photo-visible Varroa evidence summary with at least one determinate eligible bee outcome
    When an integration client checks whether Advisor-ready Varroa context exists
    Then HiveSight reports that Varroa evidence context is available with caveats
    And HiveSight does not produce a treatment recommendation
```

## User Path

Given a Dataset Curator has reviewed Varroa evidence for bees on a selected Training Data Collection Inspection Photo,
When they open the Varroa Review stage,
Then HiveSight shows the current countable photo-visible Varroa evidence for that uploaded photo and the coverage caveats needed before any later detector or Advisor integration consumes it.

## Preconditions

- The selected User has Dataset Curator capability.
- Workspace Data Use Agreement requirements remain enforced for training-data evidence.
- The source Inspection has intent `training_data_collection`.
- The source Inspection Photo has at least one completed Training Crop with bee annotations.
- If the same Inspection Photo has multiple completed Training Crops, the summary aggregates all of them.
- Unfinished Training Crops from the same Inspection Photo are disclosed as excluded caveats but do not contribute to the main counts or percentages.
- Varroa Review Outcomes may be human-created from Slice 0025. A later slice may add model-created or AI-assisted-reviewed outcomes.
- Only eligible complete visible bees with reliable head orientation count in the primary Varroa denominator.
- `no_visible_varroa` is an active negative outcome.
- `not_determined` counts as reviewed for review-completion purposes but not as determinate evidence.
- Advisor-ready context is available with caveats when the summary has at least one determinate eligible bee outcome. This does not imply treatment advice.

## End-To-End Behaviour

Core API exposes a photo-visible Varroa evidence summary for one Inspection Photo. The result is derived live from current completed Training Crops attached to that photo and their current Varroa Review Outcomes.

The summary reports:

- source Inspection Photo id and human-readable filename;
- total completed Training Crops considered;
- unfinished Training Crops from the same photo excluded from the calculation;
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

The Web UI shows this summary inside the Training Inspection Workflow's Varroa Review stage. The first UI should be a compact summary card rather than a separate page. It should make the evidence breakdown visible without implying treatment advice.

The result has an Advisor-facing shape, but this slice does not call HiveSight Advisor. If an integration client asks whether this photo has treatment-relevant Varroa context, HiveSight can answer with the summary and caveats when at least one determinate eligible bee outcome exists, or with "not available" when no determinate evidence exists.

The first calculation is derived on demand. It is not yet an immutable, signed-off Varroa Assessment record. A later slice may persist model-only or human-reviewed result revisions.

## Layers Touched

- Web UI: Add a photo-visible Varroa evidence summary card inside the Varroa Review stage for the selected Inspection Photo or selected Training Crop's source photo, showing counts, coverage, unfinished-crop caveats, and no-advice language.
- Core API: Add a read endpoint to calculate the current photo-visible Varroa evidence summary for one Inspection Photo.
- Analysis Service: Not touched.
- Storage: No new durable table in this slice; derived from Training Crops, Bee Annotations, and Varroa Review Outcomes already persisted.
- Queue or async boundary: Not touched.
- Contracts: Add `FrameLevelVarroaResultSummary` response shape and an Advisor-ready availability flag without calling Advisor.
- Observability: Log summary calculation with workspace id, inspection photo id, eligible bee count, determinate coverage, and readiness state.

## Test Seams

- Seam: Photo-visible Varroa evidence summary calculation
- Behaviour verified: positive bees, marker count, active negatives, not-determined, unreviewed, ineligible, completed-crop aggregation, unfinished-crop caveats, review completion, and determinate coverage are counted correctly.
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
  - `unfinished_training_crop_count`
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
- `advisor_context_available` is true only when `determinate_eligible_bee_count > 0`.
- Percentages are zero when `eligible_complete_bee_count` is zero.

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
- UI language such as high, medium, low, safe, treat, treatment advised, or threshold crossed.

## Acceptance Criteria

- [ ] The Core API can calculate a photo-visible Varroa evidence summary from existing Varroa Review Outcomes for one Inspection Photo.
- [ ] The summary aggregates all completed Training Crops for the selected Inspection Photo and no crops from other photos.
- [ ] Unfinished Training Crops from the same photo are disclosed as excluded caveats but do not affect bee, marker, positive, negative, or coverage counts.
- [ ] The summary separates visible-Varroa bee count from visible mite marker count.
- [ ] The summary reports active negatives, `not_determined`, unreviewed eligible bees, and ineligible/not-assessed bees separately.
- [ ] The summary reports Review Completion and Determinate Varroa Coverage.
- [ ] The Web UI shows the summary and caveat inside the Varroa Review stage for the selected Training Inspection photo.
- [ ] HiveSight exposes whether the summary is Advisor-context available with caveats when at least one determinate eligible bee exists, without calling HiveSight Advisor.
- [ ] The UI and API state that this is photo-visible evidence, not treatment advice, and do not use treatment-threshold language.
- [ ] Focused Core API tests, API-level BDD, browser acceptance, Web type-check, and `pnpm verify:slice` pass before implementation closeout.

## Open Questions

- None after Slice 0026 grilling. Acceptance scenarios still require explicit signoff before implementation.
