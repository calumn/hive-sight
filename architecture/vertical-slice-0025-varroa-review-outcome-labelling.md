# Vertical Slice 0025: Varroa Review Outcome Labelling

Status: designed; acceptance scenarios signed off on 2026-08-05.

## Purpose

Let a Dataset Curator create the first human-reviewed Varroa evidence on individual Head-Up Normalized Bee Crops.

Slices 0021-0024 establish reliable directed bee evidence, shared Bee Training Dataset Versions, real Bee Orientation training, and protected orientation benchmark evidence. Slice 0025 moves from bee evidence into Varroa evidence without pretending the live model pipeline exists yet. It uses existing human-reviewed reliable complete bee ellipses to generate a head-up bee-relative review crop, then records an explicit Varroa Review Outcome:

- `visible_varroa_present`;
- `no_visible_varroa`;
- `not_determined`.

This is deliberately a model-curation slice. It creates active positive, active negative, unresolved, and triaged Varroa evidence for later Varroa Detector training and benchmark design. It does not train a Varroa Detector, run automated orientation inference, create a beekeeper-facing Varroa Assessment result, trigger HiveSight Advisor, or recommend treatment.

## Source Inputs

- `CONTEXT.md`: Varroa Review, Varroa Review Outcome, Varroa Marker, Varroa Review Suitability, Suspected Visible Varroa Cue, Likely Varroa Detection, Not Assessed For Varroa, Head-Up Normalized Bee Crop, Model-Curation Sample, Inspection-Rate Sample, Gold-Standard Full-Frame Corpus, Model Governance, Crop Governance.
- `requirements/model-requirements.md`: MR-002 Varroa Detection, MR-009 Varroa Annotation Shape, MR-009A Varroa Review Outcome, MR-017L Dataset Selection Method, MR-018C Separate Varroa Sampling Policies, MR-018D Model-Curation Sampling Method, MR-018E Varroa Review Strength, MR-018H Gold-Standard Full-Frame Corpus.
- `requirements/varroa-evidence-methodology.md`: Model-Curation Corpus, Full-Depth Annotation And Review Protocol, Model Training And Validation Sequence.
- `architecture/adr/0007-three-stage-bee-localisation-orientation-and-varroa-pipeline.md`: three-stage pipeline, Head-Up Normalized Bee Crop convention, active Varroa review outcomes, and first-corpus exclusion of unreliable orientation.
- `architecture/bee-orientation-classifier-design.md`: Head Up convention and transform/provenance requirements.
- `architecture/domain-model.md`: Bee Annotation triage cues, Head-Up Normalized Bee Crop, Varroa Review, and Varroa Marker.
- `architecture/parking-lot.md`: PARK-0028 Automated Bee Head Direction Prediction, PARK-0030 Inspection-Rate Sampling Policy, PARK-0038 Varroa Evidence Methodology, PARK-0052 Varroa Review Invalidation After Source Bee Geometry Changes.
- `requirements/roadmap.md`: Varroa Review Outcome Labelling and Orientation-Assisted Crop Normalisation.

## Signed-Off Acceptance Scenarios

These scenarios were accepted for Slice 0025 implementation signoff on 2026-08-05.

