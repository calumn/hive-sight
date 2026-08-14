# Vertical Slice 0035: Product Photo Analysis Confidence Policy

Status: promoted, grilled, and designed; acceptance scenarios drafted for sign-off before implementation.

## Purpose

Make HiveSight's product Photo Analysis confidence rules explicit before replacing deterministic development adapters with real model adapters or using accepted Photo Analysis evidence in a later Advisor workflow.

Slice 0034 lets a Workspace member run `Analyze photo`, inspect model-assisted evidence, and mark a Varroa Photo Analysis `accepted`. That proves the workflow, but it does not yet distinguish development-only evidence from real product evidence, or explain how low-confidence Bee Localisation, Bee Orientation, and Varroa Detection results affect the run.

This slice adds a persisted, versioned confidence-policy outcome to each Varroa Photo Analysis and replaces the current boolean Advisor eligibility hook with one explicit eligibility enum. It tells the Workspace member why a result is development integration evidence, product-candidate evidence, or ineligible for later Advisor evidence. It does not create a Visible Varroa Rate, treatment trigger, diagnosis, Advisor request workflow, or production model promotion claim.

## Source Inputs

- `CONTEXT.md`: Varroa Photo Analysis, Inspection Photo Bee Evidence, Likely Varroa Detection, Not Assessed For Varroa, Visible Varroa Rate.
- `requirements/product-spec.md`: Varroa image analysis, tagged photo review, coverage-gated visible Varroa result language.
- `requirements/model-requirements.md`: end-to-end pipeline evaluation, orientation coverage, unreliable-orientation rate, confidence buckets, coverage warnings, suppression before a headline estimate.
- `requirements/varroa-evidence-methodology.md`: incomplete and orientation-unreliable evidence must remain explicit coverage limits rather than becoming negatives.
- `architecture/vertical-slice-0034-one-click-varroa-photo-analysis-workflow.md`: delivered product Photo Analysis workflow, deterministic development adapter, partial result caveats, and Advisor eligibility hook.
- `architecture/current-system-architecture.md`: delivered Varroa Photo Analysis path is deterministic development model evidence, not a production Varroa model or Advisor trigger.
- `architecture/parking-lot.md`: PARK-0057 Product Photo Analysis Confidence Policy.
- `requirements/roadmap.md`: Product Photo Analysis Confidence Policy immediate future candidate.

## Draft Acceptance Scenarios

These scenarios need explicit acceptance-scenario sign-off before implementation.

```gherkin
@api
Feature: Product Photo Analysis confidence policy

  Scenario: Accepted deterministic Photo Analysis is development-integration evidence only
    Given a Varroa Assessment Photo Analysis was produced by the deterministic development adapter
    When a Workspace member views the Photo Analysis confidence policy
    Then HiveSight labels the run as development model evidence only
    And HiveSight reports the Advisor evidence eligibility as ineligible
    When the Workspace member marks the Photo Analysis accepted
    Then HiveSight reports the Advisor evidence eligibility as development integration only
    And HiveSight does not label the run as product-candidate evidence

  Scenario: A complete non-stub Photo Analysis can become product-candidate evidence after review
    Given a Varroa Assessment Photo Analysis was produced by a replaceable non-stub adapter
    And every localised complete bee has usable orientation and Varroa Detector evidence
    And the Varroa Detector evidence satisfies product photo confidence policy version "product_photo_confidence_policy_v1"
    When a Workspace member views the Photo Analysis confidence policy
    Then HiveSight records the confidence policy status as advisor candidate possible
    And HiveSight reports that accepted review is required before later Advisor use
    When the Workspace member marks the Photo Analysis accepted
    Then HiveSight reports the Advisor evidence eligibility as product candidate

  Scenario: Low-confidence-only Varroa evidence blocks Advisor eligibility without hiding markers
    Given a Varroa Assessment Photo Analysis includes a bee with only Varroa detections below the policy confidence floor
    When HiveSight applies the Product Photo Analysis Confidence Policy
    Then HiveSight keeps the detection visible in the evidence detail
    And HiveSight reports a confidence warning for Varroa Detection
    And HiveSight reports the Advisor evidence eligibility as ineligible

  Scenario: Zero likely Varroa detections can be product-candidate evidence
    Given a completed non-stub Varroa Assessment Photo Analysis has zero likely Varroa detections
    And every eligible complete bee has a completed detector call with acceptable provenance
    When a Workspace member marks the Photo Analysis accepted
    Then HiveSight reports the Advisor evidence eligibility as product candidate
    And HiveSight does not state that no Varroa is present in the hive

  Scenario: Incomplete bee processing remains explicit coverage limitation
    Given a Varroa Assessment Photo Analysis has eligible complete bees that were not assessed for Varroa
    When HiveSight applies the Product Photo Analysis Confidence Policy
    Then HiveSight reports the unassessed bee count as a coverage limitation
    And HiveSight does not treat unassessed bees as no-visible-Varroa evidence
    And HiveSight reports the Advisor evidence eligibility as ineligible
```

