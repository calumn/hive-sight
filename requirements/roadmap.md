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
- Development User switching across seeded Users and Workspaces.
- A Reviewer Work Queue for eligible shared review work.
- A staged Training Inspection Workflow with Inspection Setup, Crop Selection, Bee Annotation, Crop Governance, and Model Governance.

Important current limitation:

HiveSight can now build, train, and benchmark an early crop-level Bee Localisation candidate, build and evaluate the first Bee Orientation baseline path, label bee-level Varroa Review Outcomes for human model-curation evidence, roll those reviewed outcomes into a current photo-visible Varroa evidence summary, preview deterministic stub Varroa Detector boxes for one eligible Head-Up Normalized Bee Crop, and run a transient model-assisted frame mite count across eligible bees on one photographed frame. It cannot yet make a user-facing Varroa assessment, trigger HiveSight Advisor, persist model-only Varroa result history, or produce a statistically defensible photo-visible estimate.

## Immediate Candidate Slices

These are the strongest near-term candidates based on the current project state.

| Candidate | Type | Purpose | Why Now |
| --- | --- | --- | --- |
| Benchmark Dataset Curation Browser | Business / Technical | Let a Dataset Curator see and manage protected benchmark evidence as a named asset. | Slice 0015.4 uses benchmark items frozen inside a training Dataset Version; comparing candidates fairly soon needs a reusable benchmark lifecycle. |
| Full-Frame Bee Localisation Evaluation | Technical | Evaluate whether the Bee Localisation candidate can find bees in realistic whole-frame photos, not just reviewed crops. | Crop-level success does not prove the model works on real inspection photos. |
| Orientation Reliability Review | Business / Technical | Add explicit `reliable` / `unreliable` orientation review for directed bee ellipses. | Promoted into `architecture/vertical-slice-0021-orientation-reliability-review.md`. |
| Bee Orientation Model Baseline | Technical | Build and validate the first Head Up / Head Down orientation package from the shared Bee Detection and Bee Orientation marked-bee Dataset Version, and record the first non-user-facing orientation candidate. | Implemented by Slice 0022 as `architecture/vertical-slice-0022-bee-orientation-training-baseline.md`; real predictive orientation training and benchmark evaluation remain later work. |
| Varroa Review Outcome Labelling | Business | Designed as Slice 0025: add the CAPTCHA-like workflow for `visible_varroa_present`, `no_visible_varroa`, and `not_determined` on Head-Up Normalized Bee Crops, using reliable complete human-reviewed bees only. | Varroa training needs active positives and active negatives, not silent absence. |
| Varroa Evidence Methodology And Gold-Standard Design | Research / Governance | Establish the full-depth annotation, review, split, sampling-experiment, and field-calibration protocol before Varroa corpus construction begins. | This is documented in `requirements/varroa-evidence-methodology.md`; the protocol prevents training convenience from becoming an unsupported beekeeper-facing statistical claim. |
| Frame-Level Varroa Result Summary | Business / Technical | Implemented as Slice 0026: derive a frame/photo-level visible Varroa evidence summary from reviewed bee-level Varroa Review Outcomes, including marker count, positive bee count, active negatives, unresolved bees, and coverage. | This gives the upcoming detector and Advisor-context work a coherent result shape. |
| Varroa Detector Adapter Seam | Technical | Implemented as Slice 0027: add a replaceable deterministic stub adapter seam that can return likely Varroa detections for one eligible Head-Up Normalized Bee Crop, with paired clean/annotated preview UI and non-user-facing provenance. | Once a frame-level result shape exists, adapter output has somewhere coherent to land without coupling the UI to a specific model runtime. |
| Frame Mite Counting Workflow | Business / Technical | Implemented as Slice 0028: run the Varroa detector path over eligible bees from a photographed frame and produce the first model-assisted visible mite count with caveats. | This is the first end-to-end mite-counting path, even if the adapter is still stubbed. |
| Advisor Varroa Context API | Technical / Integration | Planned as Slice 0029: expose the minimum Varroa result context HiveSight Advisor needs, without yet accepting treatment recommendations back into HiveSight. | This reaches the integration point while keeping Advisor treatment logic outside HiveSight. |
| Varroa Corpus Governance | Business / Governance | Preserved as Slice 0030: review saved Varroa Review Outcomes across the Workspace and record include, exclude, or defer decisions before Varroa Detector training datasets are frozen. | Still needed for model-curation discipline, but the current tranche prioritises the frame-count and Advisor-context path. |
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
| Bulk Dataset Role Assignment | Business / UX | Safely assign many completed crops into dataset roles with source-leakage, review-strength, and benchmark-protection guardrails. |
| Negative Or Background Bee Localisation Dataset Role | Technical / Governance | Decide whether completed no-bee crops should become explicit background evidence for Bee Localisation training and export. |
| Dataset Item Supersession Workflow | Technical / Governance | Correct wrong Dataset Item assignments without mutating history consumed by Dataset Versions or Training Runs. |
| Public Dataset Candidate Import | Technical / Governance | Import external/public annotations as untrusted candidates with source rights, attribution, and source-group provenance. |

