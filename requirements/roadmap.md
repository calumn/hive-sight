# HiveSight Roadmap

Date started: 2026-08-03

This roadmap captures potential future vertical slices and work packages. It is not a committed delivery plan. Future candidate work should stay unnumbered until it is promoted into an actual slice document or deliberately scheduled into the delivery order.

Use this document when planning the next slice or a tranche of work. Before promoting an item, review `architecture/parking-lot.md`, the relevant requirements, and recent slice closeout notes so the new slice closes the right loop rather than adding another loose end.

Numbering convention: candidate roadmap rows should normally use descriptive names, not slice numbers. Add a slice number only when the work has a concrete slice artifact or has been explicitly pulled into the next build sequence.

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
- A shared acceptance-catalogue pilot where one client-neutral Gherkin feature runs through both Core API and Web UI bindings.

Important current limitation:

HiveSight can now build, train, and benchmark an early crop-level Bee Localisation candidate, build and evaluate the first Bee Orientation baseline path, label bee-level Varroa Review Outcomes for human model-curation evidence, roll those reviewed outcomes into a current photo-visible Varroa evidence summary, preview deterministic stub Varroa Detector boxes for one eligible Head-Up Normalized Bee Crop, run a transient model-assisted frame mite count across eligible bees on one photographed frame, and assemble Advisor Varroa context for a later HiveSight-to-Advisor treatment-plan request. It cannot yet make a user-facing Varroa assessment, trigger HiveSight Advisor, persist model-only Varroa result history, or produce a statistically defensible photo-visible estimate.

## Immediate Future Candidate Slices

These are the strongest near-term candidates based on the current project state.

| Candidate | Type | Purpose | Why Now |
| --- | --- | --- | --- |
| Benchmark Dataset Curation Browser | Business / Technical | Let a Dataset Curator see and manage protected benchmark evidence as a named asset. | Slice 0015.4 uses benchmark items frozen inside a training Dataset Version; comparing candidates fairly soon needs a reusable benchmark lifecycle. |
| Full-Frame Bee Localisation Evaluation | Technical | Evaluate whether the Bee Localisation candidate can find bees in realistic whole-frame photos, not just reviewed crops. | Crop-level success does not prove the model works on real inspection photos. |
| Varroa Evidence Methodology And Gold-Standard Design | Research / Governance | Establish the full-depth annotation, review, split, sampling-experiment, and field-calibration protocol before Varroa corpus construction begins. | This is documented in `requirements/varroa-evidence-methodology.md`; the protocol prevents training convenience from becoming an unsupported beekeeper-facing statistical claim. |
| Varroa Corpus Governance | Business / Governance | Review saved Varroa Review Outcomes across the Workspace and record include, exclude, or defer decisions before Varroa Detector training datasets are frozen. | This previously designed work returns to an unnumbered candidate until it is deliberately scheduled after the testing pilot. |
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
| Orientation-Assisted Crop Normalisation | Technical | Partly folded into Slice 0025 as the review-preview transform for human Varroa labelling. Automated orientation inference, model-input package export, and live pipeline crop generation remain later work. |

## Varroa Detection

| Candidate Slice | Type | Outcome |
| --- | --- | --- |
| Varroa Corpus Governance | Business / Governance | Show saved Varroa Review Outcomes across the Workspace, separate positive, active negative, unresolved, stale, included, excluded, and deferred evidence, and record current corpus curation decisions without freezing a Dataset Version. |
| Gold-Standard Full-Frame Annotation Pilot | Research / Technical | Demonstrate the methodology on a small, fully reconciled set of complete frame images and measure annotation/review workload and agreement. |
| Varroa Model-Curation Sampling Plan | Business / Technical | Select Varroa labelling tasks using `stratified_random`, `curator_targeted`, and explicit `human_selected` versus `upstream_model_selected` metadata. |
| Varroa Dataset Repository Browser | Business / Technical | Show positive, active negative, and not-determined Varroa evidence by dataset role, source, orientation reliability, and selection method. |
| Varroa Detector Baseline | Technical | Train the first Varroa Detection model on Head-Up Normalized Bee Crops using active positives and active negatives. |
| Varroa Benchmark Report | Technical / Governance | Evaluate Varroa precision, recall, false positives, false negatives, marker agreement, and review-strength caveats. |
| Blind Independent Review For Varroa Benchmark | Business / Governance | Add second-review and adjudication workflow for benchmark Varroa evidence before any user-facing promotion claim. |

## Statistical Inference And Beekeeper Results

| Candidate Slice | Type | Outcome |
| --- | --- | --- |
| Inspection-Rate Sampling Policy | Business / Technical | Define how sampled bees support a stated visible Varroa rate and confidence interval. |
| Sampling-Strategy Simulation And Calibration | Research / Technical | Use protected full-depth frames to select an initial spatial/quality-stratified and possibly sequential inspection-rate plan; separately study paired field-reference measurements without conflating their targets. |
| End-To-End Pipeline Evaluation | Technical / Governance | Evaluate Bee Localisation, Bee Orientation, and Varroa Detection together on protected full-frame evidence. |
| Varroa Coverage And Suppression Rules | Business / Governance | Show coverage warnings and suppress headline estimates when evidence coverage is too weak. |
| First Model-Only Varroa Assessment Result | Business | Produce a clearly caveated, non-promoted inspection result from the staged pipeline. |
| Beekeeper Result Explanation | Business | Explain count, coverage, uncertainty, caveats, and action thresholds in language a beekeeper can act on. |
| Inspection Recovery Review | Business / Governance | Let a Workspace owner review and correct a suppressed or inadequate model-only result without rewriting the original result. |

