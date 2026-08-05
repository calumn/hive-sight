# Vertical Slice 0023: Real Bee Training Baseline

Status: implemented; acceptance scenarios signed off on 2026-08-05; focused verification passed on 2026-08-05.

## Purpose

Let a Dataset Curator train a real, non-user-facing Bee Orientation Model Candidate alongside Bee Localisation from one shared Marked-Bee Dataset Version.

This slice turns the Slice 0022 Bee Orientation package proof into a real predictive-training proof while correcting the operator language from YOLO-specific commands to Bee Training. The source evidence remains one locked Marked-Bee Dataset Version. Bee Localisation and Bee Orientation produce separate Training Runs, artifacts, reports, and Model Candidates, but they do not create separate source Dataset Versions.

The real Bee Orientation adapter is deliberately narrow. It trains a binary Head Up / Head Down classifier on body-axis-normalized crop examples from the existing orientation package. It does not benchmark the candidate, run live orientation inference, generate Head-Up Normalized Bee Crops for Varroa, or change user-facing Varroa Assessment.

## Source Inputs

- `CONTEXT.md`: Marked-Bee Dataset Version, Bee Localisation Model, Bee Orientation Model, Model Purpose, Training Run, Model Candidate, Head-Up Normalized Bee Crop.
- `requirements/model-requirements.md`: MR-001 Bee Localisation, MR-001A Bee Head Direction, MR-008B Orientation Reliability, MR-029A Training Run Records, MR-029B Model Candidate Records, Bee Orientation Metrics.
- `requirements/roadmap.md`: Bee Orientation real training, benchmark, and crop-normalisation candidate sequence.
- `architecture/adr/0007-three-stage-bee-localisation-orientation-and-varroa-pipeline.md`: Bee Localisation, Bee Orientation, and Varroa Detection remain separately governed Model Purposes.
- `architecture/bee-orientation-classifier-design.md`: first Bee Orientation implementation as a binary Head Up / Head Down image classifier.
- `architecture/vertical-slice-0022-bee-orientation-training-baseline.md`: shared Marked-Bee Dataset Version, orientation package builder, fake orientation adapter, and non-user-facing orientation candidate.

## Accepted Acceptance Scenarios

These scenarios were accepted for implementation on 2026-08-05.

```gherkin
Feature: Real Bee Training Baseline

  Scenario: Dataset Curator sees one Bee Training workflow
    Given a Dataset Curator has a shared Marked-Bee Dataset Version
    When they open Model Governance
    Then HiveSight shows Bee Localisation and Bee Orientation readiness from that same Dataset Version
    And HiveSight offers one primary action to Train bee baseline
    And the UI does not describe the workflow as YOLO training

  Scenario: Bee Training commands replace YOLO-named commands
    Given a developer is preparing the local model-training stack
    When they inspect the supported pnpm commands
    Then HiveSight documents `pnpm model:setup:bee`
    And HiveSight documents `pnpm dev:all:bee-training`
    And HiveSight documents `pnpm model:train:bee`
    And YOLO-named user commands are not available as supported commands
    And internal adapter metadata may still identify `ultralytics_yolo_obb` where technically accurate

  Scenario: Bee Training readiness reports both model purposes
    Given a shared Marked-Bee Dataset Version has Bee Localisation evidence and Bee Orientation evidence
    When HiveSight checks Bee Training readiness
    Then HiveSight reports Bee Localisation adapter availability
    And HiveSight reports Bee Orientation adapter availability
    And HiveSight reports whether each model purpose has enough eligible Training and Validation evidence
    And HiveSight blocks Train bee baseline when either model purpose is not ready

  Scenario: Bee Training uses one shared source Dataset Version
    Given Bee Training readiness is satisfied
    When the Dataset Curator starts Train bee baseline
    Then HiveSight starts Bee Localisation training from the selected Marked-Bee Dataset Version
    And after Bee Localisation completes, HiveSight starts Bee Orientation training from the same Marked-Bee Dataset Version
    And the job history shows two separate Training Runs with separate Model Purposes
    And HiveSight does not create separate source Dataset Versions for Bee Localisation and Bee Orientation

  Scenario: Real Bee Orientation adapter creates a non-user-facing candidate
    Given Bee Orientation training starts with the real orientation adapter
    When the Training Run completes
    Then HiveSight creates a Bee Orientation Model Candidate with real model artifacts
    And the Training Run records the package hash, architecture, device, settings, logs, validation accuracy, and confusion matrix
    And the report states that validation metrics are training-run validation only, not benchmark evidence
    And the candidate is not available for Varroa Assessment or automatic Head-Up Normalized Bee Crop generation

  Scenario: Insufficient orientation data blocks real orientation training
    Given a shared Marked-Bee Dataset Version has fewer than four eligible reliable complete bees in Training or Validation
    When HiveSight checks Bee Training readiness
    Then HiveSight reports the Bee Orientation data blocker
    And HiveSight does not start Train bee baseline
    And the message explains the minimum required orientation evidence

  Scenario: Local dependency problems are explained before training
    Given Docker Desktop or the local Postgres database is unavailable
    When a developer starts the Bee Training dev stack
    Then HiveSight reports that the local database dependency is unavailable
    And HiveSight tells the developer to start Docker Desktop and bring the database up
    And HiveSight does not reset or seed the database automatically
```

