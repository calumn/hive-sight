# HiveSight Roadmap

Date started: 2026-08-03

This roadmap captures potential future vertical slices and work packages. It is not a committed delivery plan, and slice numbers are deliberately provisional unless a slice document already exists.

Use this document when planning the next slice or a tranche of work. Before promoting an item, review `architecture/parking-lot.md`, the relevant requirements, and recent slice closeout notes so the new slice closes the right loop rather than adding another loose end.

## Roadmap Principles

- Prefer thin, demoable vertical slices over broad platform projects.
- Keep Bee Localisation, Bee Orientation, and Varroa Detection independently testable, even if a future model combines capabilities.
- Protect benchmark evidence from training, routine tuning, and hindsight selection.
- Keep human review as the trust boundary for training and benchmark evidence.
- Keep product inspection evidence separate from model-improvement evidence until consent, contribution, and curator approval are explicit.
- Treat user-facing Varroa estimates as statistical claims, not just model outputs.

## Current Position

Recent slices have established:

- Training Data Collection inspections with multiple photos and crop-level bee annotation.
- Directed Oriented Bee Ellipses, where `rotation_degrees` points toward the bee head.
- Dataset Item role assignment, Dataset Versions, Training Runs, and Model Candidates.
- A local YOLO OBB Bee Localisation training baseline.
- Model Candidate crop pre-labelling under human review.
- A Dataset Repository Browser.
- A Bee Localisation benchmark evaluation and report path for Training Crop benchmark items.
- Postgres-backed product and model-governance metadata for the local development stack.

Important current limitation:

HiveSight can now build, train, and benchmark an early crop-level Bee Localisation candidate. It cannot yet make a user-facing Varroa assessment, predict bee head direction automatically, evaluate full-frame bee localisation, label Varroa evidence, or produce a statistically defensible infestation estimate.

## Immediate Candidate Slices

These are the strongest near-term candidates based on the current project state.

| Candidate | Type | Purpose | Why Now |
| --- | --- | --- | --- |
| Benchmark Dataset Curation Browser | Business / Technical | Let a Dataset Curator see and manage protected benchmark evidence as a named asset. | Slice 0015.4 uses benchmark items frozen inside a training Dataset Version; comparing candidates fairly soon needs a reusable benchmark lifecycle. |
| Full-Frame Bee Localisation Evaluation | Technical | Evaluate whether the Bee Localisation candidate can find bees in realistic whole-frame photos, not just reviewed crops. | Crop-level success does not prove the model works on real inspection photos. |
| Orientation Reliability Review | Business / Technical | Add explicit `reliable` / `unreliable` orientation review for directed bee ellipses. | Bee head direction is now meaningful, but reliability is not yet captured. |
| Bee Orientation Model Baseline | Technical | Train the first model that predicts head/tail direction for localised bees. | Varroa crops need consistent head-normalised orientation. |
| Varroa Review Outcome Labelling | Business | Add the CAPTCHA-like workflow for `visible_varroa_present`, `no_visible_varroa`, and `not_determined`. | Varroa training needs active positives and active negatives, not silent absence. |
| Dev User And Role Switching | Technical / UX | Let local development and acceptance testing switch between seeded development Users with their own Workspaces and capabilities. | Review, curation, contributor, and owner flows are now central enough that one hard-coded dev user hides behaviour. |
| Public Dataset Candidate Import | Technical / Governance | Import public USDA-ARS image/XML evidence as Candidate Annotations requiring human review. | This could accelerate dataset growth, but only if provenance and source rights are handled correctly. |

## Bee Localisation And Dataset Quality

| Candidate Slice | Type | Outcome |
| --- | --- | --- |
| Benchmark Dataset Version Lifecycle | Technical / Governance | Create named benchmark Dataset Versions independent of a candidate's training Dataset Version, with frozen sampling plan, source-group checks, and report reuse. |
| Model Candidate Comparison | Business / Technical | Compare multiple Bee Localisation Model Candidates against the same protected benchmark and show which is better under the same evidence. |
| Precise Rotated Geometry Evaluation | Technical | Replace `ellipse_match_v1` with a better-tested rotated box or ellipse matching rule before publishing quality claims. |
| Full-Frame And Tiled YOLO Export | Technical | Export larger regions or full-frame sides for model training once crop training is not enough. |
| Full-Frame Bee Localisation Evaluation | Technical | Benchmark model performance on dense, realistic frame photos and report losses by density, lighting, image quality, and Hive Configuration. |
| Dataset Quality Dashboard | Business / Technical | Show dataset coverage by role, source group, hive context, curriculum stage, bee density, image quality, annotation source, and warning state. |
| Dataset Item Supersession Workflow | Technical / Governance | Correct wrong Dataset Item assignments without mutating history consumed by Dataset Versions or Training Runs. |
| Public Dataset Candidate Import | Technical / Governance | Import external/public annotations as untrusted candidates with source rights, attribution, and source-group provenance. |

