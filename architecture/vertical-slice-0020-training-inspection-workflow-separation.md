# Vertical Slice 0020: Training Inspection Workflow Separation

Status: implemented.

## Purpose

Make Training Data Collection inspections easier and safer to work through by separating the current overloaded Inspection page into task-focused workflow stages.

The slice does not change the underlying domain model. It reorganises the existing Training Data Collection workflow so the Dataset Curator can move through four clear jobs:

- set up or resume the Inspection;
- upload photos and define Training Crops;
- annotate bees within those crops;
- govern completed crops through review requests and Dataset Role assignment.

This is not cosmetic. It reduces the chance of accidentally working in the wrong state, makes long annotation sessions easier to resume, and creates a cleaner home for review/governance rules without crowding the crop editor.

## Source Inputs

- `CONTEXT.md`: Inspection, Inspection Intent, Training Data Collection, Inspection Photo, Source Image, Training Crop, Oriented Bee Ellipse, Dataset Curator, Review Queue Item, Dataset Item, Dataset Role.
- `requirements/product-spec.md`: AI-assisted annotation and dataset bootstrap scenarios.
- `requirements/roadmap.md`: Product Workflow And UX items, especially Annotation Productivity Improvements, Inspection Completion Semantics, Inspection History And Resume, Reviewer Work Queue.
- `architecture/parking-lot.md`: UI-level Gherkin harness, Candidate Annotation Review redesign, review queue follow-ons, annotation productivity follow-ons.
- `architecture/vertical-slice-0017-resume-training-inspections-and-crops.md`: resumable Training Data Collection inspections and saved crop/ellipse state.
- `architecture/vertical-slice-0018-dev-user-and-role-switching.md`: Development User switching must clear user-scoped UI state.
- `architecture/vertical-slice-0019-reviewer-work-queue.md`: Request review, Review Work, and requested-review status are now real workflow surfaces.
- Recent manual QA feedback: the single Inspection page now mixes setup, upload, crop selection, bee annotation, review request, Dataset Role assignment, model training, and model evaluation, which makes the workflow hard to reason about.

## Skill And Acceptance-Test Note

HiveSight's current skills already contain the important Gherkin workflow:

- `sdlc-delivery-vertical-slice-planning` explicitly requires acceptance scenario drafting and sign-off before implementation when a slice has new user-facing behaviour.
- `sdlc-delivery-acceptance-bdd` covers Gherkin scenario quality and step-definition mapping.
- `sdlc-delivery-acceptance-scenario-signoff` covers the separate checkpoint where the User reviews the actual scenario text before implementation.

`productivity-grilling` remains deliberately generic. It should continue to resolve design questions one at a time. For this slice, grilling must be followed by explicit acceptance scenario sign-off before implementation begins.

UI-level Gherkin remains parked as a harness choice. Slice 0020 should define signed-off Gherkin-style scenarios in the slice doc, while implementation may still use Playwright browser acceptance unless the UI-level Gherkin harness is deliberately promoted.

## User Path

Given a Dataset Curator is working in a Training Data Collection Inspection
And the Inspection may contain multiple uploaded photos and multiple saved Training Crops
When the Dataset Curator opens the Inspection workflow
Then HiveSight presents separate workflow stages for setup, crop selection, bee annotation, and crop governance
And each stage shows only the controls needed for that task
And moving between stages preserves the same saved Inspection, photo, crop, ellipse, review, and Dataset Item state.

## Preconditions

- Slice 0017 resume behaviour remains in place: existing Training Data Collection Inspections, photos, Training Crops, and Oriented Bee Ellipses can be reloaded.
- Slice 0019 review workflow remains in place: a completed Training Crop can be requested for review, and requested-review state can be displayed.
- Development User switching remains available and must continue to clear user-scoped UI state.
- Workspace Data Use Agreement remains required before upload, crop annotation, review request, Dataset Role assignment, and model-governance actions.
- Dataset Curator capability remains required for Training Crop annotation, Dataset Item assignment, and model-training/governance controls.
- Review Work remains a separate page for Reviewer Users. This slice reorganises the Dataset Curator's Training Data Collection workflow, not the Reviewer Work page.
- This slice should avoid new persisted records.

## End-To-End Behaviour

The current Inspection view becomes a Training Inspection workflow for `training_data_collection` inspections.

The first implementation uses task stages inside the existing Inspection route, most likely tabs or a stepper. This is not a commitment to long-term routing. A future multi-page flow can be introduced once the workflow shape is stable.

