# Vertical Slice 0019: Reviewer Work Queue

## Purpose

Make the seeded development Users from Slice 0018 behaviourally meaningful by adding the first shared review workflow.

A Dataset Curator can make a completed Training Crop available for review. Any eligible Reviewer can see it in a shared Reviewer Work Queue, provided conflict rules do not disqualify them. The Reviewer can open the limited evidence needed for review and record a task-level review outcome. The Reviewer does not become a Workspace Member and does not gain broad access to the source Workspace.

This slice proves the access pattern HiveSight will need for future Blind Independent Review, Third-Party Adjudication, contributor tasks, and external review work without creating brittle named reviewer assignments as the primary operating model.

## Source Inputs

- `CONTEXT.md`
- `requirements/roadmap.md`
- `architecture/parking-lot.md`, especially `PARK-0039: Assigned Review And Contribution Task Inbox`
- `architecture/vertical-slice-0018-dev-user-and-role-switching.md`
- `architecture/vertical-slice-0015.3-dataset-repository-browser.md`
- `architecture/adr/0007-three-stage-bee-localisation-orientation-and-varroa-pipeline.md`
- Current Core API dev auth seam: `x-hivesight-dev-user-id`
- Current Web API seam: `CoreApiClient`

## User Path

Given a Dataset Curator has completed Training Crop evidence in their own Workspace
When the Dataset Curator requests review for the Training Crop
Then eligible Reviewer Users see the item in a shared `Review Work` page
And a Reviewer who did not request, create, curate, or already review the item can open only the queued crop evidence
And the first eligible Reviewer completion closes the queue item for everyone
And the Dataset Curator can see the review request status and outcome without changing Dataset Item eligibility automatically.

## Preconditions

- Slice 0018 is complete.
- Development User switching is enabled in local development.
- The `NO-CAPABILITY` development persona is renamed to `BASIC-OWNER` so manual QA language reflects that the User owns a Workspace but has no elevated internal capabilities.
- Training Crop annotation, crop evidence viewing, and Dataset Curator capability checks already exist.
- The source Training Crop belongs to the requesting Dataset Curator's active Workspace.
- The Training Crop is `review_complete` and has at least one reviewed bee ellipse.
- Workspace Data Use Agreement remains accepted for the source Workspace.
- The Review Queue eligibility rule excludes:
  - the User who requested the review;
  - the User who completed the Training Crop review being queued;
  - any User who has already completed a Review Queue Outcome for the item.

## End-To-End Behaviour

The Dataset Curator opens a completed Training Crop and clicks `Request review`. Review request notes are optional, but the UI should warn or guide the Curator that notes should be neutral because they are visible to the Reviewer.

The Core API creates a Review Queue Item with:

- a human-readable queue id, such as `HS-RQ-000001`;
- source Workspace id for authorization/audit only;
- requested-by User id for conflict checks and curator-side visibility only;
- subject type `training_crop`;
- subject id;
- status `available`;
- optional request notes;
- requested timestamp;
- immutable task evidence snapshot metadata.

Only one active `available` Review Queue Item may exist for the same Training Crop at a time. After an item is `completed` or `cancelled`, the Dataset Curator may request another review for the same Training Crop as a new queue item, and previous review history remains visible where appropriate.

The Dataset Curator can cancel an `available` Review Queue Item before any Reviewer completes it. Cancellation requires notes. Once a queue item has a completed Review Queue Outcome, the outcome is immutable and the queue item cannot be cancelled or deleted.

While a Training Crop has an `available` Review Queue Item, editing the Training Crop is blocked in this slice. The Curator can cancel the queue item, edit the crop, and request review again. Reviewers judge the request-time evidence snapshot, not a moving target.

A Reviewer switches to `REVIEWER-1`, `REVIEWER-2`, or `REVIEWER-3` in the Development session panel and sees a separate `Review Work` page. This page is visible only to Users with Reviewer capability. It lists all locally queued items for which the selected Reviewer is eligible, sorted oldest first. The first implementation has no filters, priorities, claiming, leases, or named assignments.

