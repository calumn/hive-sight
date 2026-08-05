# Vertical Slice 0030: Varroa Corpus Governance

Status: designed; acceptance scenarios pending signoff; renumbered from Slice 0026 after the Varroa-to-Advisor tranche was replanned.

## Purpose

Let a Dataset Curator govern saved Varroa Review Outcomes across the Workspace before any Varroa Detector training begins.

Slice 0025 creates human Varroa evidence one Head-Up Normalized Bee Crop at a time. Slice 0030 turns those reviewed outcomes into a deliberate model-curation corpus decision: include, exclude, or defer. The slice makes active positives and active negatives inspectable as a corpus, keeps unresolved or stale evidence out of model training by default, and preserves provenance back to the same source bee evidence used by Bee Localisation and Bee Orientation.

This is not a Varroa Detector training slice. It does not create a user-facing Varroa Assessment, visible rate, sampling estimate, HiveSight Advisor trigger, or treatment recommendation.

## Source Inputs

- `CONTEXT.md`: Model Governance, Varroa Review, Varroa Review Outcome, Varroa Marker, Varroa Corpus Governance, Varroa Corpus Curation Decision, Model-Curation Sample, Varroa Sampling Plan, Dataset Version, Head-Up Normalized Bee Crop.
- `requirements/model-requirements.md`: MR-002 Varroa Detection, MR-009A Varroa Review Outcome, MR-017 Dataset Roles, MR-017A Dataset Items, MR-017L Dataset Selection Method, MR-018C Separate Varroa Sampling Policies, MR-018D Model-Curation Sampling Method, MR-018E Varroa Review Strength.
- `requirements/varroa-evidence-methodology.md`: Model-Curation Corpus, Reproducibility And Governance, Explicit Non-Claims.
- `architecture/vertical-slice-0025-varroa-review-outcome-labelling.md`: saved single-curator Varroa Review Outcomes and markers.
- `architecture/domain-model.md`: Varroa Review, Varroa Marker, Dataset Item, Dataset Version, Varroa Sampling Plan.
- `architecture/parking-lot.md`: PARK-0013 Varroa Training Source Independence, PARK-0030 Inspection-Rate Sampling Policy, PARK-0052 Varroa Review Invalidation After Source Bee Geometry Changes.
- `requirements/roadmap.md`: Varroa Dataset Repository Browser, Varroa Model-Curation Sampling Plan, Varroa Detector Baseline.

## Signed-Off Acceptance Scenarios

Pending.

```gherkin
Feature: Varroa Corpus Governance

  Scenario: Dataset Curator reviews Varroa corpus evidence across the Workspace
    Given the Workspace has saved Varroa Review Outcomes from Training Data Collection inspections
    When the Dataset Curator opens Varroa Corpus Governance
    Then HiveSight lists Varroa Review Outcomes across the Workspace
    And HiveSight separates visible Varroa, no visible Varroa, not determined, stale, and deferred evidence
    And HiveSight shows the source Training Crop, Bee Annotation, review strength, selection method, and annotation source for each outcome
    And HiveSight labels the evidence as model-curation evidence, not a Varroa Assessment

  Scenario: Dataset Curator includes reviewed positive and negative outcomes in the model-curation corpus
    Given a Varroa Review Outcome is eligible for the first Varroa model-curation corpus
    When the Dataset Curator marks it included
    Then HiveSight records a Varroa Corpus Curation Decision of included
    And HiveSight preserves whether the evidence is visible_varroa_present or no_visible_varroa
    And HiveSight records who made the corpus decision and when
    And HiveSight keeps the original Varroa Review Outcome unchanged

  Scenario: Dataset Curator excludes or defers Varroa outcomes with reasons
    Given a Varroa Review Outcome is visible in Varroa Corpus Governance
    When the Dataset Curator marks it excluded or deferred with a reason
    Then HiveSight records the Varroa Corpus Curation Decision
    And HiveSight shows the reason in the corpus list and summary
    And HiveSight does not count that outcome as included corpus evidence

  Scenario: Not determined outcomes are deferred by default
    Given a Varroa Review Outcome has outcome not_determined
    When the Dataset Curator reviews corpus eligibility
    Then HiveSight marks the outcome as deferred by default
    And HiveSight explains that unresolved Varroa evidence is not positive or negative model-curation evidence
    And HiveSight does not allow it to be included until its Varroa Review Outcome is changed to a determinate outcome

  Scenario: Stale Varroa review evidence cannot be included
    Given a Varroa Review Outcome was saved from an earlier bee-geometry or Head-Up Normalized Bee Crop transform snapshot
    When the current source Training Crop or Bee Annotation no longer matches that saved snapshot
    Then HiveSight marks the Varroa Review Outcome as stale
    And HiveSight prevents it being included in the model-curation corpus
    And HiveSight directs the Dataset Curator to recheck the Varroa Review before inclusion

  Scenario: Corpus summary separates bee-positive count from marker count
    Given the Varroa corpus has included positive and negative curation decisions
    When the Dataset Curator reviews the corpus summary
    Then HiveSight reports included positive bees, included negative bees, deferred outcomes, excluded outcomes, stale outcomes, and total included markers separately
    And HiveSight does not report a Varroa infestation rate, visible Varroa rate, or treatment recommendation
```

