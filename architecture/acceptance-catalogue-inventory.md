# Acceptance Catalogue Inventory

Status: initial inventory created by Slice 0031 on 2026-08-07.

## Purpose

This document is the living map of HiveSight acceptance-style coverage. It separates current capability specifications from historical slice evidence, and records which behaviours should be migrated into the canonical acceptance catalogue when that adds clarity.

The canonical catalogue lives under:

```text
acceptance/features/<capability>/...
```

Canonical features must declare their supported execution seams with feature-level tags:

- `@api`: Core API binding exists or is intended for this feature.
- `@web`: Web UI binding exists or is intended for this feature.

Legacy slice-history tests remain useful evidence. They should not be bulk-migrated just because they exist.

## Classification Labels

- `shared`: the behaviour is product-level and useful through more than one client seam.
- `api-only`: the behaviour is current product or integration behaviour best proven through the Core API.
- `web-only`: the behaviour is current browser/user-interaction behaviour best proven in Playwright.
- `service-only`: the behaviour is best proven below HTTP/UI, usually at a worker or internal service seam.
- `legacy historical evidence`: the test documents a completed slice but is not the living canonical specification.
- `lower-level / do not migrate`: the test protects implementation detail, visual geometry, or harness behaviour that should remain outside Gherkin.

## Migration Recommendations

- `migrate now`: move this behaviour next.
- `migrate when touched`: keep as-is until the capability changes or drift risk rises.
- `keep as legacy evidence`: leave historical slice evidence in place.
- `keep as browser-specific coverage`: keep in Playwright because the assertion is visual, geometric, interaction-heavy, or accessibility-focused.
- `do not migrate`: keep outside acceptance Gherkin.

## Canonical Acceptance Catalogue

| Capability | Behaviour | Current location | Seam | Classification | Migration recommendation | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| varroa | Visible Varroa review outcome | `acceptance/features/varroa/visible-varroa-review-outcome.feature` | API + Web UI | shared | already canonical | Living dual-seam feature from Slice 0030. |
| varroa | Photo-visible Varroa evidence summary | `acceptance/features/varroa/photo-visible-varroa-evidence-summary.feature` | API | api-only | already canonical | Migrated by Slice 0032 because it feeds frame-level count and Advisor context evidence. |
| varroa | Varroa Photo Analysis evidence and adapter readiness | `acceptance/features/varroa/varroa-photo-analysis-evidence-and-adapter-readiness.feature` | API | api-only | already canonical | Added by Slice 0033 for the safe adapter, persisted Photo Analysis, per-bee evidence, and Advisor-eligibility trust boundary. |
| varroa | One-click Varroa Photo Analysis workflow | `acceptance/features/varroa/varroa-photo-analysis-workflow.feature` | API | api-only | already canonical | Slice 0034 product-photo workflow; Web interaction assertions remain browser-specific until a matching Web binding exists. |
| treatment | Advisor treatment recommendation intake | `acceptance/features/treatment/advisor-treatment-recommendation-intake.feature` | API | api-only | already canonical | Living API-bound catalogue feature for the Advisor recommendation intake and treatment evidence chain. |

## Canonical Core API BDD Bindings

| Capability | Behaviour | Current location | Seam | Classification | Migration recommendation | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| varroa | Visible Varroa review outcome | `services/core-api/tests/test_visible_varroa_review_outcome_api_bdd.py` | Core API | shared | already canonical | Core API binding for the canonical Varroa Review Outcome feature. |
| varroa | Photo-visible Varroa evidence summary | `services/core-api/tests/test_photo_visible_varroa_evidence_summary_api_bdd.py` | Core API | api-only | already canonical | Core API binding for the canonical photo-visible Varroa evidence summary feature. |
| varroa | Varroa Photo Analysis evidence and adapter readiness | `services/core-api/tests/test_varroa_photo_analysis_api_bdd.py` | Core API | api-only | already canonical | Core API binding for the canonical Varroa Photo Analysis evidence and adapter readiness feature. |
| varroa | One-click Varroa Photo Analysis workflow | `services/core-api/tests/test_varroa_photo_analysis_workflow_api_bdd.py` | Core API | api-only | already canonical | Core API binding for the Slice 0034 product-photo workflow. |
| treatment | Advisor treatment recommendation intake | `services/core-api/tests/test_advisor_treatment_recommendation_api_bdd.py` | Core API | api-only | already canonical | Core API binding for the canonical treatment recommendation intake feature. |

