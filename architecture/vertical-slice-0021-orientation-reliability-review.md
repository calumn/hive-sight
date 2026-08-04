# Vertical Slice 0021: Orientation Reliability Review

Status: grilled and accepted for slice planning.

## Purpose

Let an annotation editor record whether each directed Oriented Bee Ellipse has trustworthy head direction without adding a click to the normal obvious-head case.

This slice proves the first required evidence gate for Bee Orientation. HiveSight already stores directed ellipse rotation, where `rotation_degrees` points from the ellipse centre toward the bee's head. A new ellipse defaults to reliable because, in normal annotation work, the bee's head direction is usually obvious once the annotator has drawn, rotated, and flipped the ellipse. The annotator changes the value only when head/tail direction is genuinely doubtful.

The slice does not train the Bee Orientation Model. It creates the reviewed Orientation Reliability evidence that later shared marked-bee Dataset Versions, Head Up / Head Down dataset exports, and Head-Up Normalized Varroa evidence must consume.

This is still one source training set, not a second annotation corpus. The Dataset Curator provides reviewed, marked, oriented bees once. Bee Localisation and Bee Orientation consume different projections of that same governed source evidence: YOLO OBB uses the geometry projection, while Bee Orientation uses the directed head/tail projection only when Orientation Reliability is reviewed as reliable.

When a marked-bee Dataset Version is promoted, it should apply to both Bee Localisation and Bee Orientation in lockstep. This slice must not create a separate orientation source dataset that can drift away from the YOLO/localisation source dataset. Later slices may create separate derived export packages for each Model Purpose from the same Dataset Version.

## Source Inputs

- `CONTEXT.md`: Oriented Bee Ellipse, Orientation Reliability, Training Inspection Workflow, Bee Annotation, Crop Governance, Bee Orientation Model, Head-Up Normalized Bee Crop.
- `requirements/model-requirements.md`: MR-001A Bee Head Direction, MR-008B Orientation Reliability, Bee Orientation Metrics.
- `requirements/ai-assisted-annotation-and-model-training-baseline.md`: Bee Orientation and Orientation Reliability requirements.
- `requirements/roadmap.md`: Bee Orientation candidate slices, especially Orientation Reliability Review and Shared Marked-Bee Dataset Version Promotion.
- `architecture/adr/0006-directed-bee-ellipse-orientation.md`: Oriented Bee Ellipse rotation is directed centre-to-head geometry.
- `architecture/adr/0007-three-stage-bee-localisation-orientation-and-varroa-pipeline.md`: Bee Localisation, Bee Orientation, and Varroa Detection are separately governed Model Purposes.
- `architecture/bee-orientation-classifier-design.md`: Bee Orientation Dataset Builder eligibility requires reviewed Orientation Reliability of `reliable`.
- `architecture/domain-model.md`: Reviewed Bee Annotations must carry Orientation Reliability before shared marked-bee Dataset Versions are used for Bee Orientation or head-normalized Varroa exports.
- `architecture/parking-lot.md`: PARK-0029 Orientation Reliability Review And Dataset Gate.

## Accepted Acceptance Scenarios

```gherkin
Feature: Orientation Reliability Review

  Scenario: New bee annotations default to reliable head direction
    Given an annotation editor is working on an editable Training Crop
    When they create a new Oriented Bee Ellipse
    Then HiveSight saves the bee annotation with Orientation Reliability reliable
    And the Bee Annotation UI shows the selected bee as Head direction reliable
    And no extra click is required for the normal obvious-head case

  Scenario: Annotation editor marks head direction as unreliable
    Given an annotation editor is working on an editable Training Crop
    And a selected Oriented Bee Ellipse has doubtful head direction
    When they switch Head direction reliable off
    Then HiveSight saves Orientation Reliability unreliable for that bee annotation
    And the crop can still be marked review complete
    And later shared marked-bee dataset readiness excludes that bee from reliable-orientation evidence

  Scenario: Existing local test annotations are treated as reliable
    Given existing local test Training Crops contain Oriented Bee Ellipses created before Slice 0021
    When HiveSight loads or migrates those annotations
    Then HiveSight treats their Orientation Reliability as reliable
    And HiveSight does not show those bees as needing one-time orientation review
    And no separate defaulted-provenance flag is required for this bootstrap test data

  Scenario: Assigned dataset evidence cannot be silently changed
    Given a Training Crop has been assigned into a Dataset Item
    When an annotation editor opens that crop
    Then HiveSight does not allow Orientation Reliability to be changed in place
    And any later correction requires the existing reopen or supersession workflow

  Scenario: Crop Governance summarizes orientation readiness
    Given a completed Training Crop contains reliable and unreliable Oriented Bee Ellipses
    When the Dataset Curator views the crop in Crop Governance
    Then HiveSight shows how many bees are reliable for orientation-dependent exports
    And HiveSight shows how many bees are excluded because head direction is unreliable
    And Crop Governance links back to Bee Annotation rather than editing Orientation Reliability directly
```