## User Path

Given a Dataset Curator has reviewed marked-bee evidence and created a shared Marked-Bee Dataset Version,
When they start **Train bee baseline** from Model Governance or run the local `pnpm model:train:bee` command,
Then HiveSight trains Bee Localisation first and Bee Orientation second from that same source Dataset Version and records separate non-user-facing Model Candidates for each Model Purpose.

## Preconditions

- Slice 0022 is implemented.
- The selected User has Dataset Curator capability.
- Workspace Data Use Agreement requirements remain enforced.
- A shared Marked-Bee Dataset Version exists or can be created from eligible Training and Validation Dataset Items.
- Bee Localisation readiness is satisfied for the selected Dataset Version.
- Bee Orientation readiness includes at least four eligible reliable complete bees in Training and four in Validation.
- Optional real Bee Training dependencies are installed through the Bee Training setup command.
- Local Postgres is available for the Bee Training dev lane.

## Grilled Design Decisions

- Use a real PyTorch/torchvision Bee Orientation adapter for the first predictive implementation.
- Keep fast tests on fake adapters; real training remains an explicit local lane.
- Stop Slice 0023 at a non-user-facing trained Bee Orientation Model Candidate.
- Do not add orientation inference, Head-Up Normalized Bee Crop generation, benchmark evaluation, or Varroa changes.
- Use the Slice 0022 package examples only: generated head-up and 180-degree head-down pairs, without additional random augmentations in this slice.
- Record validation accuracy and a Head Up / Head Down confusion matrix as training-run validation only, not benchmark evidence.
- Replace YOLO-named user commands with Bee Training commands and remove YOLO aliases now.
- Keep internal adapter ids such as `ultralytics_yolo_obb` where technically accurate.
- `pnpm model:train:bee` trains both model purposes sequentially from one shared Marked-Bee Dataset Version.
- Create one shared Marked-Bee Dataset Version first, then start separate Bee Localisation and Bee Orientation Training Runs from that exact version.
- If the sequential Bee Localisation run fails, stop and report that Bee Orientation was not started.
- Do not introduce a parent Bee Training Baseline Run entity yet.
- Use CPU by default for the first real Bee Orientation adapter, recording the device used.
- Add an append-only local QA fixture/helper path; do not reset model-governance data by default.
- Add a Docker/Postgres preflight for the Bee Training dev lane and never migrate, reset, or seed automatically.
- Update user-facing UI and docs from YOLO language to Bee Localisation / Bee Training language, including crop pre-label wording.

## End-To-End Behaviour

Model Governance presents one Bee Training workflow around a selected shared Marked-Bee Dataset Version. Bee Localisation and Bee Orientation readiness are shown side by side. The primary action is **Train bee baseline**.

