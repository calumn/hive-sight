# Vertical Slice 0022: Bee Orientation Training Baseline

Status: accepted for implementation after renewed acceptance scenario signoff.

## Purpose

Let a Dataset Curator train the first non-user-facing Bee Orientation baseline from the same locked Marked-Bee Dataset Version used for Bee Detection and Bee Orientation.

This slice proves the first end-to-end Bee Orientation model-governance path. A curator freezes reviewed marked-bee evidence once, then HiveSight derives purpose-specific packages from that source version:

- Bee Detection receives a YOLO OBB package.
- Bee Orientation receives a Head Up / Head Down crop package.

The Bee Orientation classifier is deliberately narrow. It does not find bees, detect Varroa, or produce a user-facing Varroa Assessment. It predicts whether a body-axis-normalized bee crop is `head_up` or `head_down`.

The fake adapter in this slice validates a real derived orientation package and records a non-user-facing Model Candidate. It does not perform predictive training, does not report fake accuracy, and does not enable downstream use.

## Source Inputs

- `CONTEXT.md`: Marked-Bee Dataset Version, Oriented Bee Ellipse, Orientation Reliability, Dataset Version, Model Purpose, Bee Detection, Bee Localisation Model, Bee Orientation Model, Head-Up Normalized Bee Crop.
- `requirements/model-requirements.md`: MR-001A Bee Head Direction, MR-008B Orientation Reliability, MR-029A Training Run Records, MR-029B Model Candidate Records, MR-030 Benchmark Evaluation Before Promotion.
- `requirements/roadmap.md`: Bee Orientation candidate slices: Shared Marked-Bee Dataset Version Promotion, Bee Orientation Dataset Builder, Bee Orientation Model Baseline.
- `architecture/adr/0007-three-stage-bee-localisation-orientation-and-varroa-pipeline.md`: Bee Localisation, Bee Orientation, and Varroa Detection are separate Model Purposes with shared marked-bee source Dataset Versions.
- `architecture/bee-orientation-classifier-design.md`: binary Head Up / Head Down classifier, reliable complete visible bees only for the first corpus, purpose-specific derived packages and governance records.
- `architecture/vertical-slice-0021-orientation-reliability-review.md`: Orientation Reliability is reviewed evidence on Oriented Bee Ellipses.

## Proposed Acceptance Scenarios

These revised scenarios were accepted for implementation on 2026-08-04.

