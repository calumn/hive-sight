# Vertical Slice 0034: One-Click Varroa Photo Analysis Workflow

Status: designed and grilled; acceptance scenarios formally accepted on 2026-08-07; ready for implementation.

## Purpose

Let a Beekeeper analyse an uploaded Varroa Assessment Inspection Photo through one visible `Analyze photo` action. HiveSight runs Bee Localisation, Bee Orientation, and Varroa Detection as one asynchronous product workflow, persists the resulting evidence, and lets any Workspace member inspect and review it.

The beekeeper does not select Training Crops or individual model stages. This slice removes that old product path completely. Training Inspection model-curation workflows remain separate and unchanged.

## User Path

Given a configured Hive has a Varroa Assessment Inspection with one or more accepted Inspection Photos,
when a Workspace member selects `Analyze photo` for one unanalysed or previously failed photo,
then HiveSight runs the complete photo pipeline, stores a durable Varroa Photo Analysis and Inspection Photo Bee Evidence, and shows a clear result with evidence and caveats.

`Analyze all photos` is a convenience request that processes a fixed snapshot of eligible photos serially. It is not an inspection-level scientific result.

## Accepted Acceptance Scenarios

```gherkin
@api @web
Feature: Varroa photo analysis workflow

  Scenario: A beekeeper analyses one Varroa Assessment photo
    Given a Workspace member has a Varroa Assessment Inspection with an uploaded photo
    And that photo has no prior Photo Analysis
    When the Workspace member requests photo analysis
    Then HiveSight starts one Photo Analysis for that Inspection Photo
    And HiveSight shows the photo-analysis stage while it is running
    And HiveSight completes Bee Localisation, Bee Orientation, and Varroa Detection as one workflow
    And HiveSight reports the Photo Analysis as unreviewed
    And HiveSight reports the number of analysed eligible bees and bees with likely visible Varroa
    And HiveSight does not require a Training Crop

  Scenario: A photo analysis preserves evidence without creating training evidence
    Given a completed Photo Analysis has likely Varroa detections
    When a Workspace member views its evidence
    Then HiveSight shows the source Inspection Photo and its identified bees
    And HiveSight shows the selected bee head-up with its detection markers
    And HiveSight preserves individual mite markers for each analysed bee
    And HiveSight does not create Training Crops or Varroa Review Outcomes

  Scenario: A partial result remains reviewable with its caveat
    Given a Photo Analysis localises complete bees
    And orientation or Varroa Detection cannot process one of those bees
    When HiveSight completes the Photo Analysis
    Then HiveSight reports the Photo Analysis as partial
    And HiveSight reports the failed-bee count and caveat
    And a Workspace member can accept the result

  Scenario: No bees found cannot become accepted evidence
    Given a Photo Analysis finds no complete bees in an Inspection Photo
    When HiveSight completes the Photo Analysis
    Then HiveSight reports no bees found
    And a Workspace member cannot accept the result
    And a Workspace member can mark the result rejected, inconclusive, or needs expert review with a note

  Scenario: Review status controls later Advisor evidence eligibility
    Given a completed or partial Photo Analysis is unreviewed
    When a Workspace member marks it accepted
    Then HiveSight marks it eligible for later Advisor evidence
    When a Workspace member changes it to needs expert review with a note
    Then HiveSight marks it ineligible for later Advisor evidence
    And HiveSight retains the review history for audit

  Scenario: Analyze all photos continues through independent outcomes
    Given a Varroa Assessment Inspection has unanalysed and previously failed photos
    And the Inspection has a completed Photo Analysis and a no-bees-found Photo Analysis
    When a Workspace member requests analysis of all photos
    Then HiveSight creates one Photo Analysis Batch for the eligible photos
    And HiveSight analyses each eligible photo independently
    And HiveSight skips the completed and no-bees-found photos
    And HiveSight continues after a photo analysis fails
    And HiveSight reports the batch as completed with issues
```

## Preconditions

- The actor has access to the Workspace.
- The Workspace Data Use Agreement is accepted.
- The Hive has Hive Configuration.
- The Inspection intent is `varroa_assessment`.
- The photo belongs to that Inspection and Workspace and has been accepted at photo intake.
- Slice 0033 Photo Analysis persistence and the replaceable adapter seam are present.

## Settled Decisions

### Product workflow and persistence

- A new **Inspection Photo Bee Evidence** record is a child of a Varroa Photo Analysis and retains a direct `inspection_photo_id` reference for convenience and integrity checks.
- It captures source-photo geometry, complete-visible-bee classification, head orientation, eligibility, normalised crop evidence, detector evidence, adapter/model provenance, and any per-bee failure.
- It does not require a Training Crop. The obsolete product `AnalysisRun` / “Process stub analysis” path is removed from code, UI, local development data, and seeds. Training workflows are not affected.
- A produced outcome is immutable. A future reanalysis with a new model will create a new Photo Analysis and new evidence; that workflow is deferred.
- A retry after a failed attempt creates a new run and retains the original failure. A recovery process marks abandoned `running` attempts as `failed` with a `stale_or_interrupted` reason before allowing retry.
- Raw structured adapter request/response evidence is retained for traceability, with source image references and integrity metadata rather than duplicate image bytes.
- The new durable data shape receives a schema migration and live Postgres persistence verification. Old local development stub records may be discarded; no useful-data migration is required.

