# Vertical Slice 0034: One-Click Varroa Photo Analysis Workflow

Status: implemented; Core API acceptance, focused API/Web checks, and `pnpm verify:slice` passed on 2026-08-07. Live Postgres migration verification was not recorded in the latest generated slice report.

## Purpose

Let a Beekeeper analyse an uploaded Varroa Assessment Inspection Photo through one visible `Analyze photo` action. HiveSight runs Bee Localisation, Bee Orientation, and Varroa Detection as one asynchronous product workflow, persists the resulting evidence, and lets any Workspace member inspect and review it.

The beekeeper does not select Training Crops or individual model stages. This slice removes the older stub-analysis path from the Varroa Assessment user flow. Training Inspection model-curation workflows remain separate and unchanged.

## User Path

Given a configured Hive has a Varroa Assessment Inspection with one or more accepted Inspection Photos,
when a Workspace member selects `Analyze photo` for one unanalysed or previously failed photo,
then HiveSight runs the complete photo pipeline, stores a durable Varroa Photo Analysis and Inspection Photo Bee Evidence, and shows a clear result with evidence and caveats.

`Analyze all photos` is a convenience request that processes a fixed snapshot of eligible photos serially. It is not an inspection-level scientific result.

## Implemented Acceptance Scenarios

The implemented canonical acceptance feature is API-bound. Browser-specific workflow and evidence checks remain in Playwright acceptance coverage.

```gherkin
@api
Feature: Varroa photo analysis workflow

  Scenario: A beekeeper analyses one Varroa Assessment photo
    Given a Workspace member has a Varroa Assessment Inspection with an uploaded photo
    And that photo has no prior Photo Analysis
    When the Workspace member requests photo analysis
    Then HiveSight starts one Photo Analysis for that Inspection Photo
    And HiveSight reports the Photo Analysis as unreviewed
    And HiveSight reports the number of analysed eligible bees and bees with likely visible Varroa
    And HiveSight does not require a Training Crop

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

  Scenario: Review status controls later Advisor evidence eligibility
    Given a completed or partial Photo Analysis is unreviewed
    When a Workspace member marks it accepted
    Then HiveSight marks deterministic Photo Analysis as development integration evidence
    When a Workspace member changes it to needs expert review with a note
    Then HiveSight marks it ineligible for later Advisor evidence
```

Additional focused API tests cover product Photo Analysis without Training Crops, head-up evidence image retrieval, duplicate produced-run prevention, batch skipping for produced results, no-usable-bees review rules, review-derived Advisor evidence eligibility, and required notes for non-accepted review statuses.

Browser acceptance coverage exercises the Varroa Assessment UI path: photo upload, visible `Analyze photo` controls, no Training workflow controls, result evidence display, paired source/head-up evidence, reversible review controls, and resume after Development User switching.

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
- It does not require a Training Crop. The older product `AnalysisRun` / `Process analysis` path is no longer the Varroa Assessment user path; the Web UI exposes `Analyze photo` and `Analyze all photos` for Varroa Assessment inspections. Training workflows are not affected.
- A produced outcome is immutable. A future reanalysis with a new model will create a new Photo Analysis and new evidence; that workflow is deferred.
- A completed, partial, or no-usable-bees outcome is treated as produced evidence and cannot be started again in this slice. Failed retry and stale-running recovery remain follow-on hardening unless explicitly covered by a later implementation pass.
- The persisted run and per-bee evidence retain source image references, source geometry, adapter/model provenance, detections, and per-bee failure detail without duplicating image bytes.
- The new durable data shape received schema migration `0034_product_photo_analysis_evidence.sql`. The latest generated slice report does not record live Postgres migration verification for this slice.

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

- The public API starts analysis with a `202` response and creates a `running` Photo Analysis before background processing completes.
- The UI shows terminal result status and evidence after refresh. Fine-grained per-stage progress text (`Finding bees`, `Orienting bees`, `Looking for Varroa`) is not part of the delivered browser surface.
- Only one produced analysis may exist for a photo in this slice. The UI disables individual controls once an analysis exists; the API returns `photo_analysis_already_produced` when a produced result is started again.
- A completed, partial, or `no_usable_bees` photo cannot be rerun in this slice. The action remains visible but disabled with an explanatory label.
- `Analyze all photos` snapshots eligible photos at invocation, processes them serially, and continues after a photo-level failure. New uploads wait for the next batch.
- A persisted Photo Analysis Batch records Workspace, Inspection, attempted photo ids, skipped photo ids, produced runs, status, and timestamps. It is operational evidence only in this slice.
- Batch states are `completed`, `completed_with_issues`, and `failed`. Partial or failed produced runs lead to `completed_with_issues`; completed and no-usable-bees produced results are skipped by later batches.
- Detailed policy-rejected batch item records remain follow-on hardening; this slice keeps the API guard at the individual workflow boundary.

### Review and evidence