```gherkin
Feature: Bee Orientation Training Baseline

  Scenario: Dataset Curator creates a shared Marked-Bee Dataset Version
    Given a Dataset Curator has Training and Validation Dataset Items with reviewed Oriented Bee Ellipses
    When they create a Dataset Version from Model Governance
    Then HiveSight creates a Marked-Bee Dataset Version for Bee Detection and Bee Orientation
    And the Dataset Version is not described as Bee Detector-only evidence
    And Bee Detection and Bee Orientation show separate derived-package workflows from that shared version

  Scenario: Bee Orientation readiness counts only eligible orientation evidence
    Given a locked Marked-Bee Dataset Version contains reliable complete bees, unreliable complete bees, reliable partial bees, and protected benchmark bees
    When HiveSight checks Bee Orientation training readiness
    Then HiveSight counts only reliable complete visible bees in Training and Validation as eligible orientation source bees
    And HiveSight reports unreliable orientations as excluded from orientation training
    And HiveSight reports partial visible bees as deferred from the first orientation baseline
    And HiveSight reports protected benchmark evidence separately without including it in the training package
    And HiveSight blocks training unless at least one eligible Training bee and one eligible Validation bee exist

  Scenario: Bee Orientation package is derived from frozen Dataset Item snapshots
    Given a locked Marked-Bee Dataset Version has eligible reliable complete bee snapshots
    When the Dataset Curator starts a Bee Orientation baseline Training Run
    Then HiveSight builds the orientation package from Dataset Item reviewed ellipse snapshots, not editable Training Crop state
    And HiveSight reads original source image bytes for each eligible bee
    And HiveSight creates a real 224 by 224 PNG head-up crop using a 20 percent ellipse margin
    And HiveSight creates a generated head-down PNG by rotating the head-up crop 180 degrees
    And both generated examples stay in the same Training or Validation split as their source Dataset Item

  Scenario: Derived orientation package is inspectable and reproducible
    Given HiveSight has generated a Bee Orientation package
    When the Training Run records its package artifacts
    Then the package contains PNG crop files, `manifest.json`, `labels.jsonl`, and `exclusions.jsonl`
    And each label row includes source ids, split, label, augmentation, transform metadata, and generated image SHA-256
    And the manifest records the package format version, class map, image size, margin, policies, exclusion summary, and deterministic package hash
    And the package hash excludes timestamps and machine-local absolute paths
    And HiveSight creates a report with contact-sheet thumbnails showing head-up and generated head-down pairs side by side

  Scenario: Missing source image bytes block orientation package generation
    Given a locked Marked-Bee Dataset Version includes an otherwise eligible orientation source bee
    And the original source image bytes are missing or unreadable
    When HiveSight checks Bee Orientation training readiness
    Then HiveSight reports a source-image blocker
    And HiveSight does not start Bee Orientation training until the source image problem is resolved

  Scenario: Fake Bee Orientation adapter validates package shape only
    Given a Bee Orientation package has been generated and validated
    When the fake Bee Orientation adapter completes the Training Run
    Then HiveSight creates a non-user-facing Bee Orientation Model Candidate with Model Purpose `bee_orientation`
    And the candidate artifact is a fake adapter manifest, not fake neural-network weights
    And the Training Run report states that no predictive model training was performed
    And the Training Run reports package and count metrics, not fake accuracy or a fake confusion matrix
    And the Model Governance view shows the run as Bee Orientation, not Bee Detector

  Scenario: Bee Orientation remains separate from downstream and benchmark workflows
    Given a Bee Orientation Model Candidate exists from the fake baseline
    When the Dataset Curator reviews Model Governance
    Then HiveSight does not offer to use that candidate for Bee Detector crop pre-labelling
    And HiveSight does not offer Bee Orientation benchmark execution in this slice
    And HiveSight does not change user-facing Varroa Assessment workflows
    And Bee Detection and Bee Orientation Training Runs both reference the same Marked-Bee Dataset Version while keeping separate Model Purposes, derived packages, adapters, reports, and Model Candidates
```

## User Path

Given a Dataset Curator is in Model Governance
When they create or select a shared Marked-Bee Dataset Version and start Bee Orientation baseline training
Then HiveSight records a Bee Orientation Training Run and Model Candidate from a real, inspectable Head Up / Head Down package derived from reliable complete bees in that shared source version.

## Preconditions

- Slice 0021 is implemented: Oriented Bee Ellipses carry Orientation Reliability.
- The selected User has Dataset Curator capability.
- Workspace Data Use Agreement requirements remain enforced.
- At least one Training Dataset Item and one Validation Dataset Item exist for the Marked-Bee Dataset Version.
- Eligible orientation source bees are complete visible bee snapshots whose Orientation Reliability is `reliable`.
- Benchmark evidence is counted but protected from training package generation.
- Original source image bytes are available for eligible source bees.
- Existing model-governance jobs and artifact storage are available.

## Grilled Design Decisions