## Bee Orientation

| Candidate Slice | Type | Outcome |
| --- | --- | --- |
| Orientation Reliability Review | Business / Technical | Let a curator mark whether each directed ellipse has reliable head direction. |
| Bee Orientation Dataset Version | Technical / Governance | Freeze reliable complete-visible-bee evidence for orientation training and benchmark use. |
| Bee Orientation Model Baseline | Technical | Train and record the first head/tail classifier on body-axis-normalised bee crops. |
| Bee Orientation Benchmark Report | Technical | Report directed head/tail accuracy, angular error, unreliable-orientation rate, and performance by image quality and occlusion. |
| Orientation-Assisted Crop Normalisation | Technical | Produce head-normalised bee crops for Varroa labelling and model input, while excluding unreliable orientation from the first Varroa corpus. |

## Varroa Detection

| Candidate Slice | Type | Outcome |
| --- | --- | --- |
| Varroa Review Outcome Labelling | Business | Let a reviewer actively mark a bee crop as `visible_varroa_present`, `no_visible_varroa`, or `not_determined`, with mite point or tight-box markers for positives. |
| Varroa Model-Curation Sampling Plan | Business / Technical | Select Varroa labelling tasks using `stratified_random`, `curator_targeted`, and explicit `human_selected` versus `upstream_model_selected` metadata. |
| Varroa Dataset Repository Browser | Business / Technical | Show positive, active negative, and not-determined Varroa evidence by dataset role, source, orientation reliability, and selection method. |
| Varroa Detector Baseline | Technical | Train the first Varroa Detection model on head-normalised bee crops using active positives and active negatives. |
| Varroa Benchmark Report | Technical / Governance | Evaluate Varroa precision, recall, false positives, false negatives, marker agreement, and review-strength caveats. |
| Blind Independent Review For Varroa Benchmark | Business / Governance | Add second-review and adjudication workflow for benchmark Varroa evidence before any user-facing promotion claim. |

## Statistical Inference And Beekeeper Results

| Candidate Slice | Type | Outcome |
| --- | --- | --- |
| Inspection-Rate Sampling Policy | Business / Technical | Define how sampled bees support a stated visible Varroa rate and confidence interval. |
| End-To-End Pipeline Evaluation | Technical / Governance | Evaluate Bee Localisation, Bee Orientation, and Varroa Detection together on protected full-frame evidence. |
| Varroa Coverage And Suppression Rules | Business / Governance | Show coverage warnings and suppress headline estimates when evidence coverage is too weak. |
| First Model-Only Varroa Assessment Result | Business | Produce a clearly caveated, non-promoted inspection result from the staged pipeline. |
| Beekeeper Result Explanation | Business | Explain count, coverage, uncertainty, caveats, and action thresholds in language a beekeeper can act on. |
| Inspection Recovery Review | Business / Governance | Let a Workspace owner review and correct a suppressed or inadequate model-only result without rewriting the original result. |

## Product Workflow And UX

| Candidate Slice | Type | Outcome |
| --- | --- | --- |
| Modern Candidate Annotation Review Workflow | Business | Replace legacy dataset labelling with a current candidate-review workflow aligned to Model Candidate pre-labelling and public imports. |
| Annotation Productivity Improvements | Business | Add keyboard shortcuts, bulk accept/reject, better selection, zoom presets, last-saved status, and safer navigation for long annotation sessions. |
| Inspection Completion Semantics | Business | Define when a Training Data Collection inspection is complete and how incomplete work is reported. |
| Inspection History And Resume | Business | List inspections for a selected hive, resume recent work, and separate training-data collection from Varroa assessment history. |
| Hive Setup Edit And Rename | Business / Technical | Edit Apiary, Hive, and Hive Configuration safely while preserving historical provenance snapshots. |
| Dev User Switcher | Technical / UX | Let local testing switch between seeded Users, each with stable identity, default Workspace, and capabilities, before real auth exists. |
| Auth Boundary Decision | Business / Technical | Decide how external identity providers, HiveSight User records, Workspace Memberships, Contributor Access Scope, and internal capabilities fit together. |
| First External Login Provider | Business / Technical | Add the first real OpenID Connect login path, likely Google first, with Apple parked as a later provider option. |
| Workspace Collaboration And Membership Model | Business / Technical | Decide how multiple Users can share one Workspace, and whether one User can later belong to multiple Workspaces. |
| Reviewer Work Queue | Business / Technical | Let eligible Reviewer Users see shared review work from another User's Workspace without broad Workspace Membership or brittle named assignment. |
| Reviewer Correction Workflow | Business / Governance | Let reviewers identify wrong individual annotations, propose corrected geometry/classification, and keep correction provenance separate from the original evidence. |
| Task-Oriented User Guide Maintenance | Business / Technical | Keep `docs/user-guide.md` aligned with implemented workflows and add a closeout check when slices change user behaviour. |

