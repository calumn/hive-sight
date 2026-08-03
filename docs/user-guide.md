# HiveSight User Guide

This guide is task-oriented. It explains how to exercise the current HiveSight product behaviours in the local development environment.

The guide should be updated whenever a slice changes how a user performs a task in the Web UI, Core API, or local model workflow.

## Start HiveSight Locally

Use this when you want to run the local Web UI and services.

```sh
cd ~/Projects/hive-sight
pnpm dev:all
```

Open the Web UI:

```text
http://127.0.0.1:5173/
```

Stop the local servers:

```sh
pnpm dev:stop
```

Check whether the servers are running:

```sh
pnpm dev:status
```

## Switch Development User

Use this when you want to exercise the local UI as another seeded User without real authentication.

1. Start HiveSight locally.
2. In `Development session`, choose a User from `Acting as`.
3. Wait for the selected User's Workspace, Apiary, and Hive to load.
4. Check `Capabilities` to see whether that User is a Dataset Curator, Reviewer, both, or neither.

Switching User behaves like logging out and logging in as someone else: the current page, selected Inspection, selected photos, crops, repository state, and transient images are cleared before the new User's Workspace is loaded.

Product actions that the selected User can never perform are hidden. For example, a User without Dataset Curator capability will not see the Repository page button.

## Start HiveSight With Real YOLO Training

Use this when you want to train or test a local YOLO OBB Bee Detector Model Candidate.

First install optional YOLO dependencies once:

```sh
cd ~/Projects/hive-sight
pnpm model:setup:yolo
```

Then start the stack with Postgres-backed metadata and the real YOLO adapter:

```sh
pnpm dev:all:yolo
```

Open:

```text
http://127.0.0.1:5173/
```

## Create Or Resume A Training Data Inspection

Use this when you want to upload frame photos and create Training Crops for bee annotation.

1. Open the Web UI.
2. Accept the Workspace Data Use Agreement if prompted.
3. Select an existing Apiary, or create one.
4. Select an existing Hive, or create one.
5. Make sure the Hive has a Hive Configuration and Frame Standard.
6. Create an Inspection with intent `Training data collection`.
7. If an earlier Training Inspection exists, choose it from `Resume Training Inspection`.
8. Use the workflow stage buttons to move between `Inspection Setup`, `Crop Selection`, `Bee Annotation`, and `Crop Governance`.

Training-data collection inspections show the Training Crop workflow. Varroa assessment inspections do not.

## Create Training Crops

Use this when you want to cut a large frame photo into smaller annotation areas.

1. Open the `Crop Selection` workflow stage.
2. Upload one or more frame photos.
3. Select a source photo.
4. Click the source photo to place a crop.
5. Adjust the crop coordinates or size if needed.
6. Click `Save crop`.
7. Select the saved crop from the crop list.
8. Click `Annotate selected crop` when you are ready to mark bees.

Saved crops and their reviewed ellipses persist when using the Postgres-backed local stack.
If a saved crop was created by mistake, select it and click `Delete crop`. Deletion is available only before the crop has an active review request or has been assigned into the dataset.

## Annotate Bees In A Training Crop

Use this when you want to manually create the training evidence for the Bee Detector.

1. Open the `Bee Annotation` workflow stage.
2. Select an editable Training Crop from the crop queue.
3. Use zoom and pan to inspect the crop.
4. Click inside the crop to add a default bee ellipse.
5. Use the ellipse controls to nudge, rotate, and resize the ellipse.
6. Make sure the arrow on the ellipse points toward the bee's head.
7. If the ellipse shape is correct but points tail-first, click `Flip head/tail`.
8. Set the bee type to `Complete visible bee` or `Partial visible bee`.
9. Repeat until the visible bees in the crop are annotated.
10. Use `Previous crop`, `Next crop`, or `Next incomplete` to move through the crop queue.
11. Set visible bee status.
12. Click `Complete crop`.