Reviewers see only eligible available items. They do not see ineligible items or reasons for exclusion. If several eligible Reviewers can see the same item, the first valid completion wins. A later concurrent completion attempt fails cleanly with a domain error such as `review_queue_item_already_completed`, and the UI refreshes.

An eligible Reviewer opens a queue item and sees only safe task evidence:

- Training Crop image;
- reviewed bee ellipses from the request-time snapshot;
- safe crop/source label;
- Training Crop id or human-readable crop label;
- crop dimensions;
- reviewed bee count;
- complete visible bee count;
- partial visible bee count;
- crop status and visible bee status;
- review request notes;
- requested timestamp.

The Reviewer must not see raw source filenames by default, requester identity, original crop reviewer identity, Apiary name, Hive name, Workspace name, full inspection history, other photos, repository context, model context, Dataset Version context, Training Run context, or Benchmark Evaluation context.

The Reviewer records one task-level outcome:

- `approved`;
- `changes_requested`;
- `not_determined`.

`changes_requested` and `not_determined` require notes. `approved` may include optional notes. The first implementation is deliberately task-level. It does not require the Reviewer to edit individual ellipses or produce a second independent annotation set.

When the first eligible Reviewer completes a queue review, the Review Queue Item status becomes `completed` for everyone. The completed outcome records reviewer id, timestamp, outcome, and notes. The item no longer appears in any Reviewer's available work queue. Review Queue Outcomes are not visible to other Reviewers in this slice.

The Reviewer has a separate read-only Review History surface showing the queue items they completed, using human-readable queue ids. This is visually separate from available Review Work.

The Dataset Curator has a `Requested Reviews` view or list showing their requested items, so they can see what is waiting, completed, or cancelled. It is read-only apart from pre-review cancellation. The Curator-side list shows:

- queue id;
- Training Crop id or label;
- safe source label;
- requested timestamp;
- status: `available`, `completed`, or `cancelled`;
- completed outcome when present;
- reviewer code/display identity when completed;
- cancellation status and cancellation notes when cancelled.

Dataset Curator-side `Requested Reviews` is limited to Dataset Curator Users in this slice, not ordinary Workspace Owners. Repository detail may show a compact status summary for the relevant Training Crop, but it must not become a full review dashboard.

Completing a queue review does not automatically change the Training Crop, Dataset Item eligibility, Dataset Role, Dataset Version, Training Run, or Model Candidate. `approved` is evidence for the Curator; it is not automatic dataset promotion. A Curator can request review for a Training Crop already assigned to a Dataset Item or consumed by a Dataset Version or Training Run, but the UI must show a curator-side warning that the review is retrospective and no downstream artifact will be changed automatically.

Review Queue access is not Workspace Membership. A Reviewer may see queued items from another Workspace through task/evidence scoped access, but must not be able to list or browse that Workspace's Apiaries, Hives, Inspections, other photos, other crops, Dataset Items, Dataset Versions, Training Runs, Model Candidates, or Benchmark Evaluations through the queue item.

## Layers Touched

- Web UI: Add `Review Work` page for Reviewer Users; add `Request review` and cancellation controls for Dataset Curator; add `Requested Reviews` curator-side list; add Reviewer History; hide impossible surfaces for Users without capability.
- Core API: Add Review Queue request/list/detail/complete/cancel endpoints with capability, eligibility, conflict, and limited task-access checks.
- Analysis Service: Not touched.
- Storage: Persist Review Queue Items and Review Queue Outcomes in in-memory and Postgres-backed stores.
- Queue or async boundary: Not touched.
- Contracts: Add request/response models for Review Queue Item creation, listing, detail, completion, cancellation, and curator/requester status views.
- Observability: Record enough local queue status, actor, and domain-error information to debug review requests without leaking unsafe evidence to Reviewers.

## Test Seams

- Seam: Core API review request creation.
- Behaviour verified: Dataset Curator can request review for a completed Training Crop; non-curator cannot; incomplete, excluded, empty, editable-pending, or duplicate-active crops cannot be queued.
- Test style: API test plus API-level BDD scenario.