## Bee Orientation

| Candidate Slice | Type | Outcome |
| --- | --- | --- |
| Orientation Reliability Review | Business / Technical | Promoted into `architecture/vertical-slice-0021-orientation-reliability-review.md` to let a curator mark whether each directed ellipse has reliable head direction. |
| Shared Marked-Bee Dataset Version Promotion | Technical / Governance | Implemented in Slice 0022 for new Model Governance Dataset Versions: one marked oriented-bee Dataset Version stays in lockstep for Bee Localisation and Bee Orientation source evidence. |
| Bee Orientation Dataset Builder | Technical / Governance | Implemented in Slice 0022 as a derived package builder that exports reliable complete directed ellipses into reproducible Head Up / Head Down crop packages with source maps and exclusion reasons. |
| Real Bee Training Baseline | Technical | Implemented in Slice 0023: Bee Training commands replace YOLO-named user commands, Bee Localisation and Bee Orientation train sequentially from one shared Marked-Bee Dataset Version, and the real Bee Orientation adapter creates a non-user-facing Model Candidate with training-run validation metrics only. |
| Bee Orientation Benchmark Report | Technical | Implemented by Slice 0024: evaluate a completed Bee Orientation Model Candidate against protected reliable complete benchmark bees from its shared Marked-Bee Dataset Version, report Head Up / Head Down accuracy and confusion matrix, and keep evidence purpose-limited. Angular error, promotion thresholds, live orientation inference, and Head-Up Normalized Bee Crop generation remain later work. |
| Orientation-Assisted Crop Normalisation | Technical | Partly folded into Slice 0025 as the review-preview transform for human Varroa labelling. Automated orientation inference, model-input package export, and live pipeline crop generation remain later work. |

## Varroa Detection

