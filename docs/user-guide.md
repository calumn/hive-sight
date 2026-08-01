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

## Start HiveSight With Real YOLO Training

Use this when you want to train or test a local YOLO OBB Bee Detector Model Candidate.

First install optional YOLO dependencies once:

```sh
cd ~/Projects/hive-sight
pnpm model:setup:yolo
```

Then start the stack with Postgres-backed metadata and the real YOLO adapter:

```sh
pnpm dev:all:yolo-training
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
7. Upload one or more frame photos.
8. If an earlier Training Inspection exists, choose it from `Resume Training Inspection`.

Training-data collection inspections show the Training Crop workflow. Varroa assessment inspections do not.

## Create Training Crops

Use this when you want to cut a large frame photo into smaller annotation areas.

1. Select a source photo in `Training crops`.
2. Click the source photo to place a crop.
3. Adjust the crop coordinates or size if needed.
4. Click `Save crop`.
5. Select the saved crop from the crop list.

Saved crops and their reviewed ellipses persist when using the Postgres-backed local stack.

## Annotate Bees In A Training Crop

Use this when you want to manually create the training evidence for the Bee Detector.

1. Select an editable Training Crop.
2. Use zoom and pan to inspect the crop.
3. Click inside the crop to add a default bee ellipse.
4. Use the ellipse controls to nudge, rotate, and resize the ellipse.
5. Set the bee type to `Complete visible bee` or `Partial visible bee`.
6. Repeat until the visible bees in the crop are annotated.
7. Set visible bee status.
8. Click `Complete crop`.

Complete bees should normally be fully contained by the crop. Partial bees may overlap the crop edge when the bee is only partly visible.

## Reopen And Continue A Training Crop

Use this when you need to come back later or correct completed work.

1. Start HiveSight with the Postgres-backed stack.
2. Resume the relevant Training Inspection.
3. Select the crop from the crop list.
4. If it is complete or excluded, click `Reopen crop`.
5. Add, edit, or delete ellipses.
6. Complete or exclude the crop again when finished.

## Assign Completed Crops To Dataset Roles

Use this when completed crop evidence is ready to become model training data.

1. Select a completed crop.
2. In `Bee Annotation Repository`, choose a Dataset role:
   - `Training`
   - `Validation`
   - `Benchmark`
   - `Excluded`
3. Add a source group key when assigning benchmark evidence.
4. Click `Assign item`.

The assignment snapshots the reviewed ellipses at that point. Later edits to the crop do not change an already-created Dataset Item.

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
pnpm dev:all:yolo-training
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

## Use A Model Candidate To Suggest Bees In A Crop

Use this when you want the trained Bee Detector to propose candidate ellipses for a crop, while keeping human review in control.

1. Start HiveSight with:

```sh
pnpm dev:all:yolo-training
```

2. Make sure at least one completed Model Candidate exists.
3. Select an editable Training Crop that was not included in that Model Candidate's frozen Dataset Version.
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