## Data Governance, Consent, And Rights

| Candidate Slice | Type | Outcome |
| --- | --- | --- |
| Contributor Bundle And Permission Workflow | Business / Governance | Let a Dataset Curator create named contribution bundles and collect explicit contributor acceptance before showing assigned tasks. |
| Contribution Usage Record | Business / Governance | Let contributors see where their accepted bundle has been used without exposing other contributors or the wider workspace. |
| Withdrawal, Quarantine, And Retrain Enforcement | Technical / Governance | Exclude withdrawn evidence from future use, quarantine dependent artifacts, and require clean replacement training. |
| Contributor Deletion Request | Business / Governance | Separate immediate permission withdrawal from tracked source-image, annotation, artifact, and audit-retention handling. |
| Source Rights Record Approval | Technical / Governance | Record and approve public/open source rights, permitted use scopes, attribution, and invalidation handling. |
| Public Source Licence Compatibility Review | Governance | Decide which public licences support development, evaluation, sharing, publication, commercial use, or user-facing deployment. |
| Metadata Minimisation And Retention | Technical / Governance | Strip unnecessary image metadata and define retention boundaries for source images and derived artifacts. |

## Technical Platform And Operations

| Candidate Slice | Type | Outcome |
| --- | --- | --- |
| Background Job Runner Separation | Technical | Move training/evaluation execution out of web request handling and into a clearer local worker boundary. |
| Model Job Operations Dashboard | Technical / UX | Show active jobs, logs, heartbeats, cancellation, failure reason, artifact paths, and recovery actions in one place. |
| Object Storage For Images And Artifacts | Technical | Move image bytes and model artifacts to a deliberate storage abstraction rather than local file paths. |
| Persistence Schema Hardening | Technical | Refine indexes, constraints, repositories, migration discipline, and local/QA database separation. |
| API Contract Governance | Technical | Version and review Core API, Analysis Service, and model job contracts as boundaries mature. |
| Real Authentication Provider And Session Architecture | Business / Technical | Replace local dev session headers with delegated authentication, production sessions, and HiveSight-owned authorization decisions. |
| Social Login Provider Expansion | Business / Technical | Add Apple or other identity providers after the first external-login path proves the User and permission model. |
| Release And Operations Readiness | Technical / Governance | Add deployment target, runbooks, backups, rollback, health checks, and incident handling before external use. |

## Testing And Quality

| Candidate Slice | Type | Outcome |
| --- | --- | --- |
| UI-Level Gherkin Harness | Technical / Quality | Add BDD-style UI acceptance where it improves behaviour readability beyond Playwright specs. |
| Real Model QA Test Environment | Technical / Quality | Keep real YOLO training/evaluation smoke tests outside normal CI but runnable on demand against a QA database. |
| Test Coverage Report Expansion | Technical / Quality | Extend slice verification reports to show unit, API, BDD, UI, real-adapter QA, and known skipped tests in one place. |
| Defect Regression Guard Cleanup | Technical / Quality | Review recent defects and ensure each important fix has the right regression test level. |
| Full SDLC Traceability Audit | Governance / Quality | Periodically check vision, requirements, ADRs, slices, code, tests, user guide, parking lot, and observations for drift. |

## Suggested Planning Order

The likely next tranche should stay model-evidence focused:

1. Add Dev User And Role Switching before the next role-sensitive workflow, so owner, Dataset Curator, Reviewer, Contributor, and unprivileged-user paths can be exercised honestly.
2. Improve benchmark curation and comparison so model quality claims are not tied to a single training run.
3. Evaluate Bee Localisation on full-frame evidence before assuming crop-level success transfers.
4. Add Orientation Reliability and then train/evaluate the first Bee Orientation baseline.
5. Add Varroa Review Outcome labelling with active negative evidence.
6. Train and benchmark the first Varroa Detector.
7. Only then design the first user-facing Varroa assessment result and statistical inference workflow.

This order can change if annotation productivity becomes the limiting factor, or if source-rights/contributor governance becomes necessary before using external evidence.