| Candidate Slice | Type | Outcome |
| --- | --- | --- |
| Varroa Review Outcome Labelling | Business | Designed as Slice 0025: let a Dataset Curator actively mark a Head-Up Normalized Bee Crop as `visible_varroa_present`, `no_visible_varroa`, or `not_determined`, with mite point markers for positives. |
| Frame-Level Varroa Result Summary | Business / Technical | Implemented as Slice 0026: derive a current photo/frame-level visible Varroa evidence summary from reviewed bee-level outcomes, including positive bees, active negatives, unresolved bees, coverage, and visible mite marker count. |
| Varroa Detector Adapter Seam | Technical | Implemented as Slice 0027: add a replaceable deterministic stub adapter boundary for previewing likely Varroa detections on one eligible Head-Up Normalized Bee Crop, without persisting model output as human review evidence. |
| Frame Mite Counting Workflow | Business / Technical | Implemented as Slice 0028: run the Varroa detector path over eligible bees from a photographed frame and produce the first model-assisted visible mite count with caveats. |
| Advisor Varroa Context API | Technical / Integration | Planned as Slice 0029: expose frame-level Varroa result context for HiveSight Advisor without importing treatment advice back into HiveSight yet. |
| Varroa Corpus Governance | Business / Governance | Preserved as Slice 0030: show saved Varroa Review Outcomes across the Workspace, separate positive, active negative, unresolved, stale, included, excluded, and deferred evidence, and record current corpus curation decisions without freezing a Dataset Version. |
| Gold-Standard Full-Frame Annotation Pilot | Research / Technical | Demonstrate the methodology on a small, fully reconciled set of complete frame images and measure annotation/review workload and agreement. |
| Varroa Model-Curation Sampling Plan | Business / Technical | Select Varroa labelling tasks using `stratified_random`, `curator_targeted`, and explicit `human_selected` versus `upstream_model_selected` metadata. |
| Varroa Dataset Repository Browser | Business / Technical | Show positive, active negative, and not-determined Varroa evidence by dataset role, source, orientation reliability, and selection method. |
| Varroa Detector Baseline | Technical | Train the first Varroa Detection model on Head-Up Normalized Bee Crops using active positives and active negatives. |
| Varroa Benchmark Report | Technical / Governance | Evaluate Varroa precision, recall, false positives, false negatives, marker agreement, and review-strength caveats. |
| Blind Independent Review For Varroa Benchmark | Business / Governance | Add second-review and adjudication workflow for benchmark Varroa evidence before any user-facing promotion claim. |

## Statistical Inference And Beekeeper Results

| Candidate Slice | Type | Outcome |
| --- | --- | --- |
| Frame-Level Varroa Result Summary | Business / Technical | Implemented as Slice 0026: show the current countable evidence for one photographed frame before claiming a statistical visible Varroa rate. |
| Inspection-Rate Sampling Policy | Business / Technical | Define how sampled bees support a stated visible Varroa rate and confidence interval. |
| Sampling-Strategy Simulation And Calibration | Research / Technical | Use protected full-depth frames to select an initial spatial/quality-stratified and possibly sequential inspection-rate plan; separately study paired field-reference measurements without conflating their targets. |
| End-To-End Pipeline Evaluation | Technical / Governance | Evaluate Bee Localisation, Bee Orientation, and Varroa Detection together on protected full-frame evidence. |
| Varroa Coverage And Suppression Rules | Business / Governance | Show coverage warnings and suppress headline estimates when evidence coverage is too weak. |
| First Model-Only Varroa Assessment Result | Business | Produce a clearly caveated, non-promoted inspection result from the staged pipeline. |
| Beekeeper Result Explanation | Business | Explain count, coverage, uncertainty, caveats, and action thresholds in language a beekeeper can act on. |
| Inspection Recovery Review | Business / Governance | Let a Workspace owner review and correct a suppressed or inadequate model-only result without rewriting the original result. |

## Treatment And Advisor Integration

HiveSight remains the system of record for hive identity, Varroa assessment evidence, and treatment history. HiveSight Advisor may recommend a treatment plan from grounded guidance, but HiveSight owns whether the beekeeper accepts it, records it, applies it, and later judges the result.

| Candidate Slice | Type | Outcome |
| --- | --- | --- |
| Hive Treatment History | Business / Technical | Let a Beekeeper record a Hive Treatment Course, one or more Treatment Applications, and simple notes against a selected Hive. |
| Advisor Varroa Context API | Technical / Integration | Planned as Slice 0029: expose the minimum frame-level Varroa evidence, hive, apiary, jurisdiction, and recent treatment context HiveSight Advisor needs to decide whether treatment guidance can be produced. |
| Advisor Treatment Recommendation Intake | Business / Technical | Accept a Treatment Recommendation from HiveSight Advisor, show it to the Beekeeper as suggested rather than applied, and let the Beekeeper accept or decline it. |
| Broader Advisor Context API | Technical / Integration | Extend the Varroa context contract with richer hive, apiary, jurisdiction, inspection-history, and treatment-history context once the first Advisor integration shape has proved useful. |
| Treatment Completion And Follow-up Outcome | Business | Let a Beekeeper mark a Hive Treatment Course complete and relate later Inspection evidence to the treatment outcome without rewriting the original recommendation. |

