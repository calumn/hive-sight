# Vertical Slice 0015.1: Training Run Progress And Recovery

Status: implemented.

## Purpose

Make local Bee Detector Training Runs observable, cancellable, and recoverable so a Dataset Curator can tell whether YOLO OBB training is genuinely active, completed, failed, cancelled, or stale.

This slice responds to the first real local YOLO training attempts, where the UI could show `running` for several minutes without proof of life, expected duration, log output, or a recovery action.

The purpose is not to make training faster or to improve model quality. The purpose is to make the training control loop trustworthy enough for local dataset-building work.

## Source Inputs

- `CONTEXT.md`
- `requirements/ai-assisted-annotation-and-model-training-baseline.md`
- `requirements/bee-annotation-repository-and-curriculum-training-baseline.md`
- `architecture/vertical-slice-0015-yolo-obb-training-baseline.md`
- `architecture/adr/0003-postgres-for-durable-product-and-model-governance-metadata.md`
- `architecture/postgres-persistence-design.md`
- User feedback from real YOLO baseline attempts:
  - a run showed `running` for seven to eight minutes with no useful feedback
  - the UI did not prove whether training was active, stuck, or orphaned
  - a dead active run needs a curator/dev recovery action

## User Path

Given a Dataset Curator has created a Dataset Version
And real YOLO training is enabled locally
When the Dataset Curator starts a Training Run
Then HiveSight returns promptly with a Training Run id
And the UI shows phase, elapsed time, last heartbeat, progress detail, and recent log output
And the UI continues to poll until the run reaches `completed`, `failed`, or `cancelled`
And the Dataset Curator can cancel an in-flight run or mark an orphaned run as abandoned so it releases the active-run lock.

## Preconditions

- Slice 0015 is implemented.
- Dataset Version, Training Run, Model Candidate, and artifact metadata are durable in Postgres for real local training.
- Training Run start already enforces Dataset Curator capability, warning acknowledgement, adapter availability, and database-purpose safety.
- Real YOLO training remains opt-in through `pnpm dev:all:yolo-training`.
- Fast verification must continue to pass without Ultralytics installed; progress behaviour uses a deterministic fake or controllable slow adapter in normal tests.

## End-To-End Behaviour

The Dataset Curator starts a Bee Detector Training Run from the model-training panel. The Core API creates a durable Training Run record and starts the training work behind a local background-runner boundary instead of keeping the HTTP request as the only proof of progress.

The run moves through observable phases:

- `queued`
- `exporting_dataset`
- `training`
- `recording_artifacts`
- `completed`
- `failed`
- `cancelling`
- `cancelled`
- `abandoned`

The Core API updates Training Run progress as work proceeds. At minimum, progress records:

- current phase
- status
- started time
- completed time, when terminal
- elapsed seconds
- last heartbeat time
- last activity message
- optional progress percentage
- optional current epoch and total epochs
- latest log excerpt
- cancellation request state
- stale/orphaned assessment

The Web UI polls the active Training Run detail endpoint every few seconds while the run is active. It displays:

- run id and human-readable id
- status and phase
- started time
- elapsed time
- last heartbeat
- last activity message
- latest log excerpt
- active/stale indicator
- candidate creation state
- failure/cancellation/abandonment reason when terminal

If a run is active, the UI offers **Cancel run**. Cancellation is best-effort:

- for queued runs, cancellation should be immediate
- for fake/slow test adapters, cancellation should stop before completion
- for real Ultralytics training, cancellation should request termination and record whether the adapter acknowledged it

If a run appears stale or orphaned, the UI offers **Abandon stale run**. If cancellation has been requested but the real adapter does not stop promptly, the UI offers **Abandon cancelling run** using the explicit force rule. Abandoning a run is a recovery action that marks the run terminal as `abandoned`, records the reason and actor, and releases the active-run lock.

For local development only, the UI or API may expose a **Delete run** action for an active or abandoned run only when the run has no Model Candidate and no required artifacts. Deleting is a cleanup affordance, not the primary governance workflow. The preferred action is cancel/abandon because Training Runs are audit evidence.

## Layers Touched

- Web UI: Add richer Training Run detail, active polling, proof-of-life fields, log excerpt display, cancel button, stale-run recovery button, and a clear terminal-state message.
- Core API: Add Training Run progress/detail fields, cancellation request endpoint, stale-run abandonment endpoint, and optional dev-only hard-delete endpoint with strict guards.
- Analysis Service: Not touched.
- Storage: Persist progress fields and terminal recovery metadata with Training Run records. Store log excerpts/artifact references under the existing model artifact root.
- Queue or async boundary: Replace the current effectively synchronous real training execution with a local background runner abstraction that supports status updates, heartbeat, and cancellation request propagation.
- Contracts: Extend `/v1/model-training/training-runs/{training_run_id}` response and add action endpoints for cancel, abandon stale, and optionally delete.
- Observability: Emit structured log events for run start, phase change, heartbeat, cancellation requested, cancellation completed, stale run abandoned, failure, completion, and artifact recording.
- Developer tooling: Keep `pnpm dev:all:yolo-training` unchanged. Optionally add a small CLI command to print active training run detail from Core API.