The visible stage map is present from the start. Later stages show empty or disabled states until the selected Inspection has enough data for them. The Development User switcher remains outside the workflow in the existing `Development session` area, because switching User is a proxy for logging out and back in.

The initial default stage is derived from saved state when the User first opens or resumes an Inspection, or when the Development User or Workspace changes:

- no selected or resumable Inspection: `Inspection Setup`;
- selected Inspection but no uploaded photos: `Crop Selection`;
- uploaded photos or crops with pending annotation: `Bee Annotation`;
- all crops complete, Dataset Items exist, or review work exists: `Crop Governance`.

After that, the selected stage remains under the User's control. Completing a crop must not automatically bounce the User into Crop Governance; the UI should instead show clear next-action buttons.

Stage progress counts are inspection-wide. Crop Selection may additionally show per-photo crop counts in the source-photo list.

### Stage 1: Inspection Setup

The setup stage lets the Dataset Curator select or create:

- Apiary;
- Hive;
- Hive Configuration;
- Training Data Collection Inspection.

It keeps the current resume selector for existing Training Data Collection Inspections. The selected Inspection is visibly stable across stage changes.

This stage does not show crop-ellipse controls, review-request controls, Dataset Role assignment controls, model training, or benchmark evaluation controls.

### Stage 2: Photo Upload And Crop Selection

The crop-selection stage lets the Dataset Curator:

- upload one or more Inspection Photos;
- select the Source Image/photo being cropped;
- draw and save Training Crop boxes on the full source photo;
- see existing crop boxes over the source photo;
- delete unwanted unassigned/unrequested crops, using the existing domain rules;
- see a compact crop list with crop status and assigned Dataset Role;
- see crop boxes and simple text rows, not crop thumbnails in this slice.

This stage is about defining the crop regions. It should not show ellipse annotation controls, Dataset Role assignment, review request controls, model training, or benchmark evaluation controls.

Clicking or otherwise choosing a crop can offer a clear action to move to Bee Annotation for that crop.

Crop Selection works one selected Source Image/photo at a time for drawing crop boxes, while also showing an all-photo summary and crop counts.

### Stage 3: Bee Annotation

The bee-annotation stage is focused on one selected Training Crop at a time.

It lets the Dataset Curator:

- choose a crop from the selected Inspection's unified crop queue, with source-photo labels;
- see the cropped image large enough for careful work;
- zoom and pan within the crop;
- add, select, move, resize, rotate, flip, and delete Oriented Bee Ellipses;
- use crop YOLO candidate suggestions when a Model Candidate is selected, as a secondary annotation aid near the crop editor;
- mark the crop as `review_complete` or `excluded`;
- reopen a completed crop when allowed by existing rules;
- see immediate saved state and crop/ellipse counts;
- use `Previous crop`, `Next crop`, and `Next incomplete crop` navigation.

This stage should minimise unrelated text between the crop image and controls. The controls belong close to the crop being edited.

The crop queue orders crops as incomplete first, completed second, and excluded last. Within each group it uses source-photo order and then crop creation order. Completing a crop does not automatically select the next crop; the User chooses the next action.

Completed, reviewed, or assigned crops remain visible in Bee Annotation. Assigned crops are locked unless explicitly reopened from Crop Governance. Crops with active Review Queue Items are also visible but locked, with a compact explanation that the active review must be cancelled from Crop Governance before editing.

Annotation actions should auto-save through existing APIs. Where practical, the crop editor should show a small `Saving`, `Saved`, or `Save failed` indicator so stage switching is not a trap.

Dataset Role assignment and review request controls are not primary actions here. If shown at all, they should be compact status links into Crop Governance, not full governance panels.

### Stage 4: Crop Governance

The crop-governance stage shows the selected Inspection's Training Crops as a worklist.

For each crop it should show at least:

- crop number or stable label;
- review status: `review_pending`, `review_complete`, or `excluded`;
- visible bee status;
- complete visible bee and partial visible bee counts separately when available;
- active or completed Review Queue status when present;
- completed Review Queue outcome details when present: outcome, Reviewer identity, notes, and timestamp;
- Dataset Item assignment status and Dataset Role when present;
- whether the crop is blocked from editing because a review request is active;
- whether the crop is eligible for Dataset Role assignment.

The governance stage owns:

- `Request review`;
- optional short review request notes;
- cancelling an active review request;
- requested-review status;
- Dataset Role assignment to `training`, `validation`, `benchmark`, or `excluded`;
- compact warnings when assignment is impossible;
- compact reasons for unavailable actions, such as `Complete annotation before assigning to dataset` or `Cancel active review before editing`;
- `Reopen/Edit` for crops that are complete, reviewed, or assigned;
- links back to Bee Annotation when a crop needs more work.

The governance stage uses a scannable crop worklist plus a selected-crop detail/action panel. Rows should not become overloaded with every possible action.

Supported filters for this slice:

- `All`;
- `Needs annotation`;
- `Ready for governance`;
- `Waiting for review`;
- `Assigned`;
- `Excluded`.

Dataset Role assignment before independent review remains allowed for now, but the UI must show review-strength or governance warnings rather than implying the evidence is independently verified. A completed zero-bee crop is not eligible for the positive bee-detector training dataset; a future negative/background dataset role is parked.

Reopening an assigned crop invalidates or removes its active Dataset Item assignment, while preserving audit history. Reopening a reviewed crop supersedes the previous review result because the reviewed evidence is no longer the same evidence. Retrospective review remains allowed for a crop that already has a Dataset Item, but it must be visibly labelled as retrospective and must warn that downstream artifacts do not change automatically.

Crop Governance shows selected Inspection crops only, not the whole Workspace. It includes source-photo grouping or labels, and a light `Waiting for review` filter/section for crops from this Inspection. A broader cross-inspection dashboard for "my submitted crops waiting for review" remains parked.

Dataset export and model training remain in the existing model-governance panel for this slice, but are separated from the primary bee-annotation editor by living in Crop Governance. A dedicated Model Governance page remains parked, because moving the whole model lifecycle is useful but wider than this workflow-separation slice.

## Workflow Rules

- One selected Training Data Collection Inspection is the workflow context.
- Stage changes must not create, modify, or lose data by themselves.
- Stage changes preserve saved records and reset only transient editor state.
- Saved Training Crops and Oriented Bee Ellipses remain persisted immediately through existing APIs.
- Unsaved crop draft boxes remain non-durable until `Save crop`.
- Crop annotation controls must not operate on stale evidence from another crop, photo, Inspection, Workspace, or Development User.
- User switching must clear the Training Inspection workflow state and reload from the newly selected Development User's Workspace.
- The UI should avoid showing controls that the selected User cannot possibly activate.
- The source image and inspection photo are the same underlying object. `Inspection Photo` is the UI/workflow presentation; `Source Image` is the underlying evidence object used for provenance and dataset/model governance.
- Crop boxes may overlap in this slice. Crop-boundary duplicate partial-bee handling remains parked for future dataset-quality and statistical claims.

## Layers Touched

- Web UI: Split the current Inspection surface into task-focused stages for setup, crop selection, bee annotation, and crop governance. Add stage navigation, empty states, status summaries, basic responsive behaviour, safe state resets, and a small purposeful component split around the stages.
- Core API: Ideally not touched. Existing Inspection, photo, Training Crop, ellipse, Review Queue, Dataset Item, Dataset Version, Training Run, Model Candidate, and Benchmark Evaluation endpoints should be reused. Add a smallest-possible read-only workflow summary only if the UI cannot assemble coherent state safely from existing endpoints.
- Analysis Service: Not touched.
- Storage: Not touched.
- Queue or async boundary: Not touched.
- Contracts: Ideally not touched. If the governance worklist needs a richer read model than existing crop/evidence/review endpoints can provide, add the smallest read-only response shape.
- Observability: Not touched beyond existing request logging and UI error states.

## Test Seams

- Seam: Web workflow stage separation
- Behaviour verified: setup, crop selection, bee annotation, and crop governance are visibly separate workflow stages, stage counts are inspection-wide, and each stage hides controls that belong to the other tasks.
- Test style: Playwright browser acceptance.

- Seam: Web crop-selection stage
- Behaviour verified: uploaded photos and saved crop boxes are visible; creating and deleting an unassigned crop works without exposing ellipse controls as the primary task.
- Test style: Playwright browser acceptance using existing fixture image.

- Seam: Web bee-annotation stage
- Behaviour verified: selecting a crop opens a focused annotation stage where existing zoom/pan/ellipse controls still work, YOLO pre-labelling remains available as an annotation aid, save status is visible where practical, and saved ellipses remain visible after stage changes.
- Test style: Playwright browser acceptance, extending existing Slice 0009/0017 coverage where practical.