## User Path

Given a Workspace member has a completed, partial, or no-usable-bees Varroa Photo Analysis,
when they review the result,
then HiveSight shows a confidence-policy summary that explains whether the run is development integration evidence, product-candidate evidence, or blocked from later Advisor evidence, and why.

## Preconditions

- The actor has access to the Workspace.
- The Workspace Data Use Agreement is accepted.
- The Inspection intent is `varroa_assessment`.
- Slice 0034 Varroa Photo Analysis exists for at least one Inspection Photo.
- The confidence policy is versioned and persisted so a future policy change does not silently change historical Photo Analysis outcomes.
- This slice changes only internal Web/Core API contracts; it does not change any declared HiveSight Advisor contract.

## End-To-End Behaviour

Add a Product Photo Analysis Confidence Policy evaluator to the Core API product Photo Analysis workflow.

The policy evaluates one Varroa Photo Analysis run after model evidence has been produced. It persists:

- policy version, initially `product_photo_confidence_policy_v1`;
- frozen confidence policy status;
- per-stage policy outcomes for Bee Localisation, Bee Orientation, and Varroa Detection;
- coverage counts for eligible, analysed, failed, and unassessed complete bees;
- structured caveat codes and human-readable caveats.

The current Advisor evidence eligibility is derived from frozen policy status plus current review status. It replaces the Slice 0034 boolean `advisor_evidence_eligible`.

Initial policy statuses:

- `development_evidence_only`: the run used deterministic development/stub evidence. The result remains useful for local workflow QA and integration testing.
- `advisor_candidate_possible`: the run used a replaceable non-stub adapter, every eligible complete bee reached Varroa Detection, and configured confidence rules were satisfied. It can become product-candidate Advisor evidence only after accepted review.
- `blocked_by_confidence_policy`: one or more model-stage confidence rules failed. Evidence remains visible, but the run is not later Advisor-ready.
- `blocked_by_coverage_policy`: one or more eligible complete bees were not assessed for Varroa. Evidence remains visible, but the run is not later Advisor-ready.
- `not_assessable`: the run failed before producing a meaningful policy judgement.

Current Advisor evidence eligibility values:

- `ineligible`: the run cannot be used as Advisor evidence in its current state.
- `development_integration_only`: the run can exercise HiveSight to HiveSight Advisor integration paths in development or QA, but is not product-candidate evidence.
- `product_candidate`: the run may be used as product Advisor evidence by a future Advisor request workflow.

Current eligibility rules for Slice 0035:

- If `review_status` is not `accepted`, current eligibility is `ineligible`.
- If `review_status` is `accepted`, `run.status` is `completed`, and frozen policy status is `development_evidence_only`, current eligibility is `development_integration_only`.
- If `review_status` is `accepted`, `run.status` is `completed`, and frozen policy status is `advisor_candidate_possible`, current eligibility is `product_candidate`.
- Partial, failed, and coverage-blocked runs remain `ineligible`, even when review status is `accepted`.
- A future Advisor request workflow may decide which eligibility values it accepts for which operation, but Slice 0035 only exposes the status and does not implement the Advisor request gate.

