# Vertical Slice 0021: Orientation Reliability Review

Status: draft for acceptance scenario sign-off.

## Purpose

Let a Dataset Curator review the head direction already recorded on each directed Oriented Bee Ellipse and mark whether that direction is trustworthy.

This slice proves the first required evidence gate for Bee Orientation. HiveSight already stores directed ellipse rotation, where `rotation_degrees` points from the ellipse centre toward the bee's head. That direction is useful only if a human can say whether the visible evidence supports it. A bee can be correctly localised while its head/tail direction is still visually unreliable.

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

## Acceptance Scenarios For Sign-Off

```gherkin
Feature: Orientation Reliability Review

  Scenario: Curator marks directed ellipse orientation as reliable
    Given a Dataset Curator is working in a Training Data Collection Inspection
    And a selected Training Crop has a reviewed Oriented Bee Ellipse without Orientation Reliability
    When the curator marks the bee's Orientation Reliability as reliable
    Then HiveSight saves the reliability decision for that bee annotation
    And the selected crop shows one fewer bee needing orientation review
    And the same reliability decision is still shown after the inspection is reopened

  Scenario: Curator marks directed ellipse orientation as unreliable
    Given a Dataset Curator is working in a Training Data Collection Inspection
    And a selected Training Crop has a reviewed Oriented Bee Ellipse whose head direction is not visually trustworthy
    When the curator marks the bee's Orientation Reliability as unreliable
    Then HiveSight saves the reliability decision for that bee annotation
    And Crop Governance shows the crop has unreliable orientation evidence
    And later shared marked-bee dataset readiness excludes that bee from reliable-orientation evidence

  Scenario: Missing reliability blocks orientation-dependent dataset readiness
    Given a completed Training Crop contains reviewed Oriented Bee Ellipses
    And at least one ellipse has no Orientation Reliability decision
    When the Dataset Curator views governance readiness for the crop
    Then HiveSight shows that orientation review is still needed
    And HiveSight does not count that ellipse as eligible reliable evidence for orientation-dependent exports from the shared marked-bee Dataset Version

  Scenario: Non-curators cannot change Orientation Reliability
    Given a User without Dataset Curator capability can view or resume an allowed inspection workflow
    When they view a Training Crop with Oriented Bee Ellipses
    Then HiveSight does not offer controls to change Orientation Reliability
    And the Core API rejects any direct attempt to change Orientation Reliability for that User
```

## User Path

Given a Dataset Curator is reviewing Bee Annotations in a Training Data Collection Inspection
When they select a bee ellipse in Bee Annotation or inspect a crop in Crop Governance
Then HiveSight shows whether that ellipse's Orientation Reliability is missing, reliable, or unreliable
And the curator can mark the selected ellipse as reliable or unreliable
And the decision persists with reviewer and timestamp provenance
And crop-level governance shows whether orientation review is complete enough for future orientation-dependent dataset work.

## Preconditions

- The selected Inspection has intent `training_data_collection`.
- The selected User has Dataset Curator capability.
- Workspace Data Use Agreement requirements remain enforced.
- The Training Crop and Oriented Bee Ellipse already exist.
- Existing directed ellipses may have no Orientation Reliability yet. Missing reliability is represented as "needs orientation review", not as a third reviewed reliability value.
- Dataset Item assignment and Dataset Version creation continue to use existing marked-bee evidence. This slice adds orientation-dependent readiness evidence, not a new dataset builder.
- Orientation Reliability extends the same reviewed bee annotation evidence used by Bee Localisation. It must not create a parallel source dataset or duplicate provenance chain.
- A future promoted marked-bee Dataset Version must be shared by Bee Localisation and Bee Orientation; only the derived export packages are purpose-specific.

## End-To-End Behaviour

The Bee Annotation stage adds Orientation Reliability controls for the selected Oriented Bee Ellipse.

The control has two reviewed decisions:

- `reliable`: the curator can visually trust that the directed ellipse points toward the bee's head.
- `unreliable`: the curator cannot visually trust head/tail direction, even if the bee geometry itself is acceptable.

If an existing annotation has no recorded Orientation Reliability, the UI shows it as needing orientation review. This missing state exists for migration and workflow readiness. It is not a reviewed domain outcome and must not be exported as reliable evidence.

The Crop Governance stage adds crop-level orientation-readiness evidence:

- number of bee annotations needing orientation review;
- number marked reliable;
- number marked unreliable;
- a compact warning when any completed crop still contains missing or unreliable orientation evidence.

Where the UI already shows Dataset Role or dataset readiness warnings, it should distinguish Bee Localisation readiness from future Bee Orientation / Head-Up Normalized Varroa export readiness. A crop may still be useful for Bee Localisation while not yet usable as reliable orientation evidence, but both claims come from the same reviewed source annotation record and same promoted Dataset Version.

The Core API persists Orientation Reliability on each reviewed Bee Annotation, including the reviewer User id and review timestamp. Updating reliability should not change the ellipse geometry, visibility class, review status, Dataset Item assignment, or existing Bee Localisation dataset evidence.

