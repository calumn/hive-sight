# Vertical Slice 0019: Assigned Review Task Inbox

## Purpose

Make the seeded development Users from Slice 0018 behaviourally meaningful by adding the first assigned review workflow.

A Dataset Curator can assign a completed Training Crop to a specific Reviewer. That Reviewer can see the task in a Review Inbox, open the limited evidence needed for the assignment, and record a task-level review outcome. The Reviewer does not become a Workspace Member and does not gain broad access to the source Workspace.

This slice proves the access pattern HiveSight will need for future Blind Independent Review, Third-Party Adjudication, contributor tasks, and external review work.

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
And one or more seeded Reviewer Users exist
When the Dataset Curator assigns the Training Crop to `REVIEWER-1`
Then `REVIEWER-1` sees the task in a Review Inbox
And can open only the assigned crop evidence
And can record a review outcome
And `OWNER-A`, `OWNER-B`, `CONTRIBUTOR-1`, and `NO-CAPABILITY` cannot see or complete that assigned review task.

## Preconditions

- Slice 0018 is complete.
- Development User switching is enabled in local development.
- Training Crop annotation, crop evidence viewing, and Dataset Curator capability checks already exist.
- The assigned Reviewer is a known User with Reviewer capability.
- The source Training Crop belongs to the assigning Dataset Curator's active Workspace.
- The Training Crop is `review_complete` and has at least one reviewed bee ellipse.
- Workspace Data Use Agreement remains accepted for the source Workspace.

## End-To-End Behaviour

The Dataset Curator opens a completed Training Crop or a Dataset Repository detail view and clicks `Assign review`. The first implementation may keep the control simple: choose a seeded Reviewer from a list and add optional notes.

The Core API creates an Assigned Review Task with:

- source Workspace id;
- assigned Reviewer id;
- assigned by User id;
- subject type `training_crop`;
- subject id;
- status `assigned`;
- immutable task evidence snapshot metadata.

The assigned Reviewer switches to `REVIEWER-1` in the Development session panel and sees a `Review Inbox` product surface. The Inbox lists only tasks assigned to that Reviewer. The Reviewer opens a task and sees:

- Training Crop image;
- reviewed bee ellipses;
- source filename or safe source label;
- crop status and visible bee status;
- assignment notes;
- enough provenance to understand what is being reviewed.

The Reviewer records a task-level outcome:

- `approved`;
- `changes_requested`;
- `not_determined`.

The first implementation is deliberately task-level. It does not require the Reviewer to edit individual ellipses or produce a second independent annotation set. That deeper workflow belongs with Blind Independent Review and Varroa benchmark governance.

When the task is completed, the task status becomes `completed`, the outcome is retained with reviewer id and timestamp, and the task remains visible in the Reviewer's Inbox history. The Dataset Curator can see task status and outcome from the source crop or repository detail.

Reviewer task access is not Workspace Membership. The Reviewer must not be able to list the source Workspace's Apiaries, Hives, Inspections, other photos, other crops, Dataset Items, Dataset Versions, Training Runs, Model Candidates, or Benchmark Evaluations through this task.

## Layers Touched

- Web UI: Add Review Inbox page for Reviewer Users; add Assign Review control for Dataset Curator; show assigned task status/outcome on relevant crop or repository detail.
- Core API: Add Assigned Review Task create/list/detail/complete endpoints with capability and limited task-access checks.
- Analysis Service: Not touched.
- Storage: Persist Assigned Review Tasks in in-memory and Postgres-backed stores.
- Queue or async boundary: Not touched.
- Contracts: Add request/response models for Assigned Review Task creation, listing, detail, and completion.
- Observability: Record enough local task status and actor information to debug assignments.

## Test Seams

- Seam: Core API assignment creation.
- Behaviour verified: Dataset Curator can assign a completed Training Crop to a Reviewer; non-curator cannot; non-reviewer cannot be assigned.
- Test style: API test.

- Seam: Core API limited task access.
- Behaviour verified: assigned Reviewer can read the assigned crop task evidence; unassigned Reviewer and ordinary Workspace Owner cannot; assigned Reviewer still cannot browse the source Workspace.
- Test style: API test.

- Seam: Core API task completion.
- Behaviour verified: assigned Reviewer can complete the task with `approved`, `changes_requested`, or `not_determined`; non-reviewer and unassigned users cannot complete it.
- Test style: API test.