## Browser BDD Bindings

| Capability | Behaviour | Current location | Seam | Classification | Migration recommendation | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| varroa | Visible Varroa review outcome | `apps/web/tests/bdd/steps/varroa-review-outcome.steps.ts` | Web UI | shared | already canonical | Browser binding for the canonical Varroa feature. |

## Legacy Core API Gherkin Features

| Capability | Behaviour | Current location | Seam | Classification | Migration recommendation | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| analysis | Analysis handoff | `services/core-api/tests/features/vertical_slice_0002_analysis_handoff.feature` | Core API | legacy historical evidence | migrate when touched | Historical slice feature; review current product language before migration. |
| annotation | Annotation evidence review | `services/core-api/tests/features/vertical_slice_0003_annotation_evidence_review.feature` | Core API | legacy historical evidence | migrate when touched | Historical evidence review flow. |
| annotation | Annotation review decision | `services/core-api/tests/features/vertical_slice_0004_annotation_review_decision.feature` | Core API | legacy historical evidence | migrate when touched | Has matching browser acceptance evidence. |
| annotation | AI-assisted bee annotation bootstrap | `services/core-api/tests/features/vertical_slice_0005_ai_assisted_bee_annotation_bootstrap.feature` | Core API | legacy historical evidence | migrate when touched | Has matching browser acceptance evidence. |
| dataset | Dataset role assignment | `services/core-api/tests/features/vertical_slice_0006_dataset_role_assignment.feature` | Core API | legacy historical evidence | migrate when touched | Has matching browser acceptance evidence. |
| model | GroundingDINO pre-labelling adapter | `services/core-api/tests/features/vertical_slice_0007_grounding_dino_pre_labelling_adapter.feature` | Core API | legacy historical evidence | keep as legacy evidence | Superseded in product language by later model/runtime work. |
| inspection | Inspection intent and multi-photo intake | `services/core-api/tests/features/vertical_slice_0008_inspection_intent_and_multi_photo_intake.feature` | Core API | legacy historical evidence | migrate when touched | Candidate if inspection setup changes again. |
| crop | Training Crop ellipse annotation | `services/core-api/tests/features/vertical_slice_0009_training_crop_ellipse_annotation.feature` | Core API | legacy historical evidence | migrate when touched | Candidate if crop annotation semantics change. |
| dataset | Bee Annotation Repository and dataset export | `services/core-api/tests/features/vertical_slice_0010_bee_annotation_repository_and_dataset_export.feature` | Core API | legacy historical evidence | migrate when touched | Dataset governance language has evolved since this slice. |
| dataset | Physical dataset export package | `services/core-api/tests/features/vertical_slice_0011_physical_dataset_export_package.feature` | Core API | legacy historical evidence | migrate when touched | Keep until export package is next changed. |
| hive | Hive configuration and frame standard metadata | `services/core-api/tests/features/vertical_slice_0012_hive_configuration_and_frame_standard_metadata.feature` | Core API | legacy historical evidence | migrate when touched | Candidate when hive setup UX or frame-standard rules change. |
| model | Model candidate crop pre-labelling | `services/core-api/tests/features/vertical_slice_0015_2_model_candidate_crop_pre_labelling.feature` | Core API | legacy historical evidence | migrate when touched | Model governance behaviour; not next priority. |
| model | Model candidate evaluation and benchmark report | `services/core-api/tests/features/vertical_slice_0015_4_model_candidate_evaluation_and_benchmark_report.feature` | Core API | legacy historical evidence | migrate when touched | Model governance behaviour; not next priority. |
| model | YOLO OBB training baseline | `services/core-api/tests/features/vertical_slice_0015_yolo_obb_training_baseline.feature` | Core API | legacy historical evidence | keep as legacy evidence | Replaced by combined bee detector/orientation training language. |
| review | Reviewer work queue | `services/core-api/tests/features/vertical_slice_0019_reviewer_work_queue.feature` | Core API | legacy historical evidence | migrate when touched | Candidate when Review Work changes. |
| model | Bee orientation training baseline | `services/core-api/tests/features/vertical_slice_0022_bee_orientation_training_baseline.feature` | Core API | legacy historical evidence | keep as legacy evidence | Superseded by combined training baseline direction. |
| model | Real bee training baseline | `services/core-api/tests/features/vertical_slice_0023_real_bee_training_baseline.feature` | Core API | legacy historical evidence | migrate when touched | Candidate if combined training workflow changes. |
| model | Bee orientation benchmark evaluation | `services/core-api/tests/features/vertical_slice_0024_bee_orientation_benchmark_evaluation.feature` | Core API | legacy historical evidence | migrate when touched | Model governance behaviour; not next priority. |
| varroa | Varroa review outcome labelling | `services/core-api/tests/features/vertical_slice_0025_varroa_review_outcome_labelling.feature` | Core API | legacy historical evidence | keep as legacy evidence | Current living business outcome moved to canonical Varroa catalogue; remaining details stay historical until touched. |
| varroa | Varroa detector adapter seam | `services/core-api/tests/features/vertical_slice_0027_varroa_detector_adapter_seam.feature` | Core API | api-only | migrate when touched | Adapter seam is current, but lower priority than the evidence summary. |