- Seam: Core API queue eligibility.
- Behaviour verified: Reviewer Users see available items they are eligible to review; requester, original crop reviewer, already-completed reviewer, ordinary owner, contributor, and `BASIC-OWNER` are excluded.
- Test style: API test plus API-level BDD scenario.

- Seam: Core API limited queue item access.
- Behaviour verified: eligible Reviewer can read queued crop evidence; ineligible Reviewer and ordinary Workspace Owner cannot; eligible Reviewer still cannot browse the source Workspace.
- Test style: API test plus API-level BDD scenario.

- Seam: Core API queue review completion.
- Behaviour verified: eligible Reviewer can complete the item with `approved`, `changes_requested`, or `not_determined`; notes are required for `changes_requested` and `not_determined`; non-reviewer and ineligible users cannot complete it; completed outcome is immutable; first completion wins.
- Test style: API test plus API-level BDD scenario.

- Seam: Core API queue cancellation.
- Behaviour verified: Dataset Curator can cancel an available item with notes; Reviewer cannot cancel; completed item cannot be cancelled; cancelled item can be re-requested as a new queue item.
- Test style: API test.

- Seam: Web UI capability-specific surfaces.
- Behaviour verified: Dataset Curator sees `Request review` and `Requested Reviews`; Reviewer sees `Review Work` and Review History; ordinary owner, contributor, and `BASIC-OWNER` do not see impossible review/curation actions.
- Test style: Playwright acceptance test.

- Seam: Web UI switching flow.
- Behaviour verified: after review is requested, switching from Curator to Reviewer clears the prior workspace state and shows eligible queue work without exposing the Curator's broader Workspace.
- Test style: Playwright acceptance test.

- Seam: Postgres persistence.
- Behaviour verified: Review Queue Items, cancellations, and completed Review Queue Outcomes survive Core API restart in Postgres-backed mode.
- Test style: opt-in Postgres integration test.

## API-Level Acceptance Scenarios For Signoff

```gherkin
Feature: Reviewer Work Queue

  Scenario: Dataset Curator requests review for a completed Training Crop
    Given a Dataset Curator has a completed Training Crop with reviewed bee ellipses
    When the Dataset Curator requests review for that Training Crop
    Then a Review Queue Item is created with status "available"
    And the Review Queue Item has a human-readable queue id
    And the Training Crop cannot be edited while the Review Queue Item is available

  Scenario: Eligible Reviewers see shared review work without named assignment
    Given a Dataset Curator has requested review for a completed Training Crop
    When an eligible Reviewer views Review Work
    Then the Reviewer sees the available Review Queue Item
    And the Review Queue Item is sorted with older available work first
    And the Reviewer can open the queued crop evidence

  Scenario: Requester and original crop reviewer are excluded from reviewing the same item
    Given a Dataset Curator has requested review for a completed Training Crop
    When the requesting User views Review Work
    Then the Review Queue Item is not listed
    When the User who completed the original Training Crop review views Review Work
    Then the Review Queue Item is not listed

  Scenario: Queue evidence exposes only safe review metadata
    Given a Dataset Curator has requested review for a completed Training Crop
    When an eligible Reviewer opens the Review Queue Item
    Then the Reviewer sees the Training Crop image and reviewed bee ellipses
    And the Reviewer sees the safe crop label, crop dimensions, reviewed bee counts, request notes, and requested timestamp
    And the Reviewer does not see the raw source filename
    And the Reviewer does not see the requester identity
    And the Reviewer does not see the original crop reviewer identity
    And the Reviewer does not see Apiary, Hive, Workspace, inspection history, model, training, or dataset-version context

  Scenario: First eligible completion closes the shared queue item
    Given two eligible Reviewers can see the same available Review Queue Item
    When one Reviewer completes the Review Queue Item as "approved"
    Then the Review Queue Item status becomes "completed"
    And the Review Queue Item is no longer available to any Reviewer
    And another Reviewer cannot complete the same Review Queue Item

  Scenario: Changes requested and not determined outcomes require notes
    Given an eligible Reviewer has opened an available Review Queue Item
    When the Reviewer tries to complete the item as "changes_requested" without notes
    Then the completion is rejected
    When the Reviewer tries to complete the item as "not_determined" without notes
    Then the completion is rejected

  Scenario: A Reviewer cannot complete the same queue item twice
    Given an eligible Reviewer has completed a Review Queue Item
    When that Reviewer views Review Work again
    Then the Review Queue Item is not listed as available work
    And the Reviewer cannot submit another outcome for that Review Queue Item

  Scenario: Dataset Curator cancels an available review request
    Given a Dataset Curator has an available Review Queue Item for a Training Crop
    When the Dataset Curator cancels the Review Queue Item with cancellation notes
    Then the Review Queue Item status becomes "cancelled"
    And the Training Crop can be edited again
    And the Dataset Curator can request a new review for the Training Crop

  Scenario: Review queue access is not Workspace Membership
    Given an eligible Reviewer can open a Review Queue Item from another User's Workspace
    When the Reviewer tries to browse that Workspace's Apiaries, Hives, Inspections, other photos, other crops, Dataset Items, Dataset Versions, Training Runs, Model Candidates, or Benchmark Evaluations
    Then access is denied
```