- Seam: Web UI role-specific surfaces.
- Behaviour verified: Dataset Curator sees `Assign review`; Reviewer sees `Review Inbox`; ordinary owner and no-capability user do not see impossible review/curation actions.
- Test style: Playwright acceptance test.

- Seam: Web UI switching flow.
- Behaviour verified: after a task is assigned, switching from Curator to Reviewer clears the prior workspace state and shows the Review Inbox task without exposing the Curator's broader Workspace.
- Test style: Playwright acceptance test.

- Seam: Postgres persistence.
- Behaviour verified: Assigned Review Task survives Core API restart in Postgres-backed mode.
- Test style: opt-in Postgres integration test.

## Data Shape

Minimum Assigned Review Task:

- `assigned_review_task_id`
- `workspace_id`
- `subject_type`: initially `training_crop`
- `subject_id`
- `assigned_to_user_id`
- `assigned_by_user_id`
- `status`: `assigned`, `completed`, `cancelled`
- `review_outcome`: `approved`, `changes_requested`, `not_determined`, or null
- `assignment_notes`
- `review_notes`
- `created_at`
- `completed_at`
- `evidence_snapshot`

Minimum evidence snapshot:

- source filename or safe source label;
- Training Crop id;
- crop coordinates;
- crop image dimensions;
- reviewed ellipse count;
- complete visible bee count;
- partial visible bee count;
- current crop review status when assigned.

The evidence snapshot is for auditability and task list context. The first implementation may still render the current crop image and current ellipses from canonical stored evidence, but must record enough assignment-time context to show what was assigned.

## Out Of Scope

- Contributor task inboxes.
- Contribution Bundles and permission acceptance.
- Blind Independent Review.
- Third-Party Adjudication.
- Per-ellipse reviewer correction.
- Reviewer-created replacement annotations.
- Reviewer disagreement metrics.
- Varroa Review Outcomes.
- Reviewer assignment algorithms or queues.
- Email, notifications, or real-time updates.
- Workspace collaboration or sharing.
- Real authentication provider integration.
- General role administration.

## Acceptance Criteria

- [ ] Dataset Curator can assign a completed Training Crop to a specific seeded Reviewer.
- [ ] Dataset Curator cannot assign an incomplete, excluded, or empty Training Crop.
- [ ] Dataset Curator cannot assign a task to a User without Reviewer capability.
- [ ] User without Dataset Curator capability cannot create Assigned Review Tasks.
- [ ] Assigned Reviewer sees a Review Inbox when selected in the local Development session.
- [ ] Review Inbox lists only tasks assigned to the selected Reviewer.
- [ ] Assigned Reviewer can open the task and view only the assigned crop evidence.
- [ ] Assigned Reviewer cannot browse the source Workspace's wider Apiaries, Hives, Inspections, photos, crops, repository, model runs, or benchmark evidence through the task.
- [ ] Unassigned Reviewer cannot open or complete another Reviewer's task.
- [ ] Ordinary owner, contributor, and no-capability Users do not see the Review Inbox product surface unless they also have Reviewer capability.
- [ ] Assigned Reviewer can complete a task as `approved`, `changes_requested`, or `not_determined` with optional notes.
- [ ] Completed tasks retain reviewer id, completed timestamp, outcome, and notes.
- [ ] Dataset Curator can see assigned task status and completed outcome from the relevant crop or repository context.
- [ ] Assigned Review Tasks persist in Postgres-backed local development mode.
- [ ] API tests cover curator assignment, reviewer-only task access, blocked non-reviewer assignment, blocked unassigned access, and workspace boundary preservation.
- [ ] Playwright acceptance covers assigning a task as Curator, switching to Reviewer, seeing and completing the task, and confirming no-capability users do not see impossible surfaces.
- [ ] `docs/user-guide.md` explains how to assign and complete a local review task.

## Open Questions

- Should task-level `changes_requested` be enough for the first slice, or must the Reviewer identify which ellipse is wrong?
- Should a completed task be immutable, with a new task required for re-review?
- Should the Dataset Curator be able to cancel an assigned task before completion?
- Should Review Inbox be a separate page in the current internal app switcher, or a Reviewer-only panel on the inspection page?
- Should assignment be from the Training Crop panel, the Repository item detail, or both in the first implementation?
- What exact safe source metadata may be shown to a Reviewer without leaking wider Workspace details?