- Seam: Web crop-governance stage
- Behaviour verified: crop rows show review status, requested-review status, Dataset Item assignment status, eligibility reasons, complete/partial bee counts, and allowed actions; requesting review and assigning a completed crop remain possible from the governance stage; assigned or active-review crops are locked from direct editing until reopened/cancelled through governance.
- Test style: Playwright browser acceptance, extending Slice 0010 and Slice 0019 coverage.

- Seam: Web state reset
- Behaviour verified: switching Development User or switching Inspection clears stale crop/evidence state and reloads from the current Workspace/Inspection.
- Test style: Playwright browser acceptance regression.

- Seam: Acceptance scenario sign-off
- Behaviour verified: approved Gherkin-style scenarios are embedded in this slice before implementation begins.
- Test style: documentation/sign-off checkpoint; executable implementation may remain Playwright until UI-level Gherkin is promoted.

## Data Shape

No new persisted domain entity is expected.

Existing reused shapes:

- Inspection: `inspection_id`, `hive_id`, `workspace_id`, `inspection_date`, `intent`.
- Inspection Photo: `inspection_photo_id`, filename, status, size, view URL.
- Training Crop: crop bounds, review status, visible bee status, Dataset Item id/role, notes, timestamps.
- Oriented Bee Ellipse: annotation type, center, radii, directed rotation, provenance.
- Review Queue Item: queue id, subject id, status, requested/completed/cancelled metadata, safe evidence snapshot.
- Dataset Item: role, reviewed ellipse snapshots, provenance, assignment metadata.

Possible UI-only state:

- selected workflow stage: `setup`, `crop_selection`, `bee_annotation`, `crop_governance`;
- selected photo id;
- selected crop id.

Persisting last selected stage/photo/crop is out of scope.

## Out Of Scope

- Changing the domain model for Inspections, Training Crops, Dataset Items, or Review Queue Items.
- Real authentication.
- New persisted workflow-stage preferences.
- Persisting "resume exactly where I left off" stage/photo/crop preference.
- Full URL routing unless chosen as the implementation approach.
- Mobile-first redesign of every panel; only basic narrow-width behaviour is included.
- Bulk crop creation or bulk annotation operations.
- Bulk Dataset Role assignment.
- Crop box resize/reposition after save.
- Crop thumbnails in Crop Selection.
- Reviewer correction workflow.
- Reviewer Work page UX redesign.
- Cross-inspection "my submitted crops waiting for review" dashboard.
- Per-ellipse reviewer comments or second-review/adjudication semantics.
- Hard-gating Bee Detector training on independent Review Queue outcomes.
- Full Dataset Item supersession workflow, including invalidating/removing an active assignment when a crop is reopened.
- Moving dataset export/model training into a dedicated Model Governance page.
- Negative/background Dataset Role for zero-bee crops.
- UI-level Gherkin harness implementation.
- Changing dataset eligibility, review rules, or model training rules beyond displaying/locking actions correctly.

## Acceptance Scenarios For Signoff

These scenarios were reviewed and approved before implementation.

```gherkin
Feature: Training Inspection workflow separation

  Scenario: Dataset Curator works through training inspection stages
    Given a Dataset Curator has selected a Training Data Collection Inspection
    When the Dataset Curator opens the Training Inspection workflow
    Then HiveSight shows separate stages for Inspection Setup, Crop Selection, Bee Annotation, and Crop Governance
    And each stage shows controls for its own task without crowding the other stages
    And the stage progress counts describe the whole selected Inspection

  Scenario: Dataset Curator defines crops before annotating bees
    Given a Dataset Curator has uploaded an Inspection Photo for a Training Data Collection Inspection
    When the Dataset Curator opens Crop Selection
    Then HiveSight shows the source photo and saved Training Crop boxes
    And the Dataset Curator can save a new Training Crop
    And ellipse editing, review request, and Dataset Role assignment controls are not shown as Crop Selection actions

  Scenario: Dataset Curator annotates one crop at a time
    Given a Training Data Collection Inspection has saved Training Crops
    When the Dataset Curator opens Bee Annotation for a selected crop
    Then HiveSight shows the selected crop image with zoom and pan controls
    And the Dataset Curator can add and adjust Oriented Bee Ellipses
    And the Dataset Curator can move to the previous crop, next crop, or next incomplete crop without losing saved annotations
    And the saved ellipses remain visible after moving away from and back to Bee Annotation

  Scenario: Dataset Curator governs completed crops separately from annotation
    Given a Training Data Collection Inspection has completed and pending Training Crops
    When the Dataset Curator opens Crop Governance
    Then HiveSight lists the Inspection's Training Crops with review status, visible bee status, Review Queue status, and Dataset Role assignment status
    And completed crops can be requested for review or assigned to a Dataset Role from the selected-crop governance detail
    And pending or zero-bee crops show compact reasons when Dataset Role assignment is unavailable

  Scenario: Dataset Curator reopens governed crop evidence deliberately
    Given a completed Training Crop has been assigned to a Dataset Role
    When the Dataset Curator reopens the crop for editing from Crop Governance
    Then HiveSight makes the crop editable in Bee Annotation
    And the active Dataset Item assignment is no longer treated as current evidence
    And the User can see that downstream artifacts are not automatically changed

  Scenario: Switching Development User clears stale inspection workflow state
    Given a Dataset Curator has selected a crop in one Development User's Workspace
    When the user switches to a different Development User and then switches back
    Then HiveSight reloads the selected User's Training Inspection workflow from saved data
    And no crop, ellipse, review, or Dataset Item state from the previous User is shown in the wrong Workspace
```