## Treatment And Advisor Integration

HiveSight remains the system of record for hive identity, Varroa assessment evidence, treatment history, and the Treatment Evidence Chain. HiveSight Advisor may recommend a treatment plan from grounded guidance, but HiveSight owns whether the beekeeper accepts it, records it, applies it, and later judges the result.

| Candidate Slice | Type | Outcome |
| --- | --- | --- |
| Manual Hive Treatment History | Business / Technical | Let a Beekeeper record a Hive Treatment Course and one or more dated Treatment Applications against a selected Hive when the treatment was not Advisor-recommended. Keep this separate from Slice 0029.5 so manual treatment provenance is not blurred with Advisor recommendation provenance. |
| Slice 0029.5 Advisor Treatment Recommendation Intake And Acceptance | Business / Technical | Store blocked, failed, pending, accepted, and declined Advisor treatment advice attempts as explicit Treatment Evidence Chains, then let the Beekeeper accept a pending Treatment Recommendation into a separate planned Hive Treatment Course. |
| Advisor Treatment Plan Contract Readiness | Integration | Closed by HiveSight Advisor Slice 0011: HiveSight sends `jurisdiction_code`, Advisor returns `contract_version = treatment_plan_v1` and `answer_id`, and repeated unresolved requests return the existing pending recommendation. |
| Direction-Specific Advisor Inbound Service Header | Integration | Before building Advisor-to-HiveSight callbacks, use a reverse-direction header such as `X-Advisor-Service-Key` rather than reusing Advisor's `X-HiveSight-Service-Key`. |
| Recommendation Decline And Audit Trail | Business / Governance | Let the Beekeeper decline a Treatment Recommendation with optional notes while preserving the original recommendation and decision history. |
| Advisor Recommendation Callback And Resume Integration | Integration | Notify HiveSight Advisor when a recommendation is accepted, declined, completed, or needs revision once HiveSight's treatment lifecycle is ready to support that cross-system resume workflow. |
| Broader Advisor Context API | Technical / Integration | Extend the Varroa context contract with richer hive, apiary, jurisdiction, inspection-history, and treatment-history context once the first Advisor integration shape has proved useful. |
| Treatment Completion And Follow-up Outcome | Business | Let a Beekeeper mark a Hive Treatment Course complete and relate later Inspection evidence to the treatment outcome without rewriting the original recommendation. |
| Treatment Evidence Chain Retention And Minimisation | Governance | Decide how long raw Advisor context, request, and response snapshots are retained and what minimised form is allowed for audit, deletion, export, or learning governance. |
| Advisor Learning Evidence Export Governance | Governance / Integration | Define if and how anonymised Treatment Evidence Chain records may be exposed to HiveSight Advisor retrieval, evaluation, or learning with permitted-use, minimisation, and provenance controls. |

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
| Capability-Based Acceptance Catalogue Migration | Technical / Quality | Started after Slice 0030: keep active behaviours in `acceptance/features/<capability>/...`, tagged by seam. Varroa review is dual API/Web; Advisor treatment recommendation intake is now API-bound catalogue coverage. Continue capability-by-capability, prioritising current drift risk over historical completeness. |
| Acceptance Catalogue Inventory And Labels | Technical / Quality | Inventory existing API BDD features and browser acceptance specs, then label each behaviour as shared, API-only, browser-only, service-only, legacy historical evidence, or lower-level test coverage. |
| Advisor Integration Shared Acceptance Catalogue | Integration / Quality | Share HiveSight's acceptance-catalogue note with Advisor and align on client-neutral Gherkin conventions for treatment-advice behaviours so both repos can reason from comparable acceptance language. |
| Cross-Inspection Submitted Review Dashboard | Business / Quality | Let Dataset Curators see crops they submitted for review across inspections so waiting work can be chased or cancelled deliberately. |
| Real Model QA Test Environment | Technical / Quality | Keep real YOLO training/evaluation smoke tests outside normal CI but runnable on demand against a QA database. |
| Test Coverage Report Expansion | Technical / Quality | Extend slice verification reports to show unit, API, BDD, UI, real-adapter QA, and known skipped tests in one place. |
| Defect Regression Guard Cleanup | Technical / Quality | Review recent defects and ensure each important fix has the right regression test level. |
| Full SDLC Traceability Audit | Governance / Quality | Periodically check vision, requirements, ADRs, slices, code, tests, user guide, parking lot, and observations for drift. |

## Suggested Planning Order

The likely next tranche should stay model-evidence focused:

1. Use the Slice 0030 acceptance-catalogue pattern for new cross-client behaviours and migrate existing behaviours only when touched or high-risk.
2. Schedule Varroa Corpus Governance when the first Varroa Detector training dataset needs deliberate inclusion, exclusion, or deferral decisions.
3. Build the first Varroa Detector Baseline once there is enough curated positive and active-negative evidence.
4. Add protected Varroa benchmark and gold-standard full-frame work before making any user-facing Varroa Assessment or treatment-trigger claim.
5. Follow with full Hive Treatment History, Treatment Applications, treatment outcomes, and Advisor learning export governance once the first evidence-chain path is stable.

This order can change if annotation productivity becomes the limiting factor, or if source-rights/contributor governance becomes necessary before using external evidence.