UI-level Gherkin remains deliberately deferred. Slice 0019 uses Playwright for UI acceptance, and API-level Gherkin for the business rules above.

## Data Shape

Minimum Review Queue Item:

- `review_queue_item_id`
- `human_readable_id`, for example `HS-RQ-000001`
- `workspace_id`
- `subject_type`: generic shape, but only `training_crop` behaviour is supported in Slice 0019
- `subject_id`
- `requested_by_user_id`
- `status`: `available`, `completed`, `cancelled`
- `request_notes`
- `requested_at`
- `cancelled_at`
- `cancelled_by_user_id`
- `cancellation_notes`
- `completed_at`
- `completed_by_outcome_id`
- `evidence_snapshot`

Minimum Review Queue Outcome:

- `review_queue_outcome_id`
- `review_queue_item_id`
- `reviewer_id`
- `review_outcome`: `approved`, `changes_requested`, `not_determined`
- `review_notes`
- `created_at`

Minimum evidence snapshot:

- safe crop/source label;
- Training Crop id or human-readable label;
- crop coordinates;
- crop image dimensions;
- reviewed ellipse snapshot;
- reviewed ellipse count;
- complete visible bee count;
- partial visible bee count;
- crop review status when queued;
- visible bee status when queued;
- requested timestamp.

The evidence snapshot stores metadata and references, not duplicated image bytes. The first implementation may render image bytes from the canonical source image reference, but the review judgement is against the request-time snapshot metadata and reviewed ellipse geometry.

Review Queue Outcome storage may allow many outcomes in the long-term data model, but Slice 0019 domain rules permit only one completed outcome per Review Queue Item.

## Out Of Scope

- Contributor task inboxes.
- Contribution Bundles and permission acceptance.
- Blind Independent Review.
- Third-Party Adjudication.
- Per-ellipse reviewer correction.
- Reviewer-created replacement annotations.
- Reviewer disagreement metrics.
- Varroa Review Outcomes.
- Named reviewer assignment as the primary workflow.
- Reviewer claiming, leases, timeouts, holiday cover, or work stealing.
- Multi-review requirements, such as requiring two independent outcomes before completion.
- Queue priority, filters, geography, organization, expertise, or source-group routing.
- Reviewers seeing why they are ineligible for specific items.
- Review Queue Outcomes being visible to other Reviewers.
- Email, notifications, or real-time updates.
- Workspace collaboration or sharing.
- Real authentication provider integration.
- General role administration.
- Automatic Dataset Item eligibility, Dataset Role, Dataset Version, Training Run, Model Candidate, or Benchmark Evaluation mutation based on queue outcomes.

## Acceptance Criteria