When the action starts, HiveSight creates or uses one shared source Dataset Version and starts Bee Localisation training first. If that Training Run completes, HiveSight starts Bee Orientation training from the same Dataset Version. The existing one-active-model-job guard remains acceptable for this slice, so the two jobs run sequentially rather than concurrently.

The real Bee Orientation adapter trains a small binary classifier from the existing derived package. It records real artifacts, settings, package hash, logs, validation accuracy, confusion matrix, model architecture, adapter metadata, base dependency versions where available, and device. The report must state that these are training-run validation metrics only.

The job history shows two separate Training Runs with separate Model Purposes. The Bee Orientation candidate remains non-user-facing and cannot be used for benchmark evaluation, live orientation inference, automatic Head-Up Normalized Bee Crop generation, or Varroa Assessment.

The developer command surface changes from YOLO-specific names to Bee Training names. User-facing docs and UI teach Bee Training and Bee Localisation language, not YOLO as the product concept.

## Layers Touched

- Web UI: Model Governance shows combined Bee Training readiness, one **Train bee baseline** action, separate purpose-labelled Training Runs, and Bee Localisation pre-label wording instead of crop-YOLO wording.
- Core API: Add combined Bee Training readiness/start behaviour or a thin orchestration path over existing per-purpose training workflows; add real Bee Orientation adapter availability; enforce the shared Dataset Version and minimum orientation evidence gates.
- Analysis Service: Not touched.
- Storage: Reuse existing Dataset Version, Training Run, Model Candidate, and artifact records. No parent Bee Training entity in this slice.
- Queue or async boundary: Reuse existing local model-job guard and run Bee Localisation then Bee Orientation sequentially.
- Contracts: Add or extend readiness/start responses so both model purposes are visible and separately blocked; keep internal adapter ids where accurate.
- Observability: Record purpose-specific readiness, skipped, started, completed, failed, artifact, and candidate-creation events.
- Tooling: Replace YOLO-named user commands with Bee Training commands and add Docker/Postgres preflight messaging.

## Test Seams

- Seam: Bee Training command surface
- Behaviour verified: supported commands are `model:setup:bee`, `dev:all:bee-training`, and `model:train:bee`; YOLO-named user commands are removed; docs use Bee Training language.
- Test style: package-script/static documentation check plus smoke command checks where practical.

- Seam: Bee Training readiness
- Behaviour verified: response reports Bee Localisation and Bee Orientation adapter availability and blocks the combined action when either purpose is not ready.
- Test style: focused Core API tests and API-level BDD.

- Seam: Shared Dataset Version orchestration
- Behaviour verified: both Training Runs use the same Marked-Bee Dataset Version; no separate source Dataset Version is created for Orientation.
- Test style: API/workflow tests and BDD.

- Seam: Real Bee Orientation adapter
- Behaviour verified: trains from the orientation package, emits real artifacts, logs, settings, validation accuracy, confusion matrix, package hash, architecture, and device.
- Test style: adapter-level smoke test with a controlled tiny fixture, plus opt-in real-adapter QA.

- Seam: UI Model Governance
- Behaviour verified: Dataset Curator sees one Bee Training workflow, purpose-specific readiness, one **Train bee baseline** action, purpose-labelled job history, and non-YOLO user-facing wording.
- Test style: Playwright browser acceptance.

- Seam: Local dependency preflight
- Behaviour verified: unavailable Docker/Postgres is reported clearly and does not reset or seed data.
- Test style: script-level test or focused smoke test with dependency checks mocked where practical.

## Data Shape

Minimum additions or generalizations:

- Bee Training readiness response:
  - selected Marked-Bee Dataset Version id and human-readable id;
  - Bee Localisation readiness summary;
  - Bee Orientation readiness summary;
  - adapter availability per Model Purpose;
  - blockers and warnings per Model Purpose;
  - combined `eligible_to_start_bee_training` value.
- Bee Orientation real adapter settings:
  - architecture, initially a small MobileNet-style classifier;
  - image size;
  - epochs;
  - batch size;
  - seed;
  - device, default `cpu`;
  - package hash;
  - dependency/runtime metadata where available.