Initial stage rules:

- Bee Localisation: deterministic product candidate geometries are development-only. A future non-stub localisation result must record enough provenance and confidence/category evidence for policy evaluation; if not, the run is blocked by confidence policy.
- Bee Orientation: usable orientation is required for each eligible complete bee before Varroa Detection. Slice 0035 does not set a numeric orientation confidence floor; an absent or unusable orientation is a coverage block.
- Varroa Detection: policy version `product_photo_confidence_policy_v1` uses a hard-coded Varroa Detection confidence floor of `0.75`. This is a development policy constant, not a production-validated threshold.
- A bee with at least one Varroa Detection at or above the floor may count as a bee with likely visible Varroa even if another marker on that bee is below the floor.
- A bee with only low-confidence Varroa detections blocks the whole run with `blocked_by_confidence_policy`; weak positive evidence must not be silently converted into negative evidence.
- Zero detections is valid only when every eligible complete bee has a completed detector call with non-stub provenance, no detector failures, and no coverage block. This is useful Advisor context, but the UI must not state that no Varroa is present in the hive.
- `no_usable_bees` maps to `blocked_by_coverage_policy` with a structured caveat such as `no_usable_bees`, because the run is not inherently failed but offers no assessable bee evidence.
- Partial runs map to `blocked_by_coverage_policy` with a structured caveat such as `unassessed_complete_bees_present`.

The UI shows the confidence-policy summary near the Photo Analysis result and review controls. It should use plain product language such as:

- `Development evidence only`
- `Development integration evidence`
- `Eligible for Advisor evidence`
- `Blocked by confidence policy`
- `Blocked by incomplete coverage`
- `Not assessable`

The UI should show the full human-readable caveat list by default in Slice 0035. HiveSight is still in development and QA mode, so exposing why the policy made its decision is more valuable than hiding details behind an expander.

The UI may mention Advisor evidence eligibility before an Advisor button exists, because this is development/QA state language. It must not show any button or action that implies HiveSight Advisor has been called.

The review status remains separate from the confidence policy. A Workspace member can still mark a result accepted, rejected, inconclusive, or needs expert review according to Slice 0034 review rules. A confidence-policy block does not prohibit `accepted`; it only keeps current Advisor evidence eligibility `ineligible`.

The policy outcome is frozen when the Photo Analysis is produced. It must not silently change when the analysis is read later. A future policy re-evaluation or reanalysis workflow must be explicit.

This deliberately replaces Slice 0034's backend boolean eligibility hook: accepted deterministic development evidence is accepted-for-review and can be used for development integration, but is not product-candidate evidence.

## Layers Touched

- Web UI: show confidence-policy status and the full human-readable caveat list in the Photo Analysis result panel; keep evidence detail visible even when blocked.
- Core API: add persisted policy outcome fields, replace the boolean Advisor eligibility field with an enum, add a policy evaluator, update review-derived eligibility, and add focused tests around policy outcomes.
- Analysis Service: not touched.
- Storage: persist frozen policy outcome and supporting caveat/status fields; add a migration and live Postgres verification for closeout.
- Queue or async boundary: not touched beyond applying policy after Photo Analysis processing and after review updates.
- Contracts: internal Web/Core API response shape extends `VarroaPhotoAnalysisRunResponse`; no HiveSight Advisor contract change.
- Observability: expose structured policy status and caveat codes in responses; add logs only if the implementation already has a suitable local pattern.

## Test Seams

- Seam: confidence policy evaluator
- Behaviour verified: deterministic development runs can become development-integration-only after accepted review; complete non-stub runs can become product-candidate after accepted review; low-confidence-only detector evidence and incomplete coverage block Advisor eligibility.
- Test style: focused Core API workflow tests with deterministic/fake adapters.