## Documentation Updates

- Update `docs/user-guide.md` so the Training Data Collection task is described as staged workflow: Inspection Setup, Crop Selection, Bee Annotation, Crop Governance, Repository.
- Update `requirements/roadmap.md` and `architecture/parking-lot.md` with deferred work from grilling.

## Grilling Decisions

- Implement stage separation inside the existing Inspection route; defer full page routing.
- Allow free movement between stages, with empty/disabled states rather than a strict wizard.
- Derive the initial/default stage only when first opening/resuming an Inspection or switching Development User/Workspace. Do not persist stage selection.
- Keep stage counts inspection-wide.
- Keep the Development User switcher outside the workflow.
- Keep Photo Upload and crop drawing in Crop Selection.
- Keep YOLO crop pre-labelling in Bee Annotation as a secondary annotation aid.
- Keep Dataset export, Dataset Version, Training Run, Model Candidate, and Benchmark Evaluation controls out of the Bee Annotation stage. The implementation keeps them in Crop Governance for now; a dedicated Model Governance page remains parked.
- Make Crop Governance a selected-Inspection worklist with selected-crop detail/actions.
- Keep independent review and Dataset Role assignment separate, visible governance concepts.
- Allow Dataset Role assignment before independent review for now, with clear warnings.
- Lock assigned or active-review crops from direct editing until reopened or review is cancelled through Crop Governance.
- Reopening governed crop evidence should invalidate active Dataset Item assignment and supersede review outcome, but the full Dataset Item supersession workflow remains parked.
- Keep zero-bee crop Dataset Role handling out of the positive bee-detector training dataset for now.
- Update the User Guide, roadmap, and parking lot as part of the slice.

## Acceptance Criteria

- [x] Training Data Collection workflow has separate setup, crop-selection, bee-annotation, and crop-governance stages.
- [x] Stage navigation preserves the selected Inspection context.
- [x] Setup stage does not show crop annotation or governance controls.
- [x] Crop Selection stage shows uploaded photos, saved crop boxes, crop list/status, and crop create/delete actions.
- [x] Crop Selection stage keeps ellipse controls out of the primary workflow.
- [x] Bee Annotation stage shows one selected crop at a time with the existing zoom, pan, YOLO suggestion, ellipse edit, and completion controls.
- [x] Bee Annotation stage keeps review request and Dataset Role assignment out of the primary editor workflow.
- [x] Crop Governance stage lists all Training Crops for the selected Inspection with status, counts, Dataset Item assignment status, and allowed actions.
- [x] Request review and Dataset Role assignment remain available for eligible completed crops.
- [x] Pending crops clearly indicate that annotation must be completed before review request or Dataset Role assignment.
- [x] Switching stage does not lose saved crop or ellipse data.
- [x] Switching Development User or selected Inspection clears stale UI state and reloads from the correct Workspace/Inspection.
- [x] Existing browser acceptance coverage for crop creation, bee annotation, Dataset Item assignment, review request, and user switching is preserved or updated.
- [x] New browser acceptance covers the stage separation and stale-state regression.
- [x] Approved Gherkin-style acceptance scenarios are embedded in this slice before implementation begins.
- [x] User guide is updated to describe the task-oriented workflow.

## Open Questions

- None remaining from grilling.
- Acceptance scenarios were explicitly signed off before implementation.