### Pipeline semantics

1. Localise complete visible bees from the Inspection Photo.
2. Orient each localised bee head-up.
3. Run Varroa Detection for each successfully oriented bee.
4. Persist the run, evidence, provenance, summary, and caveats.

- The initial deterministic product-photo adapter is an explicit, replaceable development adapter. It uses normalised geometry that scales to portrait or landscape source images and provides a clean completed demonstration path with at least one likely Varroa-positive bee. UI evidence is labelled `Development model evidence`.
- A model-produced orientation with low confidence remains orientation evidence in this first workflow. An absent or unusable orientation is a per-bee failure and makes the Photo Analysis `partial`.
- A Varroa detector failure for a bee is likewise a per-bee failure and makes the Photo Analysis `partial`.
- `no_usable_bees` means no complete bees were localised. The UI says `No bees found`; it is not used for orientation failures.
- Product inference handles complete visible bees only in this slice. Partial-visible-bee policy is deliberately deferred.

### Analysis and batch lifecycle

- The public API is asynchronous. Starting analysis creates a durable `running` Photo Analysis; the Web UI polls it.
- The UI shows stage-level progress (`Finding bees`, `Orienting bees`, `Looking for Varroa`) for an individual photo. Batch UI shows overall progress and per-photo states only.
- Only one active analysis may exist for a photo. The UI disables individual controls during an active batch; the API is the final guard and returns an `analysis_already_running` conflict for repeated starts.
- A completed, partial, or `no_usable_bees` photo cannot be rerun in this slice. The action remains visible but disabled with an explanatory label. A failed photo is retryable.
- `Analyze all photos` snapshots eligible photos at invocation, processes them serially, and continues after a photo-level failure. New uploads wait for the next batch.
- A persisted Photo Analysis Batch retains actor, Workspace, Inspection, requested time, snapshot photo ids, aggregate counts, and per-photo outcomes. It is operational/audit evidence only in this slice.
- Batch states are `running`, `completed`, `completed_with_issues`, and `failed`. Partial, failed, and policy-rejected photo items lead to `completed_with_issues`; `no_usable_bees` alone does not. If the batch coordinator stops before every item is attempted, its batch state is `failed`; unstarted photos remain untouched.
- A photo rejected for ownership, workspace, intent, or another policy problem creates no Photo Analysis run, is not retryable through normal UI, and is reported as a rejected batch item. The beekeeper sees only `This photo could not be analysed`, not internal compliance detail.

### Review and evidence

- Review is photo-analysis-level, reversible, and available to any Workspace member.
- Review statuses remain `unreviewed`, `accepted`, `rejected`, `inconclusive`, and `needs_expert_review`.
- `accepted` means the beekeeper is content for the run to be used later as Advisor evidence; it does not assert complete review or model correctness.
- Only completed and partial runs can be accepted. `failed` and `no_usable_bees` runs cannot be accepted. Accepted is the only backend state that sets `advisor_evidence_eligible`.
- Any non-accepted status requires a note. Changing to accepted clears the current note; changing between non-accepted states preserves it for editing. Append-only review events retain actor, time, status transition, and prior note for audit but are not shown in this slice.
- No Advisor button, label, or trigger appears in the beekeeper UI. The backend eligibility hook remains for later integration.
- Detail evidence mirrors the existing training-side Varroa review interaction: a selected head-up bee crop with linked clean and marked views, plus source photo context showing all bee/head annotations and highlighting the selected bee. Selecting evidence does not create Training Crops, Varroa Review Outcomes, or training data.
- The beekeeper-facing headline is **bees with likely visible Varroa**. Multiple markers on one bee count once. Every individual mite marker and the total likely-mite-detection count are still stored for future detector validation and alcohol-wash/sugar-roll calibration, but that total is not shown in this UI.
- The evidence list puts likely Varroa-positive bees first. It preserves all relevant produced states/caveats so development omissions are not hidden.

## Layers Touched

- Web UI: replace the old Varroa Assessment stub panel with photo-row `Analyze photo`, `Analyze all photos`, running/terminal states, review controls, result summary, and evidence drill-down.
- Core API: asynchronous single-photo and batch orchestration, polling/read endpoints, duplicate-start guard, stale-run recovery, photo-level review update, and batch result shape.
- Product analysis adapters: introduce a composite product-photo pipeline seam that invokes Bee Localisation, Bee Orientation, and Varroa Detection in order. The deterministic development adapter is isolated and replaceable.
- Storage: durable `InspectionPhotoBeeEvidence`, richer `VarroaPhotoAnalysis`, `PhotoAnalysisBatch`, batch item outcomes, and append-only review events.
- Contracts: new internal Web/Core API contracts only. No HiveSight Advisor contract changes or breaking declared external API changes.
- Observability: structured start/stage/completion/failure events, adapter provenance, stage timings, run/batch ids, and count summaries; never log photo bytes.
- Documentation: update `CONTEXT.md`, requirements, product/domain architecture, user guide, roadmap, parking lot, and traceability artefacts to distinguish product Photo Analysis from Training workflows.