## User Path

Given a Dataset Curator has used Varroa Review to save positive, active negative, or unresolved outcomes,
When they open Model Governance and choose Varroa Corpus Governance,
Then HiveSight shows the Workspace-level Varroa evidence pool and lets the curator decide which determinate, current outcomes are included, excluded, or deferred for model-curation use.

## Preconditions

- The selected User has Dataset Curator capability.
- Workspace Data Use Agreement requirements remain enforced.
- Source evidence comes from Training Data Collection inspections only.
- Source Training Crops are completed and not excluded.
- Source Bee Annotations are complete visible bees with reliable Orientation Reliability.
- Saved Varroa Review Outcomes are labelled `model_curation`, `human_selected`, `single_curator_review`, and `human_from_scratch` in this slice.
- A Varroa Review Outcome is eligible for inclusion only when:
  - its outcome is `visible_varroa_present` with one or more markers, or `no_visible_varroa` with zero markers;
  - its saved source context still matches the current Training Crop, Bee Annotation geometry, annotation type, Orientation Reliability, and Head-Up Normalized Bee Crop transform version;
  - source rights and contribution permission snapshots still allow model-development use.
- `not_determined`, stale, withdrawn, rights-invalidated, and source-ineligible outcomes are deferred or excluded by default.

## End-To-End Behaviour

Model Governance gains a `Varroa Corpus Governance` section. It operates across the Workspace, not only the currently selected Training Crop.

The view lists saved Varroa Review Outcomes with compact filters:

- all outcomes;
- eligible determinate outcomes;
- visible Varroa present;
- no visible Varroa;
- not determined;
- stale or source-ineligible;
- included;
- excluded;
- deferred;
- suspected-visible-Varroa cue;
- body occluded or hard to assess cue.

Each row shows:

- Varroa Review Outcome and marker count;
- current corpus curation decision, if any;
- source Training Crop and Bee Annotation identifiers;
- source inspection, hive, and source-image context;
- Varroa Review Suitability and Suspected Visible Varroa Cue;
- Sampling Purpose, Dataset Selection Method, Review Strength, and Annotation Source;
- whether the saved Head-Up Normalized Bee Crop transform still matches the current source evidence;
- any source-rights, contribution-permission, or source-ineligibility warning.

The curator can set one current Varroa Corpus Curation Decision per Varroa Review Outcome:

- `included`: the outcome may contribute to the first Varroa Detection model-curation corpus.
- `excluded`: the outcome should not contribute, with a reason.
- `deferred`: the outcome is not ready yet, with a reason.

The decision is editable as the current curation decision. This slice does not add immutable decision history; audit-event history remains deferred. The original Varroa Review Outcome and Varroa Markers are never rewritten by a corpus decision.

Default treatment:

- `visible_varroa_present` with marker evidence is an eligible positive candidate.
- `no_visible_varroa` is an eligible active negative candidate.
- `not_determined` is deferred by default and cannot be included until the review outcome becomes determinate.
- Outcomes with stale source snapshots are blocked from inclusion until the curator rechecks or updates the Varroa Review.
- Outcomes with `body_occluded_or_hard_to_assess` remain visible with a warning. Positive outcomes may still be included if the curator explicitly chooses; negative outcomes from hard-to-assess bees default to deferred because they are weak negative evidence.

The section includes a corpus summary:

- saved Varroa Review Outcomes;
- eligible positive candidates;
- eligible active negative candidates;
- included positive bees;
- included negative bees;
- included marker count;
- excluded outcomes;
- deferred outcomes;
- stale outcomes;
- unresolved `not_determined` outcomes;
- warning count by reason.

The summary is labelled as model-curation evidence only. It is not a Varroa Assessment, an Inspection-Rate Sample, a Visible Varroa Rate, a Gold-Standard Full-Frame Corpus, or a benchmark-strength claim.

This slice stops before freezing a Varroa Dataset Version. A later Varroa Detector Baseline slice can freeze a Dataset Version or model-specific export from included decisions, preserving the source review and corpus-decision manifest.

## Layers Touched