## Product Workflow And UX

| Candidate Slice | Type | Outcome |
| --- | --- | --- |
| Modern Candidate Annotation Review Workflow | Business | Replace legacy dataset labelling with a current candidate-review workflow aligned to Model Candidate pre-labelling and public imports. |
| Training Inspection Workflow Separation Follow-ons | Business / UX | Refine the implemented staged Training Data Collection workflow, especially exact resume position, completion semantics, and productivity improvements. |
| Annotation Productivity Improvements | Business | Add keyboard shortcuts, bulk accept/reject, better selection, zoom presets, last-saved status, and safer navigation for long annotation sessions. |
| Crop Bounds Editing After Save | Business / UX | Let a Dataset Curator safely resize or reposition saved Training Crops with clear invalidation rules for annotations, reviews, and Dataset Items. |
| Inspection Completion Semantics | Business | Define when a Training Data Collection inspection is complete and how incomplete work is reported. |
| Inspection History And Resume | Business | List inspections for a selected hive, resume recent work, and separate training-data collection from Varroa assessment history. |
| Resume Exact Training Workflow Position | Business / UX | Resume the exact stage, photo, crop, and editor context from a long-running annotation session once workflow state is stable. |
| Hive Setup Edit And Rename | Business / Technical | Edit Apiary, Hive, and Hive Configuration safely while preserving historical provenance snapshots. |
| Auth Boundary Decision | Business / Technical | Decide how external identity providers, HiveSight User records, Workspace Memberships, Contributor Access Scope, and internal capabilities fit together. |
| First External Login Provider | Business / Technical | Add the first real OpenID Connect login path, likely Google first, with Apple parked as a later provider option. |
| Workspace Collaboration And Membership Model | Business / Technical | Decide how multiple Users can share one Workspace, and whether one User can later belong to multiple Workspaces. |
| Reviewer Work Queue Follow-ons | Business / Technical | Extend the implemented Reviewer Work Queue with claiming, multi-reviewer rules, correction workflow, and broader review operations where needed. |
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
| Dedicated Model Governance Page | Technical / UX | Move Dataset Versions, Training Runs, Model Candidates, Benchmark Evaluations, and future promotion controls into a focused model-governance surface. |
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
| Cross-Inspection Submitted Review Dashboard | Business / Quality | Let Dataset Curators see crops they submitted for review across inspections so waiting work can be chased or cancelled deliberately. |
| Real Model QA Test Environment | Technical / Quality | Keep real YOLO training/evaluation smoke tests outside normal CI but runnable on demand against a QA database. |
| Test Coverage Report Expansion | Technical / Quality | Extend slice verification reports to show unit, API, BDD, UI, real-adapter QA, and known skipped tests in one place. |
| Defect Regression Guard Cleanup | Technical / Quality | Review recent defects and ensure each important fix has the right regression test level. |
| Full SDLC Traceability Audit | Governance / Quality | Periodically check vision, requirements, ADRs, slices, code, tests, user guide, parking lot, and observations for drift. |

## Suggested Planning Order

The likely next tranche should stay model-evidence focused:

1. Slice 0027 Varroa Detector adapter seam is implemented, so a stubbed or real model can return mite detections for Head-Up Normalized Bee Crops.
2. Add the Slice 0029 Advisor Varroa Context API so HiveSight Advisor can receive treatment-relevant Varroa context without moving treatment decisions into HiveSight.
3. Preserve Slice 0030 Varroa Corpus Governance, Varroa Detector training, protected benchmark work, and statistical inference as follow-on work now that the frame-counting path exists.

This order can change if annotation productivity becomes the limiting factor, or if source-rights/contributor governance becomes necessary before using external evidence.