- Seam: Photo Analysis review eligibility
- Behaviour verified: `accepted` review changes current eligibility only according to the frozen confidence-policy status and completed-run rules.
- Test style: Core API regression test updating existing Slice 0034 review coverage.

- Seam: acceptance catalogue
- Behaviour verified: product-level policy outcomes are documented in `acceptance/features/varroa/...` and bound through the Core API.
- Test style: API-level BDD.

- Seam: Web result summary
- Behaviour verified: Workspace member sees development integration, product-candidate, confidence-blocked, and coverage-blocked summaries and full caveats without losing access to the underlying evidence.
- Test style: focused Playwright browser acceptance or extension of the existing Varroa Assessment browser spec.

## Data Shape

Extend `VarroaPhotoAnalysisRunResponse` with:

- `confidence_policy_version`
- `confidence_policy_status`
- `advisor_evidence_eligibility`
- `confidence_policy_caveats`
- `bee_localisation_policy_status`
- `bee_orientation_policy_status`
- `varroa_detection_policy_status`
- `unassessed_complete_bees`
- `low_confidence_detection_count`

Confidence policy status values:

- `development_evidence_only`
- `advisor_candidate_possible`
- `blocked_by_confidence_policy`
- `blocked_by_coverage_policy`
- `not_assessable`

Advisor evidence eligibility values:

- `ineligible`
- `development_integration_only`
- `product_candidate`

Policy constants:

- `product_photo_confidence_policy_v1.varroa_detection_confidence_floor = 0.75`

This value is hard-coded in policy version `product_photo_confidence_policy_v1`. It is not configurable in Slice 0035 and is not a production-validated threshold.

## Out Of Scope

- Choosing production confidence thresholds from real benchmark data.
- Configurable confidence thresholds.
- Numeric Bee Localisation or Bee Orientation confidence floors.
- Per-bee confidence-policy fields or per-bee policy status UI.
- Promoting a real Bee Localisation, Bee Orientation, or Varroa Detection model.
- Creating a Visible Varroa Rate, confidence interval, sampling estimator, diagnosis, treatment threshold, or Advisor trigger.
- Implementing the future Advisor request gate or choosing which Advisor operations may consume `development_integration_only`.
- Reanalysis of historical photos under a newer policy or model.
- Per-bee correction, expert review, or recovery workflow.
- Reusing accepted product evidence for model training or calibration.
- Changing HiveSight Advisor request or callback contracts.

## Acceptance Criteria

- [ ] Product Photo Analysis responses include a versioned confidence-policy summary.
- [ ] Frozen policy outcome is persisted and does not silently change on later reads.
- [ ] `advisor_evidence_eligible` boolean is removed/replaced by `advisor_evidence_eligibility`.
- [ ] Deterministic development adapter runs become `development_integration_only` only when completed and accepted, and never become `product_candidate`.
- [ ] Complete non-stub runs with confidence-policy status `advisor_candidate_possible` become `product_candidate` only after accepted review.
- [ ] Partial runs, failed runs, no-usable-bees runs, coverage-blocked runs, and confidence-blocked runs remain `ineligible`, even when accepted.
- [ ] A completed accepted non-stub run with zero likely Varroa detections can be `product_candidate` when every eligible complete bee has completed detector evidence with acceptable provenance.
- [ ] Low-confidence-only Varroa evidence remains visible but blocks current Advisor evidence eligibility.
- [ ] Unassessed eligible complete bees and no-usable-bees outcomes remain explicit coverage limitations and are not treated as negative evidence.
- [ ] Web UI shows human-readable policy status and all human-readable caveats next to the Photo Analysis result and review controls.
- [ ] API-level BDD and focused Core API tests cover the policy outcomes.
- [ ] Browser acceptance covers the confidence-policy summary for at least the default deterministic development run.
- [ ] `pnpm verify:slice` passes before implementation closeout.
- [ ] Live Postgres migration verification is completed or explicitly recorded pending.

## Open Questions

- Should the first non-stub fake adapter path be added in this slice solely to prove the `product_candidate` branch, or should that branch be API-only with a test double until a real model adapter is ready?
