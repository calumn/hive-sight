# Vertical Slice 0011: Physical Dataset Export Package

## Purpose

Turn the Slice 10 YOLO OBB manifest into a real local dataset export package that can be handed to a future model-training run.

This slice proves that reviewed Bee Annotation Repository evidence can be materialized as cropped image files, YOLO OBB label files, and a manifest while preserving traceability back to Dataset Items and canonical oriented bee ellipses.

## Source Inputs

- `CONTEXT.md`
- `requirements/bee-annotation-repository-and-curriculum-training-baseline.md`
- `requirements/model-requirements.md`
- `architecture/domain-model.md`
- `architecture/adr/0002-oriented-ellipse-canonical-bee-annotations.md`
- `architecture/vertical-slice-0009-training-crop-ellipse-annotation.md`
- `architecture/vertical-slice-0010-bee-annotation-repository-and-dataset-export.md`

## User Path

Given a Dataset Curator has assigned completed Training Crops to Dataset Roles
When the Dataset Curator creates a physical YOLO OBB dataset export package
Then HiveSight writes cropped image files, YOLO OBB label files, and a manifest to local export storage
And the Dataset Curator can inspect the package location and export summary.

## Preconditions

- User is logged in.
- User has active Workspace Membership for the source Workspace.
- User has dataset curator capability.
- Workspace Data Use Agreement is accepted.
- Bee Annotation Repository contains at least one `training` or `validation` Dataset Item sourced from a Training Crop.
- Source Inspection Photos are still available in local dev object storage.
- Benchmark and excluded Dataset Items may exist but must not be written into train/validation image or label folders.
- Local export storage is available under `var/exports/datasets/`.

## End-To-End Behaviour

The Dataset Curator requests a YOLO OBB physical export for the current Workspace.

HiveSight gathers all eligible Dataset Items:

- `training` items become package entries under the train split.
- `validation` items become package entries under the validation split.
- `benchmark` items are recorded as protected metadata only.
- `excluded` items are recorded as excluded metadata only.

For each exported Dataset Item, HiveSight reads the original Inspection Photo from local dev object storage, crops the Training Crop region, and writes a crop image into the export package. HiveSight writes a matching YOLO OBB label `.txt` file derived from the Dataset Item's reviewed ellipse snapshots.

The package layout is deterministic enough for local inspection and future training integration:

```text
var/exports/datasets/
  dataset-export-<export_id>/
    manifest.json
    dataset.yaml
    images/
      train/
        bee-crop-000001-<short_dataset_item_id>.png
      val/
        bee-crop-000002-<short_dataset_item_id>.png
    labels/
      train/
        bee-crop-000001-<short_dataset_item_id>.txt
      val/
        bee-crop-000002-<short_dataset_item_id>.txt
```

Dataset Item ids retain opaque UUIDs as internal identity, and Slice 0013.5 adds immutable generated human-readable Dataset Item ids for curation, export QA, and reports. Exported image and label filenames use deterministic human-readable names. The manifest maps each generated filename back to the full Dataset Item id, human-readable Dataset Item id where available, Training Crop id, Source Image id where available, Inspection Photo id, original filename, and provenance.

The manifest records counts, class map, source Dataset Item ids, human-readable Dataset Item ids where available, source Training Crop ids, Source Image ids where available, source Inspection Photo ids, protected benchmark ids, excluded item ids/reasons, generated YOLO label rows, file sizes, SHA-256 hashes, and caveats. The generated `dataset.yaml` is a first local YOLO-compatible descriptor for the package.

The physical export is all-or-nothing. If any included Dataset Item cannot be cropped, has invalid label state, has no reviewed ellipse snapshots, cannot read its source image, or cannot write its generated files, the export fails and HiveSight attempts to remove the partial package folder. The failed export must not be reported as a successful package.

The export remains synchronous in this slice because the dev dataset is small. The API returns the package id, package path, manifest path, dataset YAML path, summary counts, generated file entries, and caveat. The full audit manifest lives on disk as `manifest.json`.

The UI shows package path, manifest path, dataset YAML path, counts, and caveat. It does not render every generated file row and does not try to open Finder or download files.

## Locked Decisions

- Slice 11 creates a local export folder only; zip and download packaging are deferred.
- Each export creates a new immutable `dataset-export-<export_id>/` folder. Existing export folders are not overwritten.
- Export folders are written under `var/exports/datasets/`; tests override this path with temporary storage.
- Dataset Item ids remain UUIDs. Generated image and label filenames use `bee-crop-000001-<short_dataset_item_id>.png` and `.txt` style names.
- Cropped export images are PNG.
- Physical folders use YOLO-friendly split names: `images/train`, `images/val`, `labels/train`, and `labels/val`.
- The HiveSight manifest records Dataset Roles as `training`, `validation`, `benchmark`, and `excluded`.
- `manifest.json` is canonical HiveSight export metadata; `dataset.yaml` is a derived YOLO convenience file.
- `dataset.yaml` uses package-relative paths with `path: .`, `train: images/train`, and `val: images/val`.
- Included `training` and `validation` Dataset Items must have at least one reviewed ellipse snapshot. Background or negative samples remain out of scope.
- Benchmark Dataset Items are manifest metadata only. No benchmark images or labels are written.
- Excluded Dataset Items are manifest metadata only. No excluded images or labels are written.
- Full source photos are not copied into the package. Only cropped Training Crop images are exported.
- The API response returns summary fields and generated file entries, not the full manifest payload.
- Slice 11 adds no download or file-serving endpoints.
- The physical export is all-or-nothing, with best-effort cleanup of partial package folders on failure.
- `manifest.json` includes generated label file references and the exact YOLO OBB label rows.
- Slice 11 records SHA-256 hashes and byte sizes for generated crop images, label files, `manifest.json`, and `dataset.yaml`.
- `pnpm verify:slice` must prove the physical export artifacts exist and contain the expected content.
- Planned order changed after external review remediation: Slice 13 is the review recommendations architecture decision pass, and the YOLO OBB training baseline is parked as Slice 15 pending that decision pass.