- [x] Dataset Curator can request review for a completed Training Crop from the Training Crop panel.
- [x] Dataset Curator cannot request review for an incomplete, excluded, empty, currently queued, or edit-locked Training Crop.
- [x] User without Dataset Curator capability cannot create Review Queue Items.
- [x] Review Queue Items have human-readable ids such as `HS-RQ-000001`.
- [x] Review request notes are optional and visible to Reviewers.
- [x] Reviewer Users see a `Review Work` page when selected in the local Development session.
- [x] `Review Work` lists only available items the selected Reviewer is eligible to review, oldest first.
- [x] A User who requested review for an item cannot review that item.
- [x] A User who completed the Training Crop review cannot review that item.
- [x] A User who already completed a Review Queue Outcome for an item cannot review it again.
- [x] `REVIEWER-1`, `REVIEWER-2`, and `REVIEWER-3` can all see the same available item when eligible.
- [x] The first eligible completion closes the queue item for every Reviewer.
- [x] A second concurrent completion attempt fails cleanly and the UI refreshes.
- [x] Eligible Reviewer can open the queue item and view only safe queued crop evidence.
- [x] Eligible Reviewer cannot see raw source filename, requester identity, original crop reviewer identity, Apiary name, Hive name, Workspace name, full inspection history, other photos, repository context, model context, Dataset Version context, Training Run context, or Benchmark Evaluation context.
- [x] Eligible Reviewer cannot browse the source Workspace's wider Apiaries, Hives, Inspections, photos, crops, repository, model runs, dataset evidence, or benchmark evidence through the queue item.
- [x] Ordinary owner, contributor, and `BASIC-OWNER` Users do not see the `Review Work` product surface unless they also have Reviewer capability.
- [x] Eligible Reviewer can complete a queue review as `approved`, `changes_requested`, or `not_determined`.
- [x] `changes_requested` and `not_determined` require notes.
- [x] Completed outcomes are immutable and retain reviewer id, timestamp, outcome, and notes.
- [x] Review Queue Outcomes are not visible to other Reviewers in this slice.
- [x] Reviewer History shows completed reviews separately from available Review Work, using human-readable queue ids.
- [x] Dataset Curator can see `Requested Reviews` with available, completed, and cancelled statuses.
- [x] Dataset Curator can see the completing Reviewer code/display identity after completion.
- [x] Dataset Curator can cancel an available review request before completion, with required cancellation notes.
- [x] Reviewer cannot cancel a queue item.
- [x] Completed queue items cannot be cancelled or deleted.
- [x] Cancelled or completed queue items allow the Dataset Curator to request a new review for the same Training Crop.
- [x] Training Crop editing is blocked while an available Review Queue Item exists for that crop.
- [x] Queue outcomes do not automatically change Training Crop status, Dataset Item eligibility, Dataset Role, Dataset Version, Training Run, Model Candidate, or Benchmark Evaluation.
- [x] Curator can request retrospective review for a Training Crop already assigned to a Dataset Item or consumed by a Dataset Version/Training Run, but sees a warning that downstream artifacts will not change automatically.
- [x] Repository detail shows at most a compact review status summary for the relevant Training Crop, not a full review browser.
- [x] API-level Gherkin scenarios cover creation, eligibility, safe metadata minimisation, completion closure, repeat-review blocking, cancellation, and workspace-boundary preservation.
- [x] Playwright acceptance covers requesting review as Curator, switching to Reviewer, seeing and completing eligible queue work, and confirming ordinary/no-capability users do not see impossible surfaces.
- [x] Review Queue Items and Review Queue Outcomes persist in Postgres-backed local development mode.
- [x] `docs/user-guide.md` explains how to request review, complete Review Work, see Requested Reviews, cancel pending review requests, and interpret the limits of a queue outcome.

## Open Questions

None before implementation.

## Parked Follow-Up Work

- Multi-review requirements, Blind Independent Review, and Third-Party Adjudication.
- Reviewer claiming, leases, stale work recovery, and operational queue management.
- Reviewer correction workflow for proposing replacement annotation geometry or classifications.
- Contributor task queues and Contribution Bundles.
- Queue routing by geography, source group, organization, expertise, or subject type.
- UI-level Gherkin harness for cross-role review workflows.