## Test Seams

- Seam: Training Run background runner
- Behaviour verified: start returns promptly, run transitions through phases, progress heartbeat is updated, and terminal status releases the active-run lock.
- Test style: Core API workflow tests with a deterministic slow fake adapter.

- Seam: cancellation
- Behaviour verified: a queued/running Training Run can be cancellation-requested by a Dataset Curator; the run reaches `cancelled`; no Model Candidate is created; the active-run lock is released.
- Test style: Core API route/workflow tests.

- Seam: stale/orphan recovery
- Behaviour verified: a run whose last heartbeat is older than the stale threshold can be marked `abandoned`; non-stale active runs cannot be abandoned; abandoned runs release the active-run lock and preserve audit reason.
- Test style: Core API route/workflow tests with controlled clock.

- Seam: dev-only deletion
- Behaviour verified: only active/abandoned runs without Model Candidate and required artifacts may be deleted, if the endpoint is implemented; completed, failed-with-artifacts, or candidate-producing runs are not hard-deleted.
- Test style: Core API tests. If hard delete is deferred, record the deferral explicitly.

- Seam: Web UI
- Behaviour verified: Dataset Curator sees running proof-of-life fields, latest log excerpt, polling timestamp, cancel action, stale recovery action, and terminal result/failure/cancellation message.
- Test style: Playwright acceptance using fake/slow adapter behaviour.

- Seam: real-adapter QA lane
- Behaviour verified: local Ultralytics run emits at least coarse phase/heartbeat/log progress and terminates as completed, failed, cancelled, or abandoned.
- Test style: explicit QA-only command/manual check; not part of normal CI.

## Data Shape

### Training Run Extensions

Add or confirm these fields on `TrainingRunResponse`:

- `status`: include `queued`, `running`, `completed`, `failed`, `cancelling`, `cancelled`, `abandoned`
- `phase`: include `queued`, `exporting_dataset`, `training`, `recording_artifacts`, `completed`, `failed`, `cancelling`, `cancelled`, `abandoned`
- `started_at`
- `completed_at`
- `last_heartbeat_at`
- `last_activity_message`
- `progress_percent`: optional integer or decimal
- `current_epoch`: optional integer
- `total_epochs`: optional integer
- `latest_log_excerpt`: optional string, bounded length
- `cancel_requested_at`
- `cancel_requested_by_user_id`
- `cancel_reason`
- `abandoned_at`
- `abandoned_by_user_id`
- `abandon_reason`
- `is_stale`
- `stale_after_seconds`
- `failure_code`
- `failure_message`
- `model_candidate_id`
- `artifact_ids`

### Action Requests

`TrainingRunCancelRequest`:

- `workspace_id`
- `reason`: optional string

`TrainingRunAbandonRequest`:

- `workspace_id`
- `reason`: required string
- optional `force`: default false; only allowed for dev/owner capability if implemented

`TrainingRunDeleteRequest`, if implemented:

- `workspace_id`
- `reason`: required string
- `confirm_no_candidate_or_required_artifacts`: true

### Action Responses

Action endpoints return the updated `TrainingRunResponse` or a deletion confirmation containing:

- `training_run_id`
- `status`
- `phase`
- `active_lock_released`: boolean
- `message`

## Suggested API Endpoints

- `GET /v1/model-training/training-runs/{training_run_id}?workspace_id=...`
- `POST /v1/model-training/training-runs/{training_run_id}/cancel`
- `POST /v1/model-training/training-runs/{training_run_id}/abandon`
- Optional dev-only: `DELETE /v1/model-training/training-runs/{training_run_id}`

## Cancellation Semantics

Cancellation is a requested state transition, not a guarantee that an external library stops instantly.

The system should:

- record the cancellation request immediately
- stop queued or fake-adapter work deterministically
- ask the real adapter to stop if a cancellable process boundary exists
- mark the run `cancelled` if work stops without producing a model candidate
- mark the run `failed` if the adapter errors while handling cancellation
- never create a Model Candidate for a cancelled run
- release the active-run lock for `cancelled`, `failed`, `completed`, and `abandoned` terminal states

If real Ultralytics cannot be cancelled safely inside the current process, this slice should still provide a safe user action by marking a stale run `abandoned` after the process is gone or no heartbeat has appeared beyond the threshold. A later slice can move real training into a separate worker/process for stronger termination.

## Stale Or Orphaned Run Semantics

A Training Run is stale when:

- status is `queued`, `running`, or `cancelling`
- and `last_heartbeat_at` is older than the configured stale threshold

Initial local threshold:

- default `HIVESIGHT_TRAINING_RUN_STALE_AFTER_SECONDS=300`

An abandoned run:

- is terminal
- releases the active-run lock
- keeps its audit record
- does not create a Model Candidate
- records who abandoned it, when, and why

## UI Expectations

The model-training panel should avoid forcing the curator to infer state from one badge.

For an active run, show:

- `HS-TR-...`
- status and phase
- elapsed time
- last heartbeat time
- latest activity/log line
- "Auto-refreshing every 3 seconds"
- "Cancel run" button

For a stale active run, show:

- "No heartbeat for N minutes"
- "Abandon stale run" button
- optional "Delete run" only if the strict deletion guard passes

For a terminal run, show:

- completed/failed/cancelled/abandoned status
- completed time
- elapsed duration
- model candidate id if created
- failure/cancellation/abandonment reason if present
- report/artifact links where present

## Out Of Scope

- Improving model accuracy.
- Changing Dataset Version selection rules.
- Model evaluation/promotion gates.
- GPU/cloud training.
- Distributed queue infrastructure.
- Production worker orchestration.
- Full live Ultralytics epoch metrics beyond a bounded latest log/progress excerpt.
- Public USDA/XML annotation import; moved to a later slice because Slice 0015.1 is now progress/recovery.
- User-facing Bee Detector inference or candidate annotation generation.

## Acceptance Criteria

- [x] Starting a Training Run returns promptly with a durable Training Run id.
- [x] Training Run detail includes phase, status, started time, elapsed seconds, last heartbeat, latest activity, latest log excerpt, and stale assessment.
- [x] UI automatically polls active Training Runs and displays last checked time.
- [x] UI shows proof of life for active Training Runs without requiring terminal refresh.
- [x] UI shows failure, cancellation, or abandonment reason for terminal non-completed runs.
- [x] A Dataset Curator can request cancellation of an active Training Run.
- [x] Cancelled runs do not create Model Candidates and release the active-run lock.
- [x] Stale active Training Runs can be marked abandoned by an authorized Dataset Curator/dev owner.
- [x] Cancelling Training Runs can be force-abandoned from the local UI when cancellation does not stop promptly.
- [x] Non-stale active Training Runs cannot be abandoned without an explicit force rule.
- [x] Abandoned runs are terminal, audited, and release the active-run lock.
- [x] Hard delete is restricted to active/cancelled/abandoned runs with no Model Candidate and no required artifacts.
- [x] Fast tests use fake/slow adapters and do not require Ultralytics.
- [x] Playwright acceptance covers visible progress/proof-of-life; Core API tests cover cancel, abandon, and guarded delete.
- [x] Real-adapter QA lane remains explicit through `pnpm dev:all:yolo-training` and shows heartbeat/log progress through the same UI fields.
- [x] `pnpm verify:slice` remains green without real YOLO dependencies.

## Implementation Notes

- Training Run start now creates a `queued` run and starts local background execution.
- `TrainingRunResponse` carries heartbeat, progress, latest activity, log excerpt, stale, cancellation, and abandonment fields.
- The Core API exposes cancel, abandon, and guarded delete endpoints for Training Runs.
- The Web UI polls active runs every three seconds and shows proof-of-life fields plus recovery controls.
- Real Ultralytics cancellation remains best-effort in this process-bound implementation; stale abandonment is the safe local recovery path if the worker disappears or stops heartbeating, and force-abandonment is the safe local recovery path if a run remains live but stuck in `cancelling`.

## Planning Decisions Proposed

- Treat `cancelled` and `abandoned` as terminal Training Run states.
- Prefer cancel/abandon over hard delete because Training Runs are governance/audit evidence.
- Allow dev-only hard delete only if it cannot remove completed/candidate-producing evidence.
- Use a local background-runner abstraction before introducing a production queue.
- Poll active run detail from the UI every three seconds.
- Use a five-minute stale threshold initially, configurable by environment variable.
- Keep real-adapter progress coarse in this slice: phase, heartbeat, latest activity, and bounded log excerpt.
- Record cancellation and abandonment reasons in the Training Run record.

## Closed Decisions

- The UI uses `Abandon stale run` for stale runs and `Abandon cancelling run` for cancellation requests that have not stopped promptly; both preserve governance evidence while clearing the active-run lock.
- Guarded hard delete is implemented only for unevidenced active/cancelled/abandoned runs.
- The initial stale threshold is five minutes and is configurable through `HIVESIGHT_TRAINING_RUN_STALE_AFTER_SECONDS`.
- Cancellation is available immediately for active runs.
- A separate subprocess worker is deferred; this slice uses background execution, best-effort cancellation, and stale-run abandonment.