## Legacy Core API BDD Bindings

| Capability | Behaviour | Current location | Seam | Classification | Migration recommendation | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| analysis | Analysis handoff | `services/core-api/tests/test_vertical_slice_0002_bdd.py` | Core API | legacy historical evidence | migrate when touched | Binding for legacy feature. |
| annotation | Annotation evidence review | `services/core-api/tests/test_vertical_slice_0003_bdd.py` | Core API | legacy historical evidence | migrate when touched | Binding for legacy feature. |
| annotation | Annotation review decision | `services/core-api/tests/test_vertical_slice_0004_bdd.py` | Core API | legacy historical evidence | migrate when touched | Binding for legacy feature. |
| annotation | AI-assisted bee annotation bootstrap | `services/core-api/tests/test_vertical_slice_0005_bdd.py` | Core API | legacy historical evidence | migrate when touched | Binding for legacy feature. |
| dataset | Dataset role assignment | `services/core-api/tests/test_vertical_slice_0006_bdd.py` | Core API | legacy historical evidence | migrate when touched | Binding for legacy feature. |
| model | GroundingDINO pre-labelling adapter | `services/core-api/tests/test_vertical_slice_0007_bdd.py` | Core API | legacy historical evidence | keep as legacy evidence | Binding for superseded historical feature. |
| inspection | Inspection intent and multi-photo intake | `services/core-api/tests/test_vertical_slice_0008_bdd.py` | Core API | legacy historical evidence | migrate when touched | Binding for legacy feature. |
| crop | Training Crop ellipse annotation | `services/core-api/tests/test_vertical_slice_0009_bdd.py` | Core API | legacy historical evidence | migrate when touched | Binding for legacy feature. |
| dataset | Bee Annotation Repository and dataset export | `services/core-api/tests/test_vertical_slice_0010_bdd.py` | Core API | legacy historical evidence | migrate when touched | Binding for legacy feature. |
| dataset | Physical dataset export package | `services/core-api/tests/test_vertical_slice_0011_bdd.py` | Core API | legacy historical evidence | migrate when touched | Binding for legacy feature. |
| hive | Hive configuration and frame standard metadata | `services/core-api/tests/test_vertical_slice_0012_bdd.py` | Core API | legacy historical evidence | migrate when touched | Binding for legacy feature. |
| model | YOLO OBB training baseline | `services/core-api/tests/test_vertical_slice_0015_bdd.py` | Core API | legacy historical evidence | keep as legacy evidence | Binding for superseded historical feature. |
| model | Model candidate crop pre-labelling | `services/core-api/tests/test_vertical_slice_0015_2_bdd.py` | Core API | legacy historical evidence | migrate when touched | Binding for legacy feature. |
| model | Model candidate evaluation and benchmark report | `services/core-api/tests/test_vertical_slice_0015_4_bdd.py` | Core API | legacy historical evidence | migrate when touched | Binding for legacy feature. |
| review | Reviewer work queue | `services/core-api/tests/test_vertical_slice_0019_bdd.py` | Core API | legacy historical evidence | migrate when touched | Binding for legacy feature. |
| model | Bee orientation training baseline | `services/core-api/tests/test_vertical_slice_0022_bdd.py` | Core API | legacy historical evidence | keep as legacy evidence | Binding for superseded historical feature. |
| model | Real bee training baseline | `services/core-api/tests/test_vertical_slice_0023_bdd.py` | Core API | legacy historical evidence | migrate when touched | Binding for legacy feature. |
| model | Bee orientation benchmark evaluation | `services/core-api/tests/test_vertical_slice_0024_bdd.py` | Core API | legacy historical evidence | migrate when touched | Binding for legacy feature. |
| varroa | Varroa review outcome labelling | `services/core-api/tests/test_vertical_slice_0025_bdd.py` | Core API | legacy historical evidence | keep as legacy evidence | Current living business outcome moved to canonical Varroa catalogue. |
| varroa | Varroa detector adapter seam | `services/core-api/tests/test_vertical_slice_0027_bdd.py` | Core API | api-only | migrate when touched | Binding for legacy feature. |