- User-facing term: **Marked-Bee Dataset Version**.
- Source evidence: one shared Marked-Bee Dataset Version for Bee Detection and Bee Orientation.
- UI shape: one shared Dataset Version step, then separate Bee Detection and Bee Orientation panels, then Model job history.
- API compatibility: keep the existing dataset-version endpoint for Slice 0022, but change domain payload and wording.
- Internal compatibility: keep existing `bee_detector` Model Purpose identifier for Bee Detection; add `bee_orientation`.
- New versions only: do not rewrite old Bee Detector-only local Dataset Versions.
- Bee Detection training may accept legacy and new Dataset Version purposes; Bee Orientation training requires the new shared Marked-Bee purpose.
- Dataset Version creation does not require orientation readiness; Bee Orientation training readiness enforces orientation eligibility later.
- First orientation corpus: complete visible bees only.
- Reliable partial bees are deferred, not deleted.
- Unreliable orientations are excluded from orientation training.
- Benchmark evidence is counted for future readiness but excluded from Slice 0022 training packages.
- Package builder reads Dataset Item snapshots, not current editable Training Crop ellipses.
- Package builder derives crops from original source image bytes using snapshot geometry and provenance.
- Transform: Pillow-based real crop/rotate/pad/resize.
- Image output: PNG.
- Crop settings: 224x224, 20 percent ellipse margin, pad to square then resize.
- Labels: one head-up and one generated head-down example per eligible source bee.
- Augmentation: head-down examples are generated by 180-degree rotation.
- Split rule: generated examples stay in their source Dataset Item split.
- Files: `manifest.json`, `labels.jsonl`, `exclusions.jsonl`, generated PNGs, and a report/contact sheet.
- Hashing: generated image SHA-256 plus deterministic package manifest hash; no timestamps or absolute local paths in the package hash.
- Fake adapter: validates package shape only; no predictive model training.
- Fake candidate artifact: fake adapter manifest, not fake weights.
- Metrics: package/count metrics only; no fake accuracy or confusion matrix.
- Candidate lifecycle: use normal `created` status with explicit fake/non-user-facing wording.
- Candidate downstream use: visible only; no orientation inference, no benchmark, no Varroa changes in Slice 0022.
- Concurrency: allow multiple historical runs; block concurrent active Bee Orientation runs. Slice 0022 may inherit the current one-active-model-job-per-workspace guard if broader job-runner changes would expand scope.
- Documentation: Slice 0022 implementation must update relevant project artifacts, not only code.

## End-To-End Behaviour

The Model Governance tab treats the locked source Dataset Version as a shared Marked-Bee Dataset Version for Bee Detection and Bee Orientation. Bee Detection and Bee Orientation appear as separate model workflows that consume different derived packages from that same source version.

The existing Dataset Version creation flow is renamed or generalized so it no longer claims to create Bee Detector-only evidence. The source version purpose should read as marked-bee evidence for Bee Detection and Bee Orientation. Existing Bee Detection training still receives its YOLO OBB derived package from that version.

The curator can check Bee Orientation readiness. Readiness reports:

- source Dataset Version id and human-readable id;
- source Dataset Version purpose;
- eligible complete/reliable Training source bee count;
- eligible complete/reliable Validation source bee count;
- generated Training example count;
- generated Validation example count;
- protected benchmark orientation source bee count;
- excluded unreliable-orientation count;
- excluded partial-visible-bee count;
- source-image availability blockers;
- any warnings inherited from the shared Dataset Version.

Starting Bee Orientation baseline training builds the derived orientation package, validates it, runs the fake adapter, records artifacts, and creates a non-user-facing Bee Orientation Model Candidate.

The derived package records source maps back to Dataset Item, Training Crop, Source Image, and Oriented Bee Ellipse ids. It records transform metadata: source image dimensions, source crop bounds, ellipse geometry, margin, rotation applied, resize/pad policy, edge padding, augmentation, split, class map, image SHA-256, and package manifest hash.

The generated package is inspectable. The report includes counts, exclusion summary, package manifest hash, source Dataset Version identity, and contact-sheet preview rows showing head-up and generated head-down PNG pairs side by side.

Model job history shows Bee Detection and Bee Orientation jobs together while labelling Model Purpose clearly. The UI must not let a Bee Orientation candidate be used for crop YOLO pre-labelling, Bee Detector benchmark evaluation, Bee Orientation benchmark evaluation, orientation inference, or Varroa Assessment.

## Layers Touched

- Web UI: Rename or generalize Dataset Version wording to Marked-Bee Dataset Version; add Bee Orientation readiness, start-baseline action, run summary, package/report link, and history labelling in Model Governance.
- Core API: Generalize Dataset Version purpose away from Bee Detector-only source evidence; add Bee Orientation readiness, package builder, fake adapter, and training-run start path, or generalize existing model-training endpoints to accept `model_purpose`.
- Analysis Service: Not touched for Slice 0022. Real classifier execution remains out of scope.
- Storage: Persist shared Marked-Bee Dataset Version purpose, Bee Orientation Training Runs, Model Candidates, generated package artifacts, reports, and source Dataset Version links through the existing store and Postgres-backed record path.
- Queue or async boundary: Reuse the existing model Training Run worker pattern and current active-run guard unless a minimal per-purpose guard falls naturally out of the implementation.
- Contracts: Extend Dataset Version purpose wording and model-purpose parsing/API responses from Bee Detector-only to shared marked-bee source evidence plus `bee_orientation` Training Runs and Model Candidates.
- Observability: Record model-purpose-specific events for readiness, package generation, queued run, completed run, failed run, and candidate creation.