- Web UI: Add a Varroa Corpus Governance section inside Model Governance with filters, corpus list, curation decision controls, source/provenance labels, warning states, and summary counts.
- Core API: Add endpoints to list Workspace-level Varroa corpus candidates, create/update the current Varroa Corpus Curation Decision, and return corpus summary counts.
- Analysis Service: Not touched.
- Storage: Add durable current Varroa Corpus Curation Decision persistence for in-memory and Postgres-backed paths. Reuse saved Varroa Review Outcome, marker, source-context snapshot, and transform metadata.
- Queue or async boundary: Not touched.
- Contracts: Add response models for Varroa corpus candidates, eligibility/warning reasons, current curation decision, and summary counts.
- Observability: Record lightweight corpus-decision-created and corpus-decision-updated events with workspace id, Varroa Review Outcome id, decision, reason, user id, and eligibility state.

## Test Seams

- Seam: Varroa corpus candidate listing
- Behaviour verified: saved Varroa Review Outcomes appear across the Workspace with outcome, source, provenance, triage cues, eligibility, and warning state.
- Test style: focused Core API tests and API-level BDD.

- Seam: Corpus curation decision persistence
- Behaviour verified: included, excluded, and deferred decisions persist without mutating the original Varroa Review Outcome.
- Test style: focused API tests, Postgres restart-survival guard, and API-level BDD.

- Seam: Inclusion eligibility guard
- Behaviour verified: only determinate current outcomes can be included; `not_determined`, stale, withdrawn, rights-invalidated, or source-ineligible evidence is blocked or deferred with a reason.
- Test style: focused service/API tests and BDD.

- Seam: UI governance workflow
- Behaviour verified: Dataset Curator can review candidates, filter evidence, save include/exclude/defer decisions, see stale/unresolved explanations, and read corpus summary counts.
- Test style: Playwright browser acceptance.

## Data Shape

Minimum new record:

- `VarroaCorpusCurationDecision`
  - `varroa_corpus_curation_decision_id`;
  - `workspace_id`;
  - `varroa_review_outcome_id`;
  - `decision`: `included` | `excluded` | `deferred`;
  - `target_class`: `visible_varroa_present` | `no_visible_varroa` | `not_applicable`;
  - `reason`;
  - `eligibility_snapshot`;
  - `source_context_snapshot`;
  - `created_by_user_id`;
  - `created_at`;
  - `updated_by_user_id`;
  - `updated_at`.

Derived candidate fields:

- `eligibility_state`: `eligible_positive` | `eligible_negative` | `deferred_unresolved` | `stale_source` | `source_ineligible` | `rights_blocked`;
- `warning_reasons`: array of human-readable warning codes;
- `marker_count`;
- `triage_cues`;
- source identifiers and human-readable ids.

## Out Of Scope

- Training a Varroa Detector.
- Creating, freezing, exporting, or naming a Varroa Dataset Version.
- Assigning final Dataset Roles to Varroa evidence beyond the current curation decision.
- Benchmark-strength Blind Independent Review, Third-Party Adjudication, or immutable Varroa review revision history.
- Gold-Standard Full-Frame Corpus construction.
- Probability sampling, inspection-rate estimation, confidence intervals, or Visible Varroa Rate display.
- User-facing Varroa Assessment results, HiveSight Advisor integration, Treatment Recommendations, or Hive Treatment Courses.
- Model-assisted Varroa candidate selection.
- Bulk include/exclude operations.

## Acceptance Criteria

- [ ] Dataset Curators can open Varroa Corpus Governance from Model Governance.
- [ ] The view lists saved Varroa Review Outcomes across the Workspace with outcome, marker count, source, provenance, triage cues, eligibility, and current corpus decision.
- [ ] Dataset Curators can mark eligible determinate outcomes included.
- [ ] Dataset Curators can mark any visible outcome excluded or deferred with a reason.
- [ ] `not_determined` outcomes are deferred by default and cannot be included as positive or negative evidence.
- [ ] Stale source evidence is detected and blocked from inclusion until rechecked.
- [ ] Positive bee counts, negative bee counts, and marker counts are reported separately.
- [ ] The UI and API state that this is model-curation evidence only, not a Varroa Assessment or rate.
- [ ] API-level BDD, focused Core API tests, browser acceptance, Web type-check, Postgres restart-survival guard, and `pnpm verify:slice` pass before implementation closeout.

## Open Questions

- Should Slice 0027 freeze included corpus decisions directly into a Varroa Dataset Version, or first add a named draft corpus object?
- What reason-code list is sufficient for the first exclude/defer workflow without creating too much UI weight?
- Should quality warnings from hard-to-assess negative bees remain a default-defer rule after real annotation evidence exists, or should the curator be allowed to include them more freely?
