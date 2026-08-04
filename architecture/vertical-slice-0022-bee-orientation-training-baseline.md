# Vertical Slice 0022: Bee Orientation Training Baseline

Status: accepted for implementation after acceptance scenario signoff.

## Purpose

Let a Dataset Curator train the first non-user-facing Bee Orientation baseline from the same locked marked-bee Dataset Version used for Bee Detection and Bee Orientation.

This slice proves the first end-to-end Bee Orientation model-governance path. A curator can prepare one shared source Dataset Version of reviewed Oriented Bee Ellipses, derive a Bee Detection package and a Head Up / Head Down orientation training package from that same version, run a local baseline adapter, and receive a Bee Orientation Model Candidate.

The classifier is deliberately narrow. It does not find bees, detect Varroa, or produce a user-facing Varroa Assessment. It predicts whether a body-axis-normalized bee crop is `head_up` or `head_down`.

Because the source evidence is shared, this slice changes the meaning of the source Dataset Version from Bee Detector-only evidence to marked-bee evidence for Bee Detection and Bee Orientation. It must not create a second orientation-only source Dataset Version. It may create purpose-specific derived export packages and purpose-specific Training Runs, Model Candidates, and reports.

## Source Inputs

- `CONTEXT.md`: Oriented Bee Ellipse, Orientation Reliability, Dataset Version, Model Purpose, Bee Detection, Bee Localisation Model, Bee Orientation Model, Head-Up Normalized Bee Crop.
- `requirements/model-requirements.md`: MR-001A Bee Head Direction, MR-008B Orientation Reliability, MR-029A Training Run Records, MR-029B Model Candidate Records, MR-030 Benchmark Evaluation Before Promotion.
- `requirements/roadmap.md`: Bee Orientation candidate slices: Shared Marked-Bee Dataset Version Promotion, Bee Orientation Dataset Builder, Bee Orientation Model Baseline.
- `architecture/adr/0007-three-stage-bee-localisation-orientation-and-varroa-pipeline.md`: Bee Localisation, Bee Orientation, and Varroa Detection are separate Model Purposes with shared marked-bee source Dataset Versions.
- `architecture/bee-orientation-classifier-design.md`: binary Head Up / Head Down classifier, reliable complete visible bees only for the first corpus, purpose-specific derived packages and governance records.
- `architecture/vertical-slice-0021-orientation-reliability-review.md`: Orientation Reliability is now reviewed evidence on Oriented Bee Ellipses.

## Accepted Acceptance Scenarios

These scenarios were accepted for implementation on 2026-08-04.

```gherkin
Feature: Bee Orientation Training Baseline

  Scenario: Dataset Curator trains a Bee Orientation baseline from the shared marked-bee Dataset Version
    Given a Dataset Curator has a locked marked-bee Dataset Version for Bee Detection and Bee Orientation
    And the Dataset Version has Training and Validation Dataset Items
    And the Dataset Version contains reliable complete visible bee orientations
    When they start a Bee Orientation baseline Training Run
    Then HiveSight derives a Head Up / Head Down orientation training package from that same Dataset Version
    And HiveSight creates a non-user-facing Bee Orientation Model Candidate
    And the Model Governance view shows the run as Bee Orientation, not Bee Detector

  Scenario: Unreliable or partial bee orientations are excluded from the first orientation package
    Given a locked marked-bee Dataset Version contains reliable complete bees, unreliable complete bees, and partial visible bees
    When HiveSight checks Bee Orientation training readiness
    Then HiveSight counts only reliable complete visible bees as orientation training examples
    And HiveSight reports excluded orientation evidence by reason
    And HiveSight does not remove those excluded bees from the shared source Dataset Version

  Scenario: Bee Orientation and Bee Localisation stay in lockstep on source evidence
    Given a Bee Detector baseline and a Bee Orientation baseline are trained from marked-bee evidence
    When the Dataset Curator reviews their Training Runs
    Then both runs reference the same source Dataset Version
    And that Dataset Version is named and governed as Bee Detection and Bee Orientation evidence
    And each run has its own Model Purpose, derived package, adapter type, metrics, and Model Candidate
    And HiveSight does not offer a separate orientation-only source Dataset Version promotion path
```

## User Path

Given a Dataset Curator is in Model Governance
When they check Bee Orientation readiness, create or select the shared marked-bee Dataset Version for Bee Detection and Bee Orientation, and start Bee Orientation baseline training
Then HiveSight records a Bee Orientation Training Run and Model Candidate from reliable Head Up / Head Down examples derived from that shared source Dataset Version.