## Test Seams

- Seam: Marked-Bee Dataset Version creation
- Behaviour verified: new versions are named and governed as shared marked-bee evidence for Bee Detection and Bee Orientation; old versions are not rewritten.
- Test style: focused Core API test and Playwright assertion in Model Governance.

- Seam: Bee Orientation readiness
- Behaviour verified: only reliable complete visible bees count as eligible orientation source bees; unreliable, partial, and benchmark evidence are reported separately; missing source bytes block training.
- Test style: focused Core API test.

- Seam: Bee Orientation derived package builder
- Behaviour verified: creates real 224x224 PNG head-up/head-down pairs from Dataset Item snapshots with 20 percent margin, source maps, transform metadata, labels, exclusions, image hashes, deterministic manifest hash, and contact-sheet report.
- Test style: service-level unit/workflow test using fixture image bytes.

- Seam: Bee Orientation Training Run workflow
- Behaviour verified: fake adapter validates package shape, creates a Training Run and non-user-facing `bee_orientation` Model Candidate, reports package/count metrics only, and records fake-adapter-manifest artifact.
- Test style: focused Core API test and API-level BDD scenario.

- Seam: Web Model Governance
- Behaviour verified: Dataset Curator can see the shared Marked-Bee Dataset Version, check Bee Orientation readiness, start the baseline, see completion, distinguish Bee Orientation jobs from Bee Detection jobs, and open the report/package artifact link.
- Test style: Playwright browser acceptance extending the model-governance flow.

- Seam: Postgres persistence
- Behaviour verified: Marked-Bee Dataset Version purpose, Bee Orientation Training Run, Model Candidate, derived artifacts, and source Dataset Version linkage survive the Postgres-backed restart path.
- Test style: opt-in Postgres persistence test when Docker/Postgres is available.

## Data Shape

Minimum additions or generalizations:

- Dataset Version purpose changes for newly created versions from Bee Detector-only training evidence to shared Marked-Bee evidence for Bee Detection and Bee Orientation, for example `marked_bee_detection_orientation`.
- Derived package/export formats identify the consuming Model Purpose, for example `bee_detection_yolo_obb_v1` and `bee_orientation_head_up_down_v1`.
- Model Purpose values include `bee_orientation` alongside the existing `bee_detector` compatibility value.
- Bee Orientation readiness response:
  - workspace id;
  - source Dataset Version id;
  - source Dataset Version human-readable id;
  - source Dataset Version purpose;
  - eligible Training source bee count;
  - eligible Validation source bee count;
  - generated Training example count;
  - generated Validation example count;
  - protected benchmark source bee count;
  - excluded unreliable-orientation count;
  - excluded partial-visible-bee count;
  - blockers and warnings.
- Derived orientation package:
  - `manifest.json`;
  - `labels.jsonl`;
  - `exclusions.jsonl`;
  - generated PNG files under split-specific folders;
  - package/contact-sheet report.
- Label row:
  - generated example id;
  - relative image path;
  - label: `head_up` or `head_down`;
  - split: `training` or `validation`;
  - augmentation: `none` or `rotate_180`;
  - Dataset Item id;
  - Training Crop id;
  - Source Image or Inspection Photo id;
  - Oriented Bee Ellipse annotation id;
  - source dimensions;
  - ellipse geometry;
  - crop bounds;
  - rotation applied;
  - padding/edge flag;
  - image SHA-256.
- Exclusion row:
  - source ids where available;
  - exclusion reason, such as `orientation_unreliable`, `partial_visible_bee_deferred`, or `benchmark_protected`;
  - split or Dataset Role;
  - relevant annotation metadata.