- Bee Orientation metrics:
  - validation accuracy;
  - confusion matrix for `head_up` and `head_down`;
  - train/validation counts;
  - loss or accuracy per epoch when available;
  - metric scope value that explicitly marks training-run validation.
- Command names:
  - `pnpm model:setup:bee`;
  - `pnpm dev:all:bee-training`;
  - `pnpm dev:lan:bee-training`;
  - `pnpm model:train:bee`.

## Out Of Scope

- Bee Orientation Benchmark Evaluation.
- User-facing Model Version promotion.
- Orientation inference in live Varroa Assessment.
- Automatic Head-Up Normalized Bee Crop generation outside the training package.
- Varroa Review Outcome labelling.
- Varroa Detection training or evaluation.
- A parent Bee Training Baseline Run entity.
- Per-Model-Purpose concurrent training scheduler redesign.
- Renaming internal adapter ids or broad compatibility contract values that are not user-facing.
- Random augmentation policy beyond the existing generated head-up/head-down package pairs.
- Database reset, migration, or seeding inside the Bee Training start command.

## Acceptance Criteria

- [x] Model Governance shows one Bee Training workflow using a shared Marked-Bee Dataset Version.
- [x] Model Governance shows Bee Localisation and Bee Orientation readiness from the same selected Dataset Version.
- [x] Model Governance offers one primary **Train bee baseline** action and does not describe the workflow as YOLO training.
- [x] Supported user commands are renamed to Bee Training command language.
- [x] YOLO-named user commands are removed from the supported command surface.
- [x] Internal adapter metadata may still identify `ultralytics_yolo_obb` where technically accurate.
- [x] Combined readiness reports adapter availability and data blockers separately for Bee Localisation and Bee Orientation.
- [x] Combined training is blocked if either purpose is not ready.
- [x] Real Bee Orientation training requires at least four eligible reliable complete bees in Training and four in Validation.
- [x] `Train bee baseline` starts Bee Localisation first and Bee Orientation second.
- [x] Both Training Runs reference the same Marked-Bee Dataset Version.
- [x] If Bee Localisation fails, Bee Orientation is not started in this slice.
- [x] Real Bee Orientation adapter trains a small PyTorch/torchvision classifier on the existing orientation package.
- [x] Real Bee Orientation Training Run records package hash, architecture, device, settings, logs, validation accuracy, and confusion matrix.
- [x] Bee Orientation validation metrics are labelled as training-run validation only, not benchmark evidence.
- [x] Bee Orientation Model Candidate remains non-user-facing and unavailable for benchmark evaluation, orientation inference, Head-Up Normalized Bee Crop generation, or Varroa Assessment.
- [x] Bee Localisation pre-label UI wording uses product language instead of implementation-adapter language.
- [x] Local dependency preflight explains unavailable Docker/Postgres without resetting or seeding the database.
- [x] Append-only QA fixture/helper path exists for local proof-of-life without requiring real weekend photos.
- [x] Focused Core API tests, adapter tests, command/script checks, and Playwright acceptance pass before closeout.
- [ ] `pnpm verify:slice` passes before closeout.
- [x] Live Postgres verification is run or explicitly recorded as pending if Docker/Postgres is unavailable.
- [x] Implementation updates relevant docs: `requirements/roadmap.md`, `docs/user-guide.md`, this slice document, command examples, `architecture/parking-lot.md`, and `requirements/ai-sdlc-observations.md`.

## Verification Notes

- Focused Core API and API-level BDD: passed on 2026-08-05.
- Web TypeScript and dev preflight command checks: passed on 2026-08-05.
- Focused Playwright acceptance for the combined Bee Training workflow: passed on 2026-08-05 against the running Postgres-backed dev stack.
- `pnpm verify:slice`: Core API, Analysis Service, Web TypeScript, and dev script checks passed on 2026-08-05. The default browser phase first could not start because the user's existing Core API was already running on port 8000. The reuse-existing-server rerun passed the Slice 0023 scenario but the overall browser suite failed in older state-sensitive scenarios against the already-populated dev database and real-adapter lane. This is recorded in `reports/slice-verification/latest.md`.

## Open Questions

- None after Slice 0023 grilling and acceptance scenario signoff.