Existing Dataset Items and Dataset Versions remain immutable snapshots. If a future orientation-dependent dataset builder consumes an annotation, it must use the reliability value from the relevant shared marked-bee Dataset Version snapshot or explicitly record why the item was excluded from the derived export. This slice may expose readiness counts before that builder exists, but it must not pretend to create a separate Bee Orientation source Dataset Version.

## Layers Touched

- Web UI: Add selected-ellipse Orientation Reliability controls in Bee Annotation; add crop-level orientation-readiness status in Crop Governance; hide controls for non-curator Users.
- Core API: Add or extend the smallest endpoint needed to update Orientation Reliability for one bee annotation and return reliability provenance in existing crop/annotation responses.
- Analysis Service: Not touched.
- Storage: Persist nullable Orientation Reliability and review provenance for existing and new Oriented Bee Ellipses. Existing rows start with no reliability decision.
- Queue or async boundary: Not touched.
- Contracts: Extend the bee annotation response and update request shape with `orientation_reliability`, `orientation_reliability_reviewed_by_user_id`, and `orientation_reliability_reviewed_at`.
- Observability: Existing request logging is sufficient; API error responses should use normal authorization and validation paths.

## Test Seams

- Seam: Core API annotation update
- Behaviour verified: a Dataset Curator can set Orientation Reliability to `reliable` or `unreliable`; the value and provenance are returned when the crop/annotation is reloaded.
- Test style: focused Core API test against the existing in-memory dev store, plus Postgres persistence coverage when practical.

- Seam: Core API authorization
- Behaviour verified: a User without Dataset Curator capability cannot change Orientation Reliability, even if they can otherwise view the relevant workflow.
- Test style: focused Core API regression test.

- Seam: Web Bee Annotation review control
- Behaviour verified: selecting a bee ellipse shows missing/reliable/unreliable state; marking each state updates the visible selected bee and survives reload.
- Test style: Playwright browser acceptance using existing training-crop fixture flow.

- Seam: Web Crop Governance readiness
- Behaviour verified: crop rows or selected-crop detail show counts for missing, reliable, and unreliable orientation evidence, and distinguish orientation-readiness warnings from Bee Localisation dataset-role status.
- Test style: Playwright browser acceptance extending Slice 0020 stage coverage.

## Data Shape

Minimum fields on reviewed bee annotation records:

- `orientation_reliability`: nullable enum, `reliable` or `unreliable`; null means no reviewed decision recorded yet.
- `orientation_reliability_reviewed_by_user_id`: nullable User id.
- `orientation_reliability_reviewed_at`: nullable timestamp.

Minimum update command:

- target annotation id;
- desired Orientation Reliability value: `reliable` or `unreliable`;
- acting User from the Core API development/auth boundary;
- expected Workspace and Training Crop context, if needed for authorization and stale-state protection.

Minimum derived crop summary:

- `orientation_reliability_missing_count`;
- `orientation_reliable_count`;
- `orientation_unreliable_count`;
- `orientation_review_complete`: true when every in-scope reviewed Oriented Bee Ellipse has a reliability decision.

## Out Of Scope

- Shared marked-bee Dataset Version promotion.
- Bee Orientation Dataset Builder export packages.
- Bee Orientation classifier training, inference, benchmark reports, or model-candidate promotion.
- Varroa Review Outcome labelling.
- Varroa Detector training or user-facing Varroa Assessment results.
- Blind independent review of Orientation Reliability.
- Numeric thresholds for model-predicted orientation reliability.
- Reworking historical Dataset Versions or Training Runs.

## Acceptance Criteria

- [ ] A Dataset Curator can mark each reviewed Oriented Bee Ellipse as orientation `reliable` or `unreliable`.
- [ ] Existing ellipses without a decision are shown as needing orientation review, not silently treated as reliable.
- [ ] Orientation Reliability and review provenance persist after reload and through the configured metadata backend.
- [ ] Crop Governance shows missing, reliable, and unreliable orientation counts for the selected crop.
- [ ] Orientation-dependent readiness excludes missing and unreliable orientation evidence, while the promoted source Dataset Version remains shared with Bee Localisation.
- [ ] Non-curator Users cannot change Orientation Reliability in the UI or Core API.
- [ ] Focused Core API and Playwright regression guards cover persistence, authorization, and the main review path.
- [ ] `pnpm verify:slice` passes before implementation closeout, with live Postgres verification recorded if the persistence path is changed.

## Open Questions

- Should Orientation Reliability be reviewed primarily in Bee Annotation, Crop Governance, or both in the first UI pass? This slice proposes Bee Annotation for per-ellipse editing and Crop Governance for summary/readiness.
- Should changing Orientation Reliability on an annotation that is already snapshotted into a Dataset Item require a reopen/supersession workflow, or is the decision only consumed by future shared marked-bee Dataset Version snapshots? This slice proposes no mutation of existing Dataset Items or Dataset Versions.
- Should partial visible bees receive Orientation Reliability now for future retained evidence, even though the first Bee Orientation corpus will use complete visible bees only? This slice proposes yes: record reliability on every reviewed Oriented Bee Ellipse, then let later dataset builders choose eligible visibility classes.