- Training Run:
  - `model_purpose`: `bee_orientation`;
  - `model_family`: `bee_orientation_binary_classifier`;
  - source Dataset Version id;
  - derived package artifact id;
  - adapter type;
  - image size, margin, augmentation policy, epochs, seed, batch size.
- Model Candidate:
  - `model_purpose`: `bee_orientation`;
  - linked Training Run;
  - not-user-facing reason;
  - fake adapter manifest artifact, not fake weights.

## Out Of Scope

- Real MobileNet, ResNet, or EfficientNet training in normal slice verification.
- Bee Orientation benchmark evaluation or promotion thresholds.
- Bee Orientation inference in live Varroa Assessment.
- Head-Up Normalized Bee Crop generation for Varroa labelling or detection outside the training package.
- Varroa Review Outcome labelling.
- Varroa Detector training.
- Partial visible bees in the first orientation training package.
- Browser-based package gallery or derived-package browser; artifact/report link is enough.
- Package preview before starting training; package artifacts appear after Training Run completion.
- Broad rename of existing `bee_detector` runtime or candidate contracts beyond user-facing wording and source Dataset Version meaning.
- Automatic migration, cleanup, or rewriting of old Bee Detector-only Dataset Versions.
- Separate orientation-only source Dataset Version promotion.
- Per-Model-Purpose concurrent training scheduler redesign if the current infrastructure only supports one active model job per Workspace.
- Ordinary beekeeper-facing Varroa Assessment documentation or UI.

## Acceptance Criteria

- [ ] New Dataset Versions created by Model Governance are visibly Marked-Bee Dataset Versions for Bee Detection and Bee Orientation, not Bee Detector-only evidence.
- [ ] Existing old Dataset Versions are not silently rewritten.
- [ ] Bee Detection training remains compatible with old Bee Detector-only test versions and new Marked-Bee versions where needed.
- [ ] Bee Orientation training requires the new shared Marked-Bee Dataset Version purpose.
- [ ] Shared Dataset Version creation does not require orientation readiness.
- [ ] Dataset Curator can check Bee Orientation readiness from Model Governance.
- [ ] Readiness counts only reliable complete visible bee snapshots in Training and Validation as eligible orientation source bees.
- [ ] Readiness reports unreliable, partial, and protected benchmark evidence separately.
- [ ] Missing or unreadable source image bytes block orientation training.
- [ ] Training is blocked unless at least one eligible Training bee and one eligible Validation bee exist.
- [ ] Starting a Bee Orientation baseline builds a real derived Head Up / Head Down package from Dataset Item snapshots and original source image bytes.
- [ ] The package creates two 224x224 PNG examples per eligible source bee: head-up and generated head-down.
- [ ] Generated examples remain in the same split as their source Dataset Item.
- [ ] Package artifacts include generated PNGs, `manifest.json`, `labels.jsonl`, `exclusions.jsonl`, deterministic package hash, image SHA-256 values, and a contact-sheet report with thumbnails.
- [ ] Fake Bee Orientation adapter validates the package only and creates a completed Training Run and non-user-facing Model Candidate with `model_purpose` `bee_orientation`.
- [ ] Fake adapter reports package/count metrics only, with no fake accuracy or fake confusion matrix.
- [ ] Candidate artifact is a fake adapter manifest, not fake model weights.
- [ ] Bee Detector and Bee Orientation Training Runs can coexist in job history and are clearly labelled by Model Purpose.
- [ ] Bee Orientation Model Candidates cannot be used for Bee Detector crop pre-labelling, Bee Detector benchmark evaluation, Bee Orientation benchmark execution, orientation inference, or Varroa Assessment.
- [ ] Focused Core API tests, package-builder tests, Playwright acceptance, and `pnpm verify:slice` pass.
- [ ] Live Postgres verification is run or explicitly recorded as pending if Docker/Postgres is unavailable.
- [ ] Slice 0022 implementation updates relevant document artifacts: `CONTEXT.md`, `requirements/roadmap.md`, `requirements/model-requirements.md`, `architecture/domain-model.md`, `architecture/bee-orientation-classifier-design.md`, this slice document, `architecture/parking-lot.md`, and Dataset Curator/Model Governance user-guide material where applicable.

## Open Questions

- None after Slice 0022 grilling and renewed acceptance scenario signoff.