Complete bees should normally be fully contained by the crop. Partial bees may overlap the crop edge when the bee is only partly visible.

The stored ellipse rotation is the bee head direction. This matters for future Varroa work, where HiveSight may rotate each bee crop consistently before looking for mites.

## Reopen And Continue A Training Crop

Use this when you need to come back later or correct completed work.

1. Start HiveSight with the Postgres-backed stack.
2. Resume the relevant Training Inspection.
3. Open `Bee Annotation` or `Crop Governance`.
4. Select the crop from the crop list.
5. If it is complete or excluded, click `Reopen crop`.
6. Add, edit, or delete ellipses.
7. Complete or exclude the crop again when finished.

## Assign Completed Crops To Dataset Roles

Use this when completed crop evidence is ready to become model training data.

1. Open the `Crop Governance` workflow stage.
2. Select a completed crop.
3. In `Bee Annotation Repository`, choose a Dataset role:
   - `Training`
   - `Validation`
   - `Benchmark`
   - `Excluded`
4. Add a source group key when assigning benchmark evidence.
5. Click `Assign item`.

The assignment snapshots the reviewed ellipses at that point. Later edits to the crop do not change an already-created Dataset Item.

## Review The Bee Annotation Repository

Use this when you want to see what is actually in the workspace dataset across multiple Training Data Collection inspections.

1. Open the Web UI.
2. Click `Bee Annotation Repository` in the Workspace gate panel.
3. Review the Training, Validation, Benchmark, Excluded, New items, and Unassigned crops counts.
4. Use the Dataset Role, Dataset Version, Bee class, and Search filters to narrow the list.
5. Select a Dataset Item to inspect its crop preview, reviewed bee ellipses, source photo, inspection, hive, hive configuration, source group, assignment note, and Dataset Version membership.
6. Check repository warnings for non-blocking data quality concerns, such as all items coming from one source image or having no benchmark items yet.
7. Click `Inspection` to return to crop annotation.

The repository browser is read-only. It does not change Dataset Item assignments or affect Dataset Version creation rules.

## Request Independent Review Of A Completed Training Crop

Use this when a Dataset Curator wants another Reviewer to check completed bee annotations before those annotations are treated as trusted training evidence.

1. Switch to a User with Dataset Curator capability.
2. Resume or create a Training Data Collection inspection.
3. Open the `Crop Governance` workflow stage.
4. Select a completed Training Crop that has visible bees and reviewed ellipses.
5. In `Independent crop review`, add request notes if useful.
6. Click `Request review`.
7. Check the requested review summary for the `HS-RQ-...` item and its current status.

While a review request is available, the crop is locked from editing so the Reviewer sees the exact evidence that was submitted.

If the request was made too early, add cancellation notes and click `Cancel request`. The crop can then be reopened, edited, completed again, and submitted for review again.

## Complete Shared Reviewer Work

Use this when a Reviewer wants to pick up available review work from the shared pool.

1. Switch to a User with Reviewer capability.
2. Click `Review Work`.
3. Select an available `HS-RQ-...` item.
4. Review the crop image, safe source label, crop dimensions, and submitted bee ellipses.
5. Choose an outcome:
   - `Approved`
   - `Changes requested`
   - `Not determined`
6. Add notes when the outcome is `Changes requested` or `Not determined`.
7. Click `Complete review`.

The queue is shared. Once one eligible Reviewer completes an item, it disappears for other Reviewers. Reviewers cannot see work they requested or originally annotated.

## Create A YOLO OBB Dataset Version

Use this when you have at least one Training item and one Validation item.

1. In `Bee Detector training baseline`, click `Check readiness`.
2. Review any warnings.
3. Click `Dataset Version`.
4. Confirm the summary shows the expected Training, Validation, and Benchmark counts.

Dataset Versions are frozen model-training evidence. Benchmark items are protected from training export.

## Train A Bee Detector Baseline