## Preconditions

- Slice 0021 is implemented: Oriented Bee Ellipses carry Orientation Reliability.
- The selected User has Dataset Curator capability.
- Workspace Data Use Agreement requirements remain enforced.
- At least one Training Dataset Item and one Validation Dataset Item exist for the shared marked-bee Dataset Version.
- Eligible orientation examples come from complete visible bees whose Orientation Reliability is `reliable`.
- The source image bytes for eligible examples are available.
- Benchmark evidence is not used as training input.
- Existing model-governance jobs and artifact storage are available.

## End-To-End Behaviour

The Model Governance tab treats the locked source Dataset Version as a shared marked-bee Dataset Version for Bee Detection and Bee Orientation. Bee Detection and Bee Orientation then appear as separate model workflows that consume different derived packages from that same source version.

In this slice, the existing Bee Detector Dataset Version creation flow is renamed or generalized so the Dataset Version no longer claims to be Bee Detector-only evidence. The source version's purpose should read as shared marked-bee evidence for Bee Detection and Bee Orientation. Existing Bee Detector training still receives its YOLO OBB derived package from that version.

The Model Governance tab gains a Bee Orientation baseline workflow alongside the Bee Detector workflow.

The curator can check Bee Orientation readiness. Readiness reports:

- source Dataset Version id and human-readable id;
- source Dataset Version purpose: Bee Detection and Bee Orientation marked-bee evidence;
- reliable complete-bee Training example count;
- reliable complete-bee Validation example count;
- excluded unreliable-orientation count;
- excluded partial-visible-bee count;
- source-image or artifact availability blockers;
- any warnings inherited from the shared Dataset Version.

When the curator starts training, HiveSight builds a derived orientation package from the locked shared source Dataset Version. The package contains normalized bee crops and labels:

- `head_up`: the crop is rotated so the stored centre-to-head direction points up;
- `head_down`: generated 180-degree flipped augmentation of eligible `head_up` examples for the first baseline.

The derived package records source maps back to Dataset Item, Training Crop, Source Image, and Oriented Bee Ellipse ids. It also records transform metadata: crop bounds, margin, rotation applied, resize/pad policy, augmentation flag, class map, and exclusion reasons.

The first adapter is a deterministic fake Bee Orientation classifier adapter for fast slice verification. The slice should leave a replaceable adapter seam for a real local MobileNet/ResNet-style classifier, but real training remains an explicit QA-lane follow-up.

The completed Training Run creates a Model Candidate with:

- `model_purpose`: `bee_orientation`;
- `model_family`: lightweight binary image classifier;
- `adapter_type`: fake for normal verification;
- `not_user_facing_reason`: baseline training only;
- metrics such as accuracy, head-up count, head-down count, and excluded evidence counts.

Model job history shows Bee Detector and Bee Orientation runs together but labels their Model Purpose clearly. The UI must not let a Bee Orientation candidate be used for crop YOLO pre-labelling or Bee Detector benchmark evaluation.

## Layers Touched

- Web UI: Rename or generalize Dataset Version wording so the source version is for Bee Detection and Bee Orientation; add Bee Orientation readiness, start-baseline action, run summary, and history labelling in Model Governance.
- Core API: Generalize Dataset Version purpose away from Bee Detector-only source evidence; add Bee Orientation readiness and training-run start path, or generalize the existing model-training endpoints to accept `model_purpose`.
- Analysis Service: Not touched for the fake baseline. Real classifier execution remains out of scope.
- Storage: Persist the generalized shared marked-bee Dataset Version purpose, Bee Orientation Training Runs, Model Candidates, derived package artifacts, reports, and source Dataset Version links through the existing store and Postgres-backed record path.
- Queue or async boundary: Reuse the existing model Training Run worker pattern.
- Contracts: Extend Dataset Version purpose wording and model-purpose parsing/API responses from Bee Detector-only to shared marked-bee source evidence plus `bee_orientation` Training Runs and Model Candidates.
- Observability: Record model-purpose-specific events for readiness, queued run, completed run, failed run, and candidate creation.

## Test Seams

- Seam: Core API Bee Orientation readiness
- Behaviour verified: only reliable complete visible bees count as eligible orientation examples; unreliable and partial bees are excluded with reasons; the source Dataset Version is explicitly shared by Bee Detection and Bee Orientation.
- Test style: focused Core API test.