## User Path

Given an annotation editor is working in Bee Annotation for an editable Training Crop
When they create or select an Oriented Bee Ellipse
Then HiveSight shows the plain-language control `Head direction reliable`
And the bee defaults to reliable head direction
And the editor can switch it to unreliable when the head/tail direction is doubtful
And Crop Governance summarizes reliable and unreliable orientation evidence without becoming the editing surface.

## Preconditions

- The selected Inspection has intent `training_data_collection`.
- The selected User is allowed to edit bee annotations in the Training Data Collection workflow.
- Workspace Data Use Agreement requirements remain enforced.
- The Training Crop and Oriented Bee Ellipse already exist.
- Existing local test annotations created before Slice 0021 are treated as `reliable` without a separate defaulted-provenance flag.
- New Oriented Bee Ellipses default to `reliable` immediately on creation.
- Dataset Item assignment and Dataset Version creation continue to use existing marked-bee evidence. This slice adds orientation-dependent readiness evidence, not a new dataset builder.
- Orientation Reliability extends the same reviewed bee annotation evidence used by Bee Localisation. It must not create a parallel source dataset or duplicate provenance chain.
- A future promoted marked-bee Dataset Version must be shared by Bee Localisation and Bee Orientation; only the derived export packages are purpose-specific.
- Once annotation evidence has been assigned into a Dataset Item, Orientation Reliability is frozen with that evidence. Any later correction requires the existing reopen or supersession workflow.

## End-To-End Behaviour

The Bee Annotation stage adds a plain-language `Head direction reliable` control for the selected Oriented Bee Ellipse.

The control has two reviewed decisions:

- `reliable`: the annotation editor can visually trust that the directed ellipse points toward the bee's head. This is the default for new and existing local test annotations.
- `unreliable`: the annotation editor cannot visually trust head/tail direction, even if the bee geometry itself is acceptable.

The stored domain value remains binary: `reliable` or `unreliable`. The UI must not introduce a numeric confidence value. A missing value should not normally exist after this slice; if encountered from bad legacy or integration data, it should be treated as not eligible for orientation-dependent exports until normalized.

The Crop Governance stage adds crop-level orientation-readiness evidence:

- number marked reliable;
- number marked unreliable;
- number eligible for orientation-dependent exports;
- number excluded from orientation-dependent exports because head direction is unreliable.

Where the UI already shows Dataset Role or dataset readiness warnings, it should distinguish Bee Localisation readiness from future Bee Orientation / Head-Up Normalized Varroa export readiness. A crop may still be useful for Bee Localisation while not yet usable as reliable orientation evidence, but both claims come from the same reviewed source annotation record and same promoted Dataset Version.

The Core API persists Orientation Reliability on each Bee Annotation. Updating reliability while the crop is editable should not change ellipse geometry, visibility class, or review status.

Changing Orientation Reliability is not allowed in place once the annotation evidence has been assigned into a Dataset Item or frozen into a Dataset Version. Corrections after that point use the existing reopen or supersession workflow so frozen evidence stays frozen.

Existing Dataset Items and Dataset Versions remain immutable snapshots. If a future orientation-dependent dataset builder consumes an annotation, it must use the reliability value from the relevant shared marked-bee Dataset Version snapshot or explicitly record why the item was excluded from the derived export. This slice may expose readiness counts before that builder exists, but it must not pretend to create a separate Bee Orientation source Dataset Version.

## Layers Touched