Use this when you want to train a local YOLO OBB Model Candidate from the current Dataset Version.

1. Start HiveSight with:

```sh
pnpm dev:all:yolo
```

2. Create or select a Dataset Version.
3. Acknowledge high-severity warnings if you deliberately want to continue with a small or incomplete dataset.
4. Click `Train baseline`.
5. Watch the Training Run summary for status, phase, heartbeat, elapsed time, log excerpt, and candidate creation.
6. When the run completes, click `Use candidate for crop YOLO` if you want that candidate to power crop pre-labelling.
7. Confirm the Training Run summary says `Now using HS-MC-... for crop YOLO`.

A completed run creates a Model Candidate. These baseline candidates are not user-facing production models.

You can also start a run from the command line:

```sh
pnpm model:train:bee:yolo
```

## Evaluate A Bee Localisation Model Candidate

Use this when you want internal model-governance evidence for a completed Bee Detector Model Candidate. This is a Dataset Curator task, not normal beekeeper inspection work.

1. Make sure your Dataset Version has protected Benchmark items from source images that were not used for Training or Validation.
2. Train a Bee Detector baseline and select the completed Model Candidate.
3. In the model-governance panel, click `Check benchmark`.
4. Review warnings such as `SMALL_BENCHMARK_SET`.
5. Click `Run benchmark`.
6. Watch status, phase, heartbeat, progress, precision, recall, activity, and log excerpt.
7. Open the `Report` and `Raw predictions` links when the run completes.

The report is Training Crop benchmark only. It does not evaluate full-frame bee localisation, bee head-end prediction, or Varroa detection.

For a command-line real-adapter proof-of-life check against the latest completed real Model Candidate:

```sh
pnpm model:qa:bee:evaluate
```

## Use A Model Candidate To Suggest Bees In A Crop

Use this when you want the trained Bee Detector to propose candidate ellipses for a crop, while keeping human review in control.

1. Start HiveSight with:

```sh
pnpm dev:all:yolo
```

2. Make sure at least one completed Model Candidate exists.
3. Open `Bee Annotation` and select an editable Training Crop that was not included in that Model Candidate's frozen Dataset Version.
4. Either click `Use candidate for crop YOLO` on the completed Training Run, or choose the Model Candidate in `YOLO crop pre-labels`.
5. Check that the panel says which Model Candidate is being used for crop YOLO.
6. Set the confidence threshold. The current default is 10%.
7. Click `YOLO this crop`.
8. Review the dashed candidate ellipses.
9. Select a candidate ellipse and nudge, rotate, or resize it if needed.
10. Click `Accept complete` or `Accept partial`.

Accepted suggestions become normal reviewed Training Crop ellipses with model-candidate provenance. Unaccepted suggestions are transient and are not dataset evidence.

If the crop was part of the candidate's own Dataset Version, HiveSight blocks pre-labelling to avoid using a model to suggest labels for its own frozen training evidence.

For a command-line proof-of-life check against the latest Model Candidate and first editable Training Crop:

```sh
pnpm model:qa:bee:prelabel
```

## Reset Early Dataset Evidence For Directed Head Review

Use this only for the early local dataset created before ellipse direction meant bee head direction.

Start the Postgres-backed stack, then run:

```sh
pnpm model:reset:directed-ellipse-review
```

This removes local Dataset Items, Dataset Versions, Training Runs, Model Candidates, and derived model artifacts. It keeps uploaded photos, Training Crops, and existing ellipses, and reopens completed crops so you can review head direction and assign fresh Dataset Items.

## Run Slice Verification

Use this when you want proof that the current behaviour still passes automated checks.

```sh
cd ~/Projects/hive-sight
pnpm verify:slice
```

This runs Core API tests, API-level BDD scenarios, Analysis Service tests, Web TypeScript checks, and browser acceptance tests. The latest report is written to:

```text
reports/slice-verification/latest.md
```