- Seam: Bee Orientation derived package builder
- Behaviour verified: creates Head Up / Head Down examples from reliable complete-bee ellipse snapshots with source maps and transform metadata.
- Test style: service-level unit or workflow test using fixture image bytes.

- Seam: Bee Orientation Training Run workflow
- Behaviour verified: starting a fake Bee Orientation baseline creates a Training Run and non-user-facing `bee_orientation` Model Candidate linked to the same shared source Dataset Version.
- Test style: focused Core API test and API-level BDD scenario.

- Seam: Web Model Governance
- Behaviour verified: Dataset Curator can see Bee Orientation readiness, start the baseline, see completion, and distinguish Bee Orientation jobs from Bee Detector jobs.
- Test style: Playwright browser acceptance extending the existing model-governance flow.

- Seam: Postgres persistence
- Behaviour verified: Bee Orientation Training Run, Model Candidate, derived artifacts, and source Dataset Version linkage survive the Postgres-backed restart path.
- Test style: opt-in Postgres persistence test when Docker/Postgres is available.

## Data Shape

Minimum additions or generalizations:

- Dataset Version purpose changes from Bee Detector-only training evidence to shared marked-bee evidence for Bee Detection and Bee Orientation.
- Derived package/export formats identify the consuming Model Purpose, for example `bee_localisation_yolo_obb_v1` and `bee_orientation_head_up_down_v1`.
- Model Purpose values include `bee_orientation` alongside the existing Bee Detector implementation value.
- Bee Orientation readiness response:
  - workspace id;
  - source Dataset Version id;
  - source Dataset Version human-readable id;
  - eligible training example count;
  - eligible validation example count;
  - excluded unreliable-orientation count;
  - excluded partial-visible-bee count;
  - warnings and blockers.
- Derived orientation package artifact:
  - package id;
  - source Dataset Version id;
  - export format, for example `bee_orientation_head_up_down_v1`;
  - class map: `0 head_up`, `1 head_down`;
  - source map entries;
  - transform metadata;
  - exclusion reasons.
- Training Run:
  - `model_purpose`: `bee_orientation`;
  - source Dataset Version id;
  - derived package artifact id;
  - adapter type;
  - classifier settings: image size, margin, augmentation policy, epochs, seed, batch size.
- Model Candidate:
  - `model_purpose`: `bee_orientation`;
  - linked Training Run;
  - not user-facing reason.

## Out Of Scope

- Real MobileNet, ResNet, or EfficientNet training in normal slice verification.
- Bee Orientation benchmark evaluation or promotion thresholds.
- Bee Orientation inference in live Varroa Assessment.
- Head-Up Normalized Bee Crop generation for Varroa labelling or detection.
- Varroa Review Outcome labelling.
- Varroa Detector training.
- Partial visible bees in the first orientation training package.
- A broad rename of all existing `bee_detector` runtime or candidate contracts beyond the source Dataset Version meaning. Any compatibility cleanup should be small and directly required by this slice.
- Separate orientation-only source Dataset Version promotion.

## Acceptance Criteria

- [ ] The locked source Dataset Version is named and governed as marked-bee evidence for Bee Detection and Bee Orientation, not Bee Detector-only evidence.
- [ ] Dataset Curator can check Bee Orientation readiness from Model Governance.
- [ ] Readiness counts only reliable complete visible bee evidence as orientation-training eligible.
- [ ] Readiness reports unreliable and partial bee exclusions without removing them from the shared source Dataset Version.
- [ ] Starting a Bee Orientation baseline creates a derived Head Up / Head Down package from the same locked shared source Dataset Version.
- [ ] The fake Bee Orientation adapter creates a completed Training Run and non-user-facing Model Candidate with `model_purpose` `bee_orientation`.
- [ ] Bee Detector and Bee Orientation Training Runs can coexist in job history and are clearly labelled by Model Purpose.
- [ ] Bee Orientation Model Candidates cannot be used for Bee Detector crop pre-labelling or Bee Detector benchmark evaluation.
- [ ] Derived package artifacts include source maps and transform metadata sufficient to trace every example back to source evidence.
- [ ] Focused Core API tests, package-builder tests, Playwright acceptance, and `pnpm verify:slice` pass.
- [ ] Live Postgres verification is run or explicitly recorded as pending if Docker/Postgres is unavailable.

## Open Questions

- Should the first implementation expose one combined `Model Governance` control with a Model Purpose selector, or separate Bee Detector and Bee Orientation workflow panels?
- What fixed crop size and margin should the first orientation package use: 128x128 with a small margin, or 224x224 to match common pretrained classifier defaults?