## Plain Browser Acceptance Specs

| Capability | Behaviour | Current location | Seam | Classification | Migration recommendation | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| annotation | Annotation review decision | `apps/web/tests/acceptance/slice-0004-annotation-review-decision.spec.ts` | Web UI | web-only | keep as browser-specific coverage | Browser workflow/interaction evidence. |
| annotation | AI-assisted bee annotation bootstrap | `apps/web/tests/acceptance/slice-0005-ai-assisted-bee-annotation-bootstrap.spec.ts` | Web UI | web-only | keep as browser-specific coverage | Browser workflow/interaction evidence. |
| dataset | Dataset role assignment | `apps/web/tests/acceptance/slice-0006-dataset-role-assignment.spec.ts` | Web UI | web-only | keep as browser-specific coverage | Browser workflow/interaction evidence. |
| model | Pre-labeller provenance | `apps/web/tests/acceptance/slice-0007-prelabeller-provenance.spec.ts` | Web UI | web-only | keep as browser-specific coverage | Browser workflow/interaction evidence. |
| inspection | Inspection intent and multi-photo intake | `apps/web/tests/acceptance/slice-0008-inspection-intent-and-multi-photo-intake.spec.ts` | Web UI | web-only | keep as browser-specific coverage | Browser workflow/interaction evidence. |
| crop | Training Crop ellipse annotation | `apps/web/tests/acceptance/slice-0009-training-crop-ellipse-annotation.spec.ts` | Web UI | web-only | keep as browser-specific coverage | Visual and geometric annotation behaviour. |
| dataset | Bee Annotation Repository and dataset export | `apps/web/tests/acceptance/slice-0010-bee-annotation-repository-and-dataset-export.spec.ts` | Web UI | web-only | keep as browser-specific coverage | Browser workflow/interaction evidence. |
| dataset | Physical dataset export package | `apps/web/tests/acceptance/slice-0011-physical-dataset-export-package.spec.ts` | Web UI | web-only | keep as browser-specific coverage | Browser workflow/interaction evidence. |
| hive | Hive configuration and frame standard metadata | `apps/web/tests/acceptance/slice-0012-hive-configuration-and-frame-standard-metadata.spec.ts` | Web UI | web-only | keep as browser-specific coverage | Browser workflow/interaction evidence. |
| model | YOLO OBB training baseline | `apps/web/tests/acceptance/slice-0015-yolo-obb-training-baseline.spec.ts` | Web UI | web-only | keep as browser-specific coverage | Historical model workflow UI evidence. |
| model | Model candidate crop pre-labelling | `apps/web/tests/acceptance/slice-0015-2-model-candidate-crop-prelabelling.spec.ts` | Web UI | web-only | keep as browser-specific coverage | Browser workflow/interaction evidence. |
| dataset | Bee Annotation Repository | `apps/web/tests/acceptance/slice-0015-3-bee-annotation-repository.spec.ts` | Web UI | web-only | keep as browser-specific coverage | Browser workflow/interaction evidence. |
| model | Model candidate evaluation | `apps/web/tests/acceptance/slice-0015-4-model-candidate-evaluation.spec.ts` | Web UI | web-only | keep as browser-specific coverage | Browser workflow/interaction evidence. |
| workspace | Workspace resume and apiary/hive selection | `apps/web/tests/acceptance/slice-0016-workspace-resume-and-apiary-hive-selection.spec.ts` | Web UI | web-only | keep as browser-specific coverage | Browser workflow/interaction evidence. |
| inspection | Resume training inspections and crops | `apps/web/tests/acceptance/slice-0017-resume-training-inspections-and-crops.spec.ts` | Web UI | web-only | keep as browser-specific coverage | Browser workflow/interaction evidence. |
| workspace | Dev user switching | `apps/web/tests/acceptance/slice-0018-dev-user-switching.spec.ts` | Web UI | web-only | keep as browser-specific coverage | Browser workflow/interaction evidence. |
| review | Reviewer work queue | `apps/web/tests/acceptance/slice-0019-reviewer-work-queue.spec.ts` | Web UI | web-only | keep as browser-specific coverage | Browser workflow/interaction evidence. |
| inspection | Training inspection workflow separation | `apps/web/tests/acceptance/slice-0020-training-inspection-workflow-separation.spec.ts` | Web UI | web-only | keep as browser-specific coverage | Browser workflow/interaction evidence. |
| model | Bee orientation training baseline | `apps/web/tests/acceptance/slice-0022-bee-orientation-training-baseline.spec.ts` | Web UI | web-only | keep as browser-specific coverage | Historical model workflow UI evidence. |
| model | Bee orientation benchmark evaluation | `apps/web/tests/acceptance/slice-0024-bee-orientation-benchmark-evaluation.spec.ts` | Web UI | web-only | keep as browser-specific coverage | Browser workflow/interaction evidence. |
| varroa | Varroa review outcome labelling | `apps/web/tests/acceptance/slice-0025-varroa-review-outcome-labelling.spec.ts` | Web UI | web-only | keep as browser-specific coverage | Retains visual, zoom, source-context, overlay, and marker-containment checks outside the shared Gherkin business outcome. |