```gherkin
Feature: Varroa Review Outcome Labelling

  Scenario: Dataset Curator records Varroa triage cues during bee annotation
    Given a Training Crop has an editable visible bee ellipse
    When the Dataset Curator marks the bee as body occluded or hard to assess for Varroa review
    And the Dataset Curator flags suspected visible Varroa on that bee
    Then HiveSight saves the Varroa review suitability cue for the bee
    And HiveSight saves the suspected visible Varroa cue for the bee
    And HiveSight records who last updated those cues and when
    And HiveSight does not treat either cue as a Varroa Review Outcome

  Scenario: Dataset Curator opens a Head-Up Normalized Bee Crop for Varroa review
    Given a completed Training Crop contains a reliable complete visible bee ellipse
    When the Dataset Curator opens that bee for Varroa review
    Then HiveSight shows a Head-Up Normalized Bee Crop for the selected bee
    And HiveSight shows the source Training Crop and bee annotation provenance
    And HiveSight shows any Varroa triage cues recorded during bee annotation
    And HiveSight labels the review purpose as model curation
    And HiveSight shows that this is not a Varroa assessment

  Scenario: Dataset Curator records an active negative Varroa Review Outcome
    Given a Head-Up Normalized Bee Crop is open for Varroa review
    When the Dataset Curator records no visible Varroa
    Then HiveSight saves a Varroa Review Outcome of no_visible_varroa
    And HiveSight records zero Varroa markers
    And HiveSight labels the evidence as an active negative judgement

  Scenario: Dataset Curator records a visible Varroa outcome with marker evidence
    Given a Head-Up Normalized Bee Crop is open for Varroa review
    When the Dataset Curator places two mite markers and records visible Varroa present
    Then HiveSight saves a Varroa Review Outcome of visible_varroa_present
    And HiveSight records the mite markers in normalized bee-crop coordinates
    And HiveSight reports one visible-Varroa bee and two visible Varroa markers
    And HiveSight shows the markers when the review is reopened

  Scenario: Dataset Curator records an unresolved Varroa Review Outcome
    Given a Head-Up Normalized Bee Crop is open for Varroa review
    When the Dataset Curator records not determined with a note
    Then HiveSight saves a Varroa Review Outcome of not_determined
    And HiveSight does not treat the crop as negative training evidence
    And HiveSight keeps the crop visible as unresolved Varroa evidence

  Scenario: Ineligible bees cannot enter the first Varroa corpus
    Given a Training Crop contains a partial visible bee or an unreliable-orientation bee
    When the Dataset Curator reviews Varroa eligibility for that bee
    Then HiveSight explains that the bee is excluded from the first Head-Up Normalized Varroa corpus
    And HiveSight does not allow a Varroa Review Outcome to be saved for that bee in this slice

  Scenario: Visible Varroa Review requires marker evidence
    Given a Head-Up Normalized Bee Crop is open for Varroa review
    When the Dataset Curator tries to save visible Varroa present without a marker
    Then HiveSight blocks the save and explains that visible Varroa requires marker evidence

  Scenario: Not determined Varroa Review requires a note
    Given a Head-Up Normalized Bee Crop is open for Varroa review
    When the Dataset Curator tries to save not determined without a note
    Then HiveSight blocks the save and explains that not determined requires a note
```

## User Path

Given a Dataset Curator has a Training Data Collection Inspection with completed bee annotations and any annotation-time Varroa triage cues,
When they open the Varroa Review stage after Crop Governance and select a reliable complete visible bee,
Then HiveSight presents a head-up bee-relative crop and lets the curator actively record positive, active negative, or unresolved Varroa evidence with provenance.

## Preconditions

- The selected User has Dataset Curator capability.
- Workspace Data Use Agreement requirements remain enforced.
- The source Inspection has intent `training_data_collection`.
- The source Training Crop is completed, not excluded, and has reviewed bee ellipses.
- A bee is eligible for this first Varroa corpus only when:
  - `annotation_type` is `complete_visible_bee`;
  - Orientation Reliability is `reliable`;
  - source image bytes are available;
  - the bee can be transformed into a Head-Up Normalized Bee Crop.
- Partial visible bees and unreliable-orientation bees are visible as excluded/deferred evidence but cannot receive first-corpus Varroa Review Outcomes in this slice.
- Varroa Review is available only to Users with Dataset Curator capability.

## End-To-End Behaviour

The Training Inspection Workflow gains a new stage: `Varroa Review`, after Crop Governance and before Model Governance.

Bee Annotation gains two compact selected-bee triage controls:

- Varroa Review Suitability: `unassessed`, `appears_assessable`, or `body_occluded_or_hard_to_assess`.
- Suspected Visible Varroa Cue: boolean.

The cues are allowed on any visible bee annotation, including partial and unreliable-orientation bees. They are fast triage signals, not final Varroa evidence. They retain current values plus last-updated user/time provenance. They do not carry full history, do not require notes, and do not preselect a final Varroa Review Outcome.

For the selected Training Crop, HiveSight lists bee annotations by Varroa review eligibility:

- eligible reliable complete visible bees;
- excluded unreliable-orientation bees;
- excluded partial visible bees;
- already reviewed Varroa outcomes.
- annotation-time suitability and suspected-visible-Varroa cues.

The default ordering is:

1. suspected visible Varroa cues;
2. unreviewed eligible bees;
3. reviewed eligible bees;
4. ineligible/deferred bees.

Simple filters for all, suspected, unreviewed, reviewed, and ineligible are optional if low-cost; the default ordering is required.

When the curator selects an eligible bee, HiveSight derives a Head-Up Normalized Bee Crop using the human-reviewed directed ellipse:

1. Load the source image bytes.
2. Extract the bee-relative region with the same margin convention used by Bee Orientation packages where practical.
3. Rotate the crop so the reviewed centre-to-head direction points upward.
4. Resize or pad to a stable review display size.
5. Preserve transform metadata so marker coordinates can be related back to source evidence.

The normalized crop is generated on demand through an image/content endpoint for the selected bee. It is not returned inline in candidate lists, not stored as a derived image artifact, and not downloadable/exportable in this slice. The UI shows the normalized crop as the primary review surface, with simple zoom. A secondary original crop context shows the source bee ellipse for sanity checking, but marker placement occurs only on the normalized crop.

The curator can then record one Varroa Review Outcome:

- `visible_varroa_present`: requires one or more mite point markers in normalized crop coordinates.
- `no_visible_varroa`: records an explicit active negative judgement with zero markers.
- `not_determined`: records that the crop was reviewed but cannot support a positive or negative label; it requires a note and zero markers.

Markers are points, not boxes. Multiple point markers are allowed. Marker coordinates are normalized 0-1 crop coordinates, inclusive, rounded to a stable precision such as four decimal places. The UI supports adding markers, selecting markers, deleting selected markers, and showing a compact marker list. Marker dragging, per-marker notes, tight boxes, body-mask containment validation, and segmentation masks are deferred.

Adding a first marker may visually suggest the positive outcome, but the curator must explicitly save an outcome. Deleting all markers does not silently convert a review to negative. Invalid outcome/marker combinations are blocked in both UI and Core API.

Saved reviews are resumable and editable as the current single-curator review for that bee. Reopening the same bee shows the saved outcome, notes, and marker positions. There is one current Varroa Review Outcome per Workspace and Bee Annotation; future immutable revisions are deferred. Existing reviews remain visible read-only when the source crop is reopened or temporarily ineligible, but create/update is blocked until the source crop and bee are eligible again.

The review record is labelled as:

- Sampling Purpose: `model_curation`;
- Dataset Selection Method: `human_selected`;
- Review Strength: `single_curator_review`;
- Annotation Source: `human_from_scratch`.

Those labels are intentionally conservative. The source Bee Annotation's provenance remains separately visible, including when the bee ellipse came from a human-reviewed Model Candidate suggestion. Blind Independent Review, adjudication, benchmark-strength review, sampling-plan selection, Varroa Dataset Role assignment, and immutable review revision history remain later slices.

The crop-level Varroa Review summary shows curation progress only:

- eligible bees;
- reviewed bees;
- visible-Varroa bees;
- no-visible-Varroa bees;
- not-determined bees;
- total markers;
- suspected-visible-Varroa cues;
- hard-to-assess cues;
- ineligible/deferred bees.

It is labelled as model-curation summary only, not a Varroa Assessment or Visible Varroa Rate. No additional acknowledgement is required.

## Layers Touched

- Web UI: Add selected-bee Varroa triage controls in Bee Annotation; add a Varroa Review stage for eligible bees in a Training Data Collection inspection, including normalized crop preview, original crop context, simple zoom, outcome controls, marker placement/deletion/list, notes, saved-state display, progress summary, and ineligible-bee explanations.
- Core API: Add endpoints to list Varroa review candidates for a Training Crop, fetch a Head-Up Normalized Bee Crop preview, create/update a Varroa Review Outcome, and return saved marker evidence.
- Analysis Service: Not touched.
- Storage: Add proper persistence for Varroa Review Outcome and Varroa marker records linked to Workspace, Inspection Photo, Training Crop, Bee Annotation, source image, and transform metadata; add Bee Annotation cue fields with lightweight last-updated provenance. Implement both in-memory and Postgres-backed paths with a migration.
- Queue or async boundary: Not touched; this slice is synchronous curation, not model inference.
- Contracts: Add explicit response models for Varroa review candidates, normalized crop preview metadata/image endpoint, triage cues, review outcome, and marker coordinates.
- Observability: Record lightweight structured review-created/review-updated and cue-updated events with workspace id, crop id, bee annotation id, outcome, marker count, user id, and transform version.