## Layers Touched

- Web UI: show a physical export action and package summary/location in the Training Crop dataset workflow.
- Core API: add physical export package creation on top of the Slice 10 YOLO OBB manifest logic.
- Analysis Service: not touched.
- Storage: local dev filesystem export storage under `var/exports/datasets/` plus existing local uploaded-photo storage.
- Queue or async boundary: not touched; export remains synchronous.
- Contracts: physical YOLO OBB export response, package manifest, generated file entries.
- Observability: standard API errors for missing source photos, no eligible items, write failures, and benchmark/excluded leakage prevention.

## Test Seams

- Seam: Core API
- Behaviour verified: physical export writes crop image files and matching YOLO OBB label files for training and validation Dataset Items.
- Test style: API tests with temporary export storage.

- Seam: Core API
- Behaviour verified: benchmark and excluded Dataset Items are present in manifest metadata but absent from train/validation image and label folders.
- Test style: API tests and API-level BDD.

- Seam: Core API
- Behaviour verified: crop image dimensions match the Training Crop bounds and labels are normalized against the crop dimensions.
- Test style: API tests.

- Seam: Web UI
- Behaviour verified: Dataset Curator can request a physical package export and see package path, counts, and caveat.
- Test style: Playwright browser acceptance.

- Seam: Slice verification report
- Behaviour verified: verification output records API, BDD, web type-check, browser acceptance, and export artifact checks.
- Test style: `pnpm verify:slice`.

## Data Shape

### Physical Dataset Export

Minimum fields:

- export id
- workspace id
- export format: `yolo_obb`
- package path
- manifest path
- dataset yaml path
- created by user id
- created at
- class map
- training item count
- validation item count
- benchmark item count
- excluded item count
- generated files
- protected benchmark Dataset Item ids
- excluded Dataset Item ids with reasons
- caveat

### Generated File Entry

Minimum fields:

- relative path
- file kind: `manifest`, `dataset_yaml`, `image`, or `label`
- split: `train`, `val`, or `metadata`
- dataset item id, optional
- training crop id, optional
- inspection photo id, optional
- export filename stem, optional
- size bytes
- sha256

### Manifest JSON

Minimum fields:

- export metadata
- class map
- coordinate convention
- included Dataset Items
- protected benchmark Dataset Items
- excluded Dataset Items
- generated image files
- generated label files
- generated YOLO OBB label rows
- generated file byte sizes
- generated file SHA-256 hashes
- caveats

### Dataset YAML

Minimum fields:

- `path: .`
- package-relative train image path
- package-relative validation image path
- class names
- note that labels are YOLO OBB labels derived from canonical oriented bee ellipses

## Out Of Scope

- Real persistent database storage.
- Cloud object storage.
- Zip download packaging.
- Browser download/file-serving endpoints.
- Long-running export jobs.
- Dataset Version creation.
- Training Run execution.
- Model Candidate creation.
- Benchmark Evaluation execution.
- Hive Configuration and Frame Standard implementation.
- Duplicate or near-duplicate leakage detection beyond current role separation.
- Exporting benchmark labels.
- Varroa mite annotation export.
- Segmentation masks.

## Acceptance Criteria

- [x] A Dataset Curator can request a physical YOLO OBB dataset export package for a Workspace.
- [x] Export requires dataset curator capability.
- [x] Export requires accepted Workspace Data Use Agreement.
- [x] Export is blocked when there are no eligible `training` or `validation` Dataset Items.
- [x] Export writes cropped image files for `training` Dataset Items.
- [x] Export writes cropped image files for `validation` Dataset Items.
- [x] Export writes cropped image files as PNG.
- [x] Export writes YOLO OBB `.txt` label files beside exported crop images.
- [x] Export filenames are deterministic human-readable names with a short Dataset Item id suffix.
- [x] Export label rows use `class x1 y1 x2 y2 x3 y3 x4 y4`.
- [x] Export label coordinates are normalized against the crop image dimensions.
- [x] Export blocks included `training` or `validation` Dataset Items with zero reviewed ellipse snapshots.
- [x] Export creates `manifest.json`.
- [x] Export creates `dataset.yaml`.
- [x] `dataset.yaml` uses package-relative paths.
- [x] Export records SHA-256 hashes and byte sizes for generated images, label files, `manifest.json`, and `dataset.yaml`.
- [x] Manifest records Dataset Item ids, Training Crop ids, and Inspection Photo ids for exported files.
- [x] Manifest records the exact YOLO OBB label rows written to label files.
- [x] Manifest records protected benchmark Dataset Item ids/counts without writing benchmark labels into train/validation folders.
- [x] Manifest records excluded Dataset Item ids/reasons without writing excluded images or labels into train/validation folders.
- [x] Export fails all-or-nothing when source image read, crop rendering, label generation, or file writing fails.
- [x] Failed export attempts best-effort cleanup of partial package folders.
- [x] Package response exposes package path, manifest path, dataset YAML path, generated files, counts, and caveat.
- [x] UI shows package path, manifest path, dataset YAML path, counts, and caveat without rendering every generated file row.
- [x] Browser acceptance covers creating a package and viewing the generated package summary.
- [x] API-level BDD covers package creation and benchmark/excluded leakage prevention.
- [x] Slice verification checks generated crop images, label files, `manifest.json`, and `dataset.yaml` exist and contain expected content.
- [x] `pnpm verify:slice` passes.

## Open Questions

- None. Scope is locked for implementation.