- Web UI: Add selected-ellipse `Head direction reliable` controls in Bee Annotation; add crop-level orientation-readiness status in Crop Governance; hide editing controls when the crop is not editable.
- Core API: Add or extend the smallest endpoint needed to update Orientation Reliability for one bee annotation and return reliability provenance in existing crop/annotation responses.
- Analysis Service: Not touched.
- Storage: Persist Orientation Reliability for existing and new Oriented Bee Ellipses. Existing local test rows are normalized to `reliable`.
- Queue or async boundary: Not touched.
- Contracts: Extend the bee annotation response and update request shape with `orientation_reliability`.
- Observability: Existing request logging is sufficient; API error responses should use normal authorization and validation paths.

## Test Seams

- Seam: Core API annotation creation and update
- Behaviour verified: new Oriented Bee Ellipses default to Orientation Reliability `reliable`; an annotation editor can set editable annotation evidence to `reliable` or `unreliable`; the value is returned when the crop/annotation is reloaded.
- Test style: focused Core API test against the existing in-memory dev store, plus Postgres persistence coverage when practical.

- Seam: Core API frozen evidence protection
- Behaviour verified: Orientation Reliability cannot be changed in place after the annotation evidence has been assigned into a Dataset Item.
- Test style: focused Core API regression test.

- Seam: Web Bee Annotation review control
- Behaviour verified: creating a bee ellipse shows `Head direction reliable` on by default; switching it off marks the selected bee unreliable and survives reload.
- Test style: Playwright browser acceptance using existing training-crop fixture flow.

- Seam: Web Crop Governance readiness
- Behaviour verified: crop rows or selected-crop detail show reliable and unreliable orientation evidence counts, distinguish orientation export readiness from Bee Localisation dataset-role status, and link back to Bee Annotation for changes.
- Test style: Playwright browser acceptance extending Slice 0020 stage coverage.

## Data Shape

Minimum fields on reviewed bee annotation records:

- `orientation_reliability`: enum, `reliable` or `unreliable`.

Minimum update command:

- target annotation id;
- desired Orientation Reliability value: `reliable` or `unreliable`;
- acting User from the Core API development/auth boundary;
- expected Workspace and Training Crop context, if needed for authorization and stale-state protection;
- editable-evidence guard rejecting updates after Dataset Item assignment or Dataset Version freezing.

Minimum derived crop summary:

- `orientation_reliable_count`;
- `orientation_unreliable_count`;
- `orientation_export_eligible_count`;
- `orientation_export_excluded_count`.

## Out Of Scope

- Shared marked-bee Dataset Version promotion.
- Bee Orientation Dataset Builder export packages.
- Bee Orientation classifier training, inference, benchmark reports, or model-candidate promotion.
- Varroa Review Outcome labelling.
- Varroa Detector training or user-facing Varroa Assessment results.
- Blind independent review of Orientation Reliability.
- Numeric thresholds for model-predicted orientation reliability.
- Notes or reason codes for unreliable head direction.
- Reworking historical Dataset Versions or Training Runs.

## Acceptance Criteria

- [ ] New Oriented Bee Ellipses default to Orientation Reliability `reliable`.
- [ ] Existing local test ellipses are treated as `reliable` without a separate defaulted-provenance flag.
- [ ] An annotation editor can mark each editable Oriented Bee Ellipse as orientation `reliable` or `unreliable`.
- [ ] Orientation Reliability persists after reload and through the configured metadata backend.
- [ ] Assigned or frozen Dataset Item evidence cannot have Orientation Reliability changed in place.
- [ ] Crop Governance shows reliable and unreliable orientation counts for the selected crop, and links back to Bee Annotation for edits.
- [ ] Orientation-dependent readiness excludes missing and unreliable orientation evidence, while the promoted source Dataset Version remains shared with Bee Localisation.
- [ ] Crop completion remains allowed when one or more bees have `unreliable` Orientation Reliability.
- [ ] Focused Core API and Playwright regression guards cover persistence, authorization, and the main review path.
- [ ] `pnpm verify:slice` passes before implementation closeout, with live Postgres verification recorded if the persistence path is changed.

## Open Questions

- None after Slice 0021 grilling. Implementation should preserve the agreed scope and avoid adding separate orientation dataset promotion, numeric reliability, notes, or Crop Governance editing.