- Review is photo-analysis-level, reversible, and available to any Workspace member.
- Review statuses remain `unreviewed`, `accepted`, `rejected`, `inconclusive`, and `needs_expert_review`.
- `accepted` means the beekeeper is content for the run to be used later as Advisor evidence; it does not assert complete review or model correctness.
- Only completed and partial runs can be accepted. `failed` and `no_usable_bees` runs cannot be accepted. Slice 0035 replaces the original boolean hook with `advisor_evidence_eligibility`, which derives current Advisor evidence eligibility from accepted review plus the frozen confidence-policy outcome.
- Any non-accepted status requires a note. Changing review status updates the current review status and note on the Photo Analysis. Append-only review event history remains a follow-on audit hardening item; it is not surfaced in the delivered response shape.
- No Advisor button, label, or trigger appears in the beekeeper UI. The backend eligibility hook remains for later integration.
- Detail evidence mirrors the existing training-side Varroa review interaction: a selected head-up bee crop with linked clean and marked views, plus source photo context showing all bee/head annotations and highlighting the selected bee. Selecting evidence does not create Training Crops, Varroa Review Outcomes, or training data.
- The beekeeper-facing headline is **bees with likely visible Varroa**. Multiple markers on one bee count once. Every individual mite marker and the total likely-mite-detection count are still stored for future detector validation and alcohol-wash/sugar-roll calibration, but that total is not shown in this UI.
- The evidence list puts likely Varroa-positive bees first. It preserves all relevant produced states/caveats so development omissions are not hidden.

## Layers Touched

- Web UI: replace the old Varroa Assessment stub panel with photo-row `Analyze photo`, `Analyze all photos`, terminal result states, review controls, result summary, and evidence drill-down.
- Core API: single-photo start/read workflow, background processing, batch convenience orchestration, produced-run guard, photo-level review update, and batch result shape.
- Product analysis adapters: introduce a composite product-photo pipeline seam that invokes Bee Localisation, Bee Orientation, and Varroa Detection in order. The deterministic development adapter is isolated and replaceable.
- Storage: durable `InspectionPhotoBeeEvidence`, richer `VarroaPhotoAnalysis`, and `PhotoAnalysisBatch` response persistence. Detailed batch item outcomes and append-only review events remain follow-on hardening.
- Contracts: new internal Web/Core API contracts only. No HiveSight Advisor contract changes or breaking declared external API changes.
- Observability: response and error shapes expose run ids, batch ids, adapter provenance, status, caveats, and count summaries. Richer structured logs and stage timings remain follow-on hardening; photo bytes must not be logged.
- Documentation: update `CONTEXT.md`, requirements, product/domain architecture, user guide, roadmap, parking lot, and traceability artefacts to distinguish product Photo Analysis from Training workflows.

## Test Seams

- **Acceptance catalogue — product photo analysis**: an Inspection Photo produces a persisted Photo Analysis without a Training Crop; completed and partial outcomes expose counts and caveats; accepted changes the backend Advisor-eligibility hook.
- **Focused Core API workflow tests**: product Photo Analysis without Training Crops, duplicate produced-run prevention, batch skipping for produced results, no-usable-bees, partial detector failures, review note rules, Advisor eligibility, and head-up image retrieval.
- **Web acceptance tests**: photo controls and disabled labels, review controls, paired clean/marked evidence, source-photo selection/highlighting, resume after Development User switching, and no Training workflow controls.
- **Future hardening seams**: stale-run recovery, retry after failed attempts, detailed policy-rejected batch item outcomes, append-only review event audit, and linked zoom/pan geometry alignment remain available follow-ons.

## Data Shape

- `VarroaPhotoAnalysis`
  - `id`, `workspace_id`, `inspection_id`, `inspection_photo_id`
  - `status`: `running` | `completed` | `partial` | `failed` | `no_usable_bees`
  - `current_stage`, started/completed timestamps, and `failure_reason`
  - bee counts: localised, eligible, analysed, failed, and likely-Varroa-positive-bee count
  - total likely mite detections (stored, not shown in this UI)
  - caveats and adapter/model provenance
  - review status and current review note

- `InspectionPhotoBeeEvidence`
  - ids for evidence, Workspace, Inspection Photo, and parent Photo Analysis
  - source geometry, complete-visible classification, head orientation/rotation, eligibility, normalised crop metadata
  - detector status, individual mite markers, and per-bee failure detail
  - adapter/model provenance

- `PhotoAnalysisBatch` and batch items
  - Workspace, Inspection, requested time, attempted photo ids, skipped photo ids, lifecycle status, and produced runs
  - detailed per-photo batch item outcomes remain follow-on hardening

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

- [x] A Varroa Assessment Inspection Photo has a one-action `Analyze photo` workflow that uses no Training Crop.
- [x] The analysis creates a durable running record, is processed through the background task path, and prevents duplicate produced runs.
- [x] It persists Photo Analysis, Inspection Photo Bee Evidence, model provenance, individual mite detections, and per-bee failures.
- [x] Complete localised bees with usable orientation are analysed; detector errors produce an auditable partial result in the delivered test path.
- [x] `no_usable_bees` means no bees found and cannot be accepted.
- [x] The UI reports bees with likely visible Varroa, not a diagnostic rate or total mite count.
- [x] The evidence screen provides paired clean/marked head-up views and selected-bee source-photo context without creating training evidence.
- [x] Review is reversible, requires a note for non-acceptance, and only accepted runs set the backend Advisor-eligibility hook.
- [x] `Analyze all photos` is a persisted convenience batch that skips already produced results and records attempted/skipped photo ids.
- [x] Gherkin lives in the capability-based acceptance catalogue for the API seam; browser behaviour is covered by Playwright acceptance.
- [x] `pnpm verify:slice` passed on 2026-08-07.
- [ ] Live Postgres persistence verification for migration `0034_product_photo_analysis_evidence.sql` is not recorded in the latest generated slice report.
- [ ] Detailed policy-rejected batch item records, failed-run retry/stale-run recovery, and append-only review event audit remain follow-on hardening.

## Deferred Follow-Up

The dedicated parking-lot entries record the revisit triggers for confidence policy, partial-visible-bee product inference, corrective-feedback/expert-review workflow, model-version reanalysis, photo deletion and retention, product-evidence training/statistical governance, and support impersonation.