## Test Seams

- **Shared acceptance catalogue — product photo analysis**: an Inspection Photo produces a persisted Photo Analysis through all stages without a Training Crop; completed and partial outcomes expose counts and caveats; accepted changes the backend Advisor-eligibility hook.
- **Shared acceptance catalogue — batch analysis**: a batch processes only its snapshot, continues after item failure/rejection, records the aggregate result, and skips produced outcomes on a subsequent batch.
- **Core API workflow tests**: duplicate starts, stale-run recovery, retry history, policy-rejected items, no-usable-bees, partial stage failures, schema/persistence, and adapter provenance.
- **Web acceptance tests**: photo controls and disabled labels, stage progress, batch progress, generic rejection copy, review controls, paired clean/marked evidence, source-photo selection/highlighting, and no Training workflow controls.
- **Visual/interaction tests**: linked zoom/pan and geometry alignment between head-up evidence and source-photo overlays.

## Data Shape

- `VarroaPhotoAnalysis`
  - `id`, `workspace_id`, `inspection_id`, `inspection_photo_id`
  - `status`: `running` | `completed` | `partial` | `failed` | `no_usable_bees`
  - `current_stage`, started/completed timestamps, and `failure_reason`
  - bee counts: localised, eligible, analysed, failed, and likely-Varroa-positive-bee count
  - total likely mite detections (stored, not shown in this UI)
  - caveats, adapter/model provenance, raw structured request/response references
  - review status and current review note

- `InspectionPhotoBeeEvidence`
  - ids for evidence, Workspace, Inspection Photo, and parent Photo Analysis
  - source geometry, complete-visible classification, head orientation/rotation, eligibility, normalised crop metadata
  - detector status, individual mite markers, and per-bee failure detail
  - adapter/model provenance

- `PhotoAnalysisBatch` and batch items
  - actor, Workspace, Inspection, requested time, fixed photo snapshot, lifecycle status, aggregate counts
  - item outcome: `completed`, `partial`, `failed`, `no_usable_bees`, or `rejected`
  - rejected-item reason code retained for audit, with generic UI copy

- `PhotoAnalysisReviewEvent`
  - analysis id, actor, timestamp, from/to status, prior/current note

## Out Of Scope

- A trained production Bee Localisation, Bee Orientation, or Varroa Detection model.
- Inspection-level roll-up, frame-side semantics, duplicate-photo detection, sampling estimator, confidence interval, diagnosis, or treatment threshold.
- Advisor trigger, Advisor UI, and treatment workflow.
- Per-bee/detection human corrections, feedback submission, expert-review queue, or administration response.
- Reanalysis using a newer model.
- Visible review/batch audit history.
- Photo deletion/retention workflow.
- Product-evidence reuse in model training or statistical calibration.
- Support/admin impersonation.

## Acceptance Criteria

- [ ] A Varroa Assessment Inspection Photo has a one-action `Analyze photo` workflow that uses no Training Crop.
- [ ] The analysis is durable and asynchronous, exposes individual stage progress, and prevents duplicate active runs.
- [ ] It persists Photo Analysis, Inspection Photo Bee Evidence, model provenance, all individual mite markers, and per-bee failures.
- [ ] Complete localised bees with usable orientation are analysed; unusable orientation/detector errors produce an auditable partial result.
- [ ] `no_usable_bees` means no bees found and cannot be accepted.
- [ ] The UI reports bees with likely visible Varroa, not a diagnostic rate or total mite count.
- [ ] The evidence screen provides paired clean/marked head-up views and selected-bee source-photo context without creating training evidence.
- [ ] Review is reversible, records audit events, requires a note for non-acceptance, and only accepted runs set the backend Advisor-eligibility hook.
- [ ] `Analyze all photos` is a persisted, serial convenience batch with a fixed snapshot and resilient per-photo outcomes.
- [ ] Invalid policy/ownership items are rejected without a Photo Analysis run or normal retry path.
- [ ] Gherkin lives in the capability-based acceptance catalogue; focused API, Web, persistence, and visual tests cover the remaining seams.
- [ ] `pnpm verify:slice` passes and live Postgres persistence verification is completed or explicitly recorded pending.

## Deferred Follow-Up

The dedicated parking-lot entries record the revisit triggers for confidence policy, partial-visible-bee product inference, corrective-feedback/expert-review workflow, model-version reanalysis, photo deletion and retention, product-evidence training/statistical governance, and support impersonation.