## Test Seams

- Seam: Varroa review candidate eligibility
- Behaviour verified: only reliable complete visible bees are eligible; partial and unreliable-orientation bees are excluded with explicit reasons.
- Test style: focused Core API tests and API-level BDD.

- Seam: Bee Annotation Varroa triage cues
- Behaviour verified: suitability and suspected-visible-Varroa cues can be set on visible bee annotations, persist with last-updated provenance, and do not become Varroa Review Outcomes.
- Test style: focused Core API tests and API-level BDD.

- Seam: Head-Up Normalized Bee Crop generation
- Behaviour verified: crop preview is generated from the source image and directed ellipse, with transform metadata and stable dimensions.
- Test style: service/workflow tests with a small fixture image.

- Seam: Varroa Review Outcome persistence
- Behaviour verified: positive outcomes require marker evidence; active negatives store zero markers; `not_determined` persists as unresolved and not negative; invalid marker/outcome combinations are rejected server-side.
- Test style: focused API tests and API-level BDD.

- Seam: UI Varroa review workflow
- Behaviour verified: Dataset Curator can open an eligible bee, save each outcome type, place and reopen marker evidence, and see ineligible-bee explanations.
- Test style: Playwright browser acceptance.

## Data Shape

Minimum new records or contract shapes:

- `HeadUpNormalizedBeeCropPreview`
  - `workspace_id`;
  - `inspection_photo_id`;
  - `training_crop_id`;
  - `bee_annotation_id`;
  - `annotation_type`;
  - `orientation_reliability`;
  - `image_width_px`;
  - `image_height_px`;
  - `transform_version`;
  - source crop bounds, rotation applied, margin, resize/pad policy;
  - source Bee Annotation geometry snapshot.

- Bee Annotation Varroa triage cues:
  - `varroa_review_suitability`: `unassessed` | `appears_assessable` | `body_occluded_or_hard_to_assess`;
  - `suspected_visible_varroa`: boolean;
  - `varroa_review_suitability_updated_by_user_id`;
  - `varroa_review_suitability_updated_at`;
  - `suspected_visible_varroa_updated_by_user_id`;
  - `suspected_visible_varroa_updated_at`.

- `VarroaReviewOutcome`
  - `varroa_review_outcome_id`;
  - `workspace_id`;
  - `inspection_photo_id`;
  - `training_crop_id`;
  - `bee_annotation_id`;
  - `outcome`: `visible_varroa_present` | `no_visible_varroa` | `not_determined`;
  - `sampling_purpose`: `model_curation`;
  - `dataset_selection_method`: `human_selected`;
  - `review_strength`: `single_curator_review`;
  - `annotation_source`: `human_from_scratch`;
  - `created_by_user_id`;
  - `created_at`;
  - `updated_by_user_id`;
  - `updated_at`;
  - `notes`;
  - `source_context_snapshot`;
  - `bee_annotation_geometry_snapshot`;
  - `training_crop_review_status_snapshot`;
  - `transform_metadata`.

- `VarroaMarker`
  - `varroa_marker_id`;
  - `varroa_review_outcome_id`;
  - marker type: `point` for this slice;
  - normalized coordinates `x`, `y` in the Head-Up Normalized Bee Crop.

Database constraints:

- One current Varroa Review Outcome per Workspace and Bee Annotation.
- Marker coordinates must be in the inclusive 0-1 range.
- `visible_varroa_present` requires one or more markers.
- `no_visible_varroa` and `not_determined` require zero markers.
- `not_determined` requires a note.

Suggested API error codes:

- `varroa_review_candidate_not_found`;
- `varroa_review_candidate_ineligible`;
- `visible_varroa_requires_marker`;
- `non_positive_varroa_outcome_requires_no_markers`;
- `not_determined_requires_note`;
- `varroa_marker_out_of_bounds`;
- `training_crop_not_complete_for_varroa_review`.

## Out Of Scope

- Varroa Detector training, inference, benchmark evaluation, or report.
- User-facing Varroa Assessment results.
- Live Bee Localisation to Bee Orientation to Varroa pipeline execution.
- Automated Bee Orientation inference.
- Running Varroa Detection on unreliable orientation.
- Blind Independent Review or Third-Party Adjudication.
- Varroa Dataset Role assignment or Varroa Dataset Versions.
- Gold-Standard Full-Frame Corpus management.
- Sampling-plan selection, stratified random queues, or inspection-rate estimation.
- Cross-crop or inspection-level Varroa Review queues and repository workflows.
- Bulk no-visible-Varroa marking.
- Custom keyboard shortcuts.
- Stored normalized crop image artifacts, downloads, or export packages.
- Mite bounding boxes, segmentation masks, marker agreement metrics, or review-strength promotion thresholds.
- Marker dragging, per-marker notes, and suspect-marker types for unresolved outcomes.
- Automatic invalidation when source Bee Annotation geometry changes; PARK-0052 records this risk.
- Local QA command or seeded demo Varroa reviews.
- Treatment recommendation or HiveSight Advisor integration.

## Acceptance Criteria

- [ ] A Dataset Curator can see eligible reliable complete bees for Varroa review from a completed Training Crop.
- [ ] The Training Inspection Workflow includes a `Varroa Review` stage after Crop Governance and before Model Governance.
- [ ] Bee Annotation exposes compact selected-bee triage controls for Varroa Review Suitability and Suspected Visible Varroa Cue.
- [ ] Triage cues can be saved on visible bee annotations with last-updated provenance and do not create Varroa Review Outcomes.
- [ ] Suspected-visible-Varroa cues appear first in the Varroa Review list by default.
- [ ] Partial visible bees and unreliable-orientation bees are shown as excluded/deferred with explicit reasons.
- [ ] HiveSight generates a Head-Up Normalized Bee Crop preview for an eligible bee.
- [ ] The preview retains source evidence and transform provenance.
- [ ] The curator can save `visible_varroa_present` only when at least one marker exists.
- [ ] Multiple point markers can be recorded, shown, selected, and deleted one by one.
- [ ] Marker coordinates are stored as normalized 0-1 crop coordinates.
- [ ] The curator can save `no_visible_varroa` as an explicit active negative with zero markers.
- [ ] The curator can save `not_determined` only with a note and without it being treated as negative evidence.
- [ ] Saved outcomes, notes, and marker positions are visible when reopened.
- [ ] Saved outcomes are editable as one current review per Bee Annotation, with created/updated provenance.
- [ ] Existing outcomes become read-only when the source Training Crop or bee is temporarily ineligible for update.
- [ ] Crop-level Varroa Review summary distinguishes curation progress from Varroa Assessment.
- [ ] Records are labelled as `model_curation`, `human_selected`, `single_curator_review`, and `human_from_scratch`.
- [ ] The UI and API make no Varroa Detector, user-facing assessment, treatment, or colony-level claim.
- [ ] Focused Core API tests and API-level BDD cover cues, eligibility, outcomes, marker rules, and persistence.
- [ ] Playwright browser acceptance covers the curator workflow.
- [ ] Postgres-backed persistence is implemented and verified, or a live Postgres verification gap is explicitly recorded.
- [ ] `pnpm verify:slice` passes before closeout when implemented.
- [ ] Relevant docs are updated after implementation: `CONTEXT.md`, `architecture/domain-model.md`, `architecture/domain-model-diagram.md`, `requirements/roadmap.md`, `docs/user-guide.md`, this slice document, `architecture/parking-lot.md`, and `requirements/ai-sdlc-observations.md`.

## Open Questions

- None after Slice 0025 grilling. Acceptance scenarios still require explicit signoff.