## Harness And Reporting Guards

| Capability | Behaviour | Current location | Seam | Classification | Migration recommendation | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| testing | Core API catalogue seam filtering | `services/core-api/tests/conftest.py` | Core API | lower-level / do not migrate | do not migrate | Ensures Core API does not execute canonical scenarios without `@api`. |
| testing | Acceptance catalogue seam-tag guard | `services/core-api/tests/test_acceptance_catalogue_seam_tags.py` | Core API | lower-level / do not migrate | do not migrate | Unit-level guard for seam filtering. |
| testing | Acceptance catalogue inventory and label guard | `services/core-api/tests/test_acceptance_catalogue_inventory.py` | Core API | lower-level / do not migrate | do not migrate | Ensures canonical feature labels and inventory path coverage remain aligned. |
| testing | Slice verification report | `scripts/verify-slice.mjs` | repository | lower-level / do not migrate | do not migrate | Generates BDD Feature Area Summary and full slice verification report. |

## Next Recommended Migration Candidate

No immediate next migration candidate is promoted.

Reason:

- Slice 0033 migrated the touched Varroa detector/photo-analysis behaviour into the canonical catalogue.
- Remaining legacy Core API Gherkin should continue to migrate when touched or when drift risk becomes high.
- Browser-only visual, geometry, zoom, and marker-containment behaviours should remain in browser acceptance coverage unless a future shared behaviour needs them.
