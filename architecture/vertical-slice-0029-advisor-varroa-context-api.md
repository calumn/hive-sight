# Vertical Slice 0029: Advisor Varroa Context API

Status: designed; grilling decisions incorporated; acceptance scenarios formally accepted on 2026-08-06.

## Purpose

Expose the minimum HiveSight-owned Varroa context that HiveSight Advisor needs to decide whether treatment guidance can be requested, without moving treatment advice, treatment acceptance, or treatment history lifecycle into this slice.

This slice turns the transient Slice 0028 Frame Mite Count into a narrowly scoped integration contract. It proves that HiveSight can assemble hive identity, inspection-photo evidence, model-assisted frame mite count evidence, caveats, and current treatment-history availability into one machine-readable context response.

This is not a HiveSight Advisor call, Treatment Recommendation, Hive Treatment Course, visible Varroa rate, statistical confidence estimate, user-facing Varroa Assessment, or durable frame-count history.

## Grilling Decisions

- Slice 0029 is context API only. It does not add a HiveSight-side outbound caller for HiveSight Advisor's treatment-plan endpoint.
- `jurisdiction_id` is optional in the context request. Missing jurisdiction does not prevent `status = available`, but it blocks `advisor_request_readiness.can_request_advice`.
- `completed_with_warnings` Frame Mite Count evidence may be included in available context with explicit warning and caveat detail.
- In Slice 0029, `advisor_request_readiness.can_request_advice` remains `false` because treatment history is not modelled yet and Training Data Collection evidence is not a user-facing Varroa Assessment.
- Training Data Collection evidence is acceptable for integration-context testing, but it is labelled as model-curation or integration-test evidence and blocks actual advice readiness.
- HiveSight uses `X-HiveSight-Service-Key` as the integration header name for symmetry with HiveSight Advisor. HiveSight's expected value is its own configured Advisor integration secret.
- A valid request with no processable evidence returns HTTP `200` with `status = not_available`. Invalid identity, auth, or entity relationships use HTTP errors.
- The context includes both model-assisted `frame_mite_count` evidence and human-reviewed `photo_visible_varroa_evidence`, kept as separate sections.
- Advisor receives aggregate frame evidence only. Per-bee detector results, detection boxes, image URLs, Head-Up transform metadata, and Bee Annotation ids stay inside HiveSight.
- The response includes `workspace_id`, `apiary_id`, `hive_id`, `inspection_id`, and `inspection_photo_id` as opaque HiveSight provenance ids, but no User or membership details.
- Slice 0029 is API-only. It adds no visible HiveSight UI.
- No Treatment History domain model is introduced. The response uses `treatment_history.status = not_modelled` and `recent_treatment_count = null` so Advisor does not mistake absence of modelling for no recent treatment.
- Caveats are machine/provenance-oriented constraints, not polished beekeeper-facing advice copy.
- The shared `hivesight-advisor-integration-contract` skill is not updated until Slice 0029 is implemented and verified. This design can be shared with the Advisor side for agreement first.
- The response uses `advisor_request_readiness`, not `advisor_suitability`.
- Endpoint path is `POST /v1/integrations/hivesight-advisor/varroa-context`.
- The response includes `contract_version = advisor_varroa_context_v1`.
- The request does not include `workspace_id`; HiveSight derives Workspace from the requested Hive.
- Valid-but-`not_available` responses still include HiveSight identity/provenance fields.
- The main evidence wrapper is `varroa_evidence`, with separate `frame_mite_count` and `photo_visible_varroa_evidence` children.
- The slice doc includes an example request/response payload for HiveSight Advisor review.
- Example evidence uses realistic-looking counts but explicitly marks them as deterministic/stub/model-curation evidence.
- No Slice 0029-specific browser acceptance is required because the slice is service-to-service API only.
- Local tests use an explicit configured dev/test service key and still exercise the service-auth dependency.
- The Advisor service key belongs in Core API settings.

## Source Inputs

- `CONTEXT.md`: Frame Mite Count, Frame-Level Varroa Result Summary, Treatment Recommendation, Hive Treatment Course, Treatment Application, Treatment Outcome.
- `requirements/roadmap.md`: Slice 0029 Advisor Varroa Context API; Treatment And Advisor Integration tranche.
- `architecture/domain-model.md`: Frame Mite Count and its non-claims around Advisor, treatment, rate, and whole-colony measurement.
- `architecture/vertical-slice-0026-frame-level-varroa-result-summary.md`: human-reviewed photo-visible evidence summary and Advisor-context availability caveats.
- `architecture/vertical-slice-0028-frame-mite-counting-workflow.md`: model-assisted frame mite count shape and transient result rules.
- `hivesight-advisor-integration-contract` skill: Advisor already exposes `POST /integrations/hivesight/treatment-plans` with `{hive_id, jurisdiction_id, situational_context}`; HiveSight has not yet built a real caller or recommendation intake.
- `architecture/parking-lot.md`: revisit any parked treatment-history, sampling, and Advisor integration follow-ons.

## User Path

Given a service-authenticated HiveSight Advisor integration client has a HiveSight Hive id and a selected Inspection Photo id,
When it requests Varroa context for that photo,
Then HiveSight returns the current Advisor-ready Varroa context if eligible frame evidence can be counted, including hive, apiary, inspection, frame-count, caveat, and treatment-history availability fields.

## Preconditions

- The integration request uses HiveSight's dedicated Advisor service credential in `X-HiveSight-Service-Key`, not the development user header and not beekeeper UI auth.
- The requested Hive exists in HiveSight.
- The requested Inspection Photo belongs to an Inspection for the same Hive.
- The Inspection has intent `training_data_collection` for this first slice, because the evidence source is still the model-curation training workflow.
- The selected Inspection Photo may or may not have processable Slice 0028 Frame Mite Count evidence. The endpoint returns `available` or `not_available` as a domain answer.
- No durable Hive Treatment History exists yet unless a prior slice adds it before implementation. Slice 0029 must make that absence explicit in the context payload.

## End-To-End Behaviour

HiveSight adds a dedicated integration endpoint for Advisor context:

- route prefix is scoped to Advisor integration only;
- service auth is checked by a dedicated dependency;
- no normal Core API user routes accept the service credential;
- no development user capability is required for the service endpoint, and development user auth alone is rejected;
- request references a Hive and selected Inspection Photo;
- HiveSight verifies the photo belongs to an Inspection for that Hive;
- HiveSight runs or reuses the same logic as Slice 0028 to build a current model-assisted Frame Mite Count;
- HiveSight returns an Advisor context response with contract version, availability, evidence, request-readiness, treatment-history modelling status, and caveats;
- HiveSight does not call HiveSight Advisor in this slice.

The endpoint returns `available` when at least one eligible bee was processed by the frame-count workflow. `completed_with_warnings` frame-count evidence can still be available, but the warnings and coverage must be included. If no eligible bee can be processed, the endpoint returns HTTP `200` with a domain `not_available` response rather than a transport error.

`available` means HiveSight has evidence context. It does not mean treatment advice can be requested. In Slice 0029, `advisor_request_readiness.can_request_advice` is normally `false` because:

- `jurisdiction_id` may be missing;
- source evidence is Training Data Collection evidence, not a beekeeper-facing Varroa Assessment;
- Hive Treatment History is not modelled.

The context is intentionally evidence-shaped, not advice-shaped. It can say:

- what Hive, Apiary, Inspection, and Inspection Photo the evidence belongs to;
- how many eligible bees were counted;
- how many processed bees had likely visible Varroa;
- how many likely visible Varroa detections were found;
- what coverage and warning status applies;
- what human-reviewed and model-assisted evidence sources apply;
- what model provenance applies;
- that the count is over bee annotations, not deduplicated physical bees;
- that treatment history is `not_modelled` if Hive Treatment History has not been implemented.

The context must not say:

- treatment needed;
- treatment not needed;
- high, medium, low, safe, dangerous, or threshold crossed;
- official infestation rate;
- whole-colony mite rate;
- Advisor recommendation accepted or pending.
- human-readable treatment caveats for Advisor to quote back to the beekeeper.

## Layers Touched

- Web UI: Not touched in the core slice. A later slice may add a button from the frame mite count card to request Advisor advice.
- Core API: Add Advisor context request/response models, integration auth setting/dependency, and a service-scoped endpoint that builds context from Hive, Inspection Photo, Frame Mite Count evidence, and Photo-visible Varroa evidence.
- Analysis Service: Not touched.
- Storage: No new durable table in the base slice. Treatment history is represented as `not_modelled` unless a prior slice creates durable treatment records.
- Queue or async boundary: Not touched; context building is synchronous and uses the current deterministic/stub detector path.
- Contracts: Add a HiveSight-side Advisor Varroa Context API contract. Do not update the shared HiveSight Advisor integration contract until implementation has passed.
- Observability: Log one Advisor-context request with route, hive id, inspection photo id, availability, frame-count status, processed bee count, detection count, and no treatment-advice flag.

## Test Seams

- Seam: Advisor service-auth gate
- Behaviour verified: the Advisor context endpoint accepts only the dedicated service credential and does not accept ordinary dev-user auth as a substitute.
- Test style: Core API route tests.

- Seam: Hive/photo ownership validation
- Behaviour verified: HiveSight rejects context requests when the Inspection Photo does not belong to the requested Hive.
- Test style: Core API tests.

- Seam: Frame-count context builder
- Behaviour verified: an available context includes the selected Hive, Apiary, Inspection, Inspection Photo, model-assisted frame mite count aggregates, human-reviewed photo-visible evidence, coverage, provenance, caveats, and no-advice flags.
- Test style: focused Core API/service tests.

- Seam: Not-available context
- Behaviour verified: no processable frame evidence returns a domain `not_available` payload with reasons, not a treatment recommendation or HTTP-level failure.
- Test style: focused Core API tests.

- Seam: Treatment-history absence
- Behaviour verified: until Hive Treatment History exists, the response explicitly reports treatment history as not modelled and uses `recent_treatment_count = null` rather than silently sending an empty history as fact.
- Test style: focused Core API tests.

## Data Shape

Minimum endpoint:

- `POST /v1/integrations/hivesight-advisor/varroa-context`

Headers:

- dedicated shared-secret header: `X-HiveSight-Service-Key`

Minimum request body:

- `hive_id`
- `inspection_photo_id`
- `jurisdiction_id`, optional

Minimum response body:

- `status`: `available` | `not_available`
- `contract_version`: `advisor_varroa_context_v1`
- `workspace_id`
- `hive_id`
- `apiary_id`
- `inspection_id`
- `inspection_photo_id`
- `inspection_date`
- `jurisdiction_id`, nullable
- `varroa_evidence`
  - `source_intent`
  - `evidence_readiness`: `integration_test_only` initially
  - `frame_mite_count`
    - `status`
    - `eligible_bee_count`
    - `processed_bee_count`
    - `bees_with_likely_varroa_count`
    - `likely_visible_varroa_detection_count`
    - `model_determinate_coverage_percent`
    - `completed_training_crop_count`
    - `unfinished_training_crop_count`
    - `excluded_training_crop_count`
    - `not_assessed_bee_count`
    - `failed_bee_count`
    - `not_assessed_reasons`
    - `failure_reasons`
    - `adapter_type`
    - `adapter_version`
    - `model_reference`
    - `caveats`
  - `photo_visible_varroa_evidence`
    - `readiness_state`
    - `eligible_complete_bee_count`
    - `reviewed_eligible_bee_count`
    - `determinate_eligible_bee_count`
    - `visible_varroa_bee_count`
    - `visible_mite_marker_count`
    - `active_negative_bee_count`
    - `not_determined_bee_count`
    - `review_completion_percent`
    - `determinate_varroa_coverage_percent`
    - `caveats`
- `treatment_history`
  - `status`: `not_modelled` initially
  - `recent_treatment_count`: null
  - `courses`: `[]`
- `advisor_request_readiness`
  - `can_request_advice`: boolean
  - `blocking_reasons`: list of machine-readable strings
  - `caveats`: list of strings
- `not_advice_reason`

Per-bee detector results, detection boxes, image URLs, Head-Up transform metadata, and Bee Annotation ids are deliberately excluded from the Advisor context contract.

## Example Contract Payload

Example request:

```json
{
  "hive_id": "00000000-0000-0000-0000-000000000302",
  "inspection_photo_id": "00000000-0000-0000-0000-000000000702",
  "jurisdiction_id": null
}
```

Example available response:

```json
{
  "contract_version": "advisor_varroa_context_v1",
  "status": "available",
  "workspace_id": "00000000-0000-0000-0000-000000000001",
  "apiary_id": "00000000-0000-0000-0000-000000000301",
  "hive_id": "00000000-0000-0000-0000-000000000302",
  "inspection_id": "00000000-0000-0000-0000-000000000401",
  "inspection_photo_id": "00000000-0000-0000-0000-000000000702",
  "inspection_date": "2026-08-06",
  "jurisdiction_id": null,
  "varroa_evidence": {
    "source_intent": "training_data_collection",
    "evidence_readiness": "integration_test_only",
    "frame_mite_count": {
      "status": "completed_with_warnings",
      "eligible_bee_count": 48,
      "processed_bee_count": 42,
      "bees_with_likely_varroa_count": 3,
      "likely_visible_varroa_detection_count": 4,
      "model_determinate_coverage_percent": 87.5,
      "completed_training_crop_count": 5,
      "unfinished_training_crop_count": 1,
      "excluded_training_crop_count": 0,
      "not_assessed_bee_count": 6,
      "failed_bee_count": 0,
      "not_assessed_reasons": {
        "partial_visible_bee": 4,
        "unreliable_orientation": 2
      },
      "failure_reasons": {},
      "adapter_type": "deterministic_stub",
      "adapter_version": "deterministic_stub_varroa_detector_v1",
      "model_reference": "deterministic_stub_varroa_detector_v1",
      "caveats": [
        "model_assisted_frame_count_only",
        "deterministic_stub_evidence",
        "bee_annotations_not_deduplicated_physical_bees"
      ]
    },
    "photo_visible_varroa_evidence": {
      "readiness_state": "partial_evidence",
      "eligible_complete_bee_count": 48,
      "reviewed_eligible_bee_count": 12,
      "determinate_eligible_bee_count": 10,
      "visible_varroa_bee_count": 2,
      "visible_mite_marker_count": 3,
      "active_negative_bee_count": 8,
      "not_determined_bee_count": 2,
      "review_completion_percent": 25.0,
      "determinate_varroa_coverage_percent": 20.8,
      "caveats": [
        "photo_visible_evidence_only",
        "human_review_incomplete"
      ]
    }
  },
  "treatment_history": {
    "status": "not_modelled",
    "recent_treatment_count": null,
    "courses": []
  },
  "advisor_request_readiness": {
    "can_request_advice": false,
    "blocking_reasons": [
      "jurisdiction_not_provided",
      "source_intent_not_varroa_assessment",
      "treatment_history_not_modelled"
    ],
    "caveats": [
      "context_available_for_integration_testing_only",
      "not_user_facing_varroa_assessment",
      "not_treatment_advice"
    ]
  },
  "not_advice_reason": "HiveSight is providing evidence context only; HiveSight Advisor owns recommendation logic."
}
```

## Proposed Gherkin

```gherkin
Feature: Advisor Varroa context API

  Scenario: HiveSight Advisor retrieves available Varroa context for one photographed frame
    Given a Hive has a Training Data Collection Inspection Photo with completed Training Crops and eligible bees
    And HiveSight is using the deterministic stub Varroa Detector adapter
    When HiveSight Advisor requests Varroa context for that Hive and Inspection Photo with the service credential
    Then HiveSight returns an available Advisor Varroa context
    And the context includes contract version, Workspace, Apiary, Hive, Inspection, Inspection Photo, and inspection date
    And the Varroa evidence keeps model-assisted frame mite count separate from human-reviewed photo-visible Varroa evidence
    And the frame mite count includes processed bee count, likely visible Varroa detections, bees with likely Varroa, coverage, adapter provenance, and caveats
    And the context exposes aggregate evidence only, without per-bee detector boxes or image URLs
    And advisor request readiness is false with blocking reasons for missing treatment-advice prerequisites
    And the context states that the evidence is not treatment advice

  Scenario: Advisor context is blocked when no frame evidence can be counted
    Given a Hive has a Training Data Collection Inspection Photo with no eligible processable bees
    When HiveSight Advisor requests Varroa context for that Hive and Inspection Photo with the service credential
    Then HiveSight returns a not_available Advisor Varroa context
    And the response still includes valid HiveSight identity and provenance fields
    And the context includes blocking reasons from the frame mite count
    And HiveSight does not return treatment advice

  Scenario: Advisor context rejects a photo from a different Hive
    Given one Hive has a Training Data Collection Inspection Photo
    And another Hive exists in the same Workspace
    When HiveSight Advisor requests Varroa context for the second Hive using the first Hive's Inspection Photo
    Then HiveSight rejects the request as photo_hive_mismatch
    And HiveSight does not disclose frame mite count details for the mismatched photo

  Scenario: Advisor context requires scoped service authentication
    Given a Hive has a Training Data Collection Inspection Photo with eligible frame evidence
    When a caller requests Advisor Varroa context without the Advisor service credential
    Then HiveSight rejects the request
    And normal development user authentication alone is not enough for the integration endpoint

  Scenario: Jurisdiction is optional for context but required for advice readiness
    Given a Hive has available frame mite count evidence
    When HiveSight Advisor requests Varroa context without a jurisdiction id
    Then HiveSight returns an available Advisor Varroa context
    And advisor request readiness is false
    And advisor request readiness includes jurisdiction_not_provided as a blocking reason

  Scenario: Training Data Collection evidence is integration-test context only
    Given a Hive has available frame mite count evidence from a Training Data Collection Inspection
    When HiveSight Advisor retrieves Advisor Varroa context
    Then the context reports evidence readiness as integration_test_only
    And advisor request readiness includes source_intent_not_varroa_assessment as a blocking reason
    And HiveSight does not describe the evidence as a user-facing Varroa Assessment

  Scenario: Treatment history absence is explicit
    Given HiveSight has not yet implemented Hive Treatment History
    When HiveSight Advisor retrieves available Varroa context
    Then the context reports treatment history status as not_modelled
    And recent treatment count is null
    And the context does not imply that the Hive has had no recent treatment
```

## Acceptance Criteria

- [ ] HiveSight exposes a dedicated Advisor Varroa context endpoint under a service-authenticated integration route.
- [ ] The service credential is scoped to the Advisor integration endpoint and is not accepted as normal user auth.
- [ ] Context requests validate that the selected Inspection Photo belongs to the requested Hive.
- [ ] Available context includes contract version, Workspace, Apiary, Hive, Inspection, Inspection Photo, inspection date, Varroa evidence, treatment-history modelling status, request readiness, and no-advice reason.
- [ ] Varroa evidence keeps model-assisted Frame Mite Count separate from human-reviewed Photo-visible Varroa Evidence.
- [ ] Advisor context exposes aggregate evidence only and excludes per-bee detector rows, detection boxes, image URLs, Head-Up transform metadata, and Bee Annotation ids.
- [ ] `completed_with_warnings` frame-count evidence remains available only with explicit warning/caveat detail.
- [ ] No processable frame evidence returns a domain `not_available` context with blocking reasons.
- [ ] Jurisdiction is optional for context but missing jurisdiction blocks `advisor_request_readiness.can_request_advice`.
- [ ] Training Data Collection evidence can be returned as integration-test context but blocks request readiness because it is not a user-facing Varroa Assessment.
- [ ] Treatment history is explicitly marked `not_modelled` until Hive Treatment History exists; `recent_treatment_count` is `null`, not `0`.
- [ ] The endpoint does not call HiveSight Advisor, create a Treatment Recommendation, create a Hive Treatment Course, or import treatment advice.
- [ ] Focused Core API tests and `pnpm verify:slice` pass before implementation closeout.
- [ ] The shared HiveSight Advisor integration contract is updated only after this slice is implemented and verified.

## Out Of Scope

- Calling `POST /integrations/hivesight/treatment-plans` on HiveSight Advisor.
- UI button to request Advisor guidance.
- Receiving, displaying, accepting, rejecting, or completing Advisor Treatment Recommendations.
- Hive Treatment Course, Treatment Application, or Treatment Outcome persistence.
- Treatment thresholds, risk bands, action language, or beekeeper-facing recommendation text.
- Statistical visible Varroa rate, confidence interval, sampling plan, or colony-level estimate.
- Durable Frame Mite Count history.
- Real Varroa Detector model implementation.

## Open Questions For Advisor Review

- Does HiveSight Advisor agree that `advisor_varroa_context_v1` carries enough aggregate Varroa evidence to decide whether a treatment-plan request could later be grounded?
- Does HiveSight Advisor agree that per-bee detections, image URLs, and detector boxes should stay inside HiveSight for this contract?
- Does HiveSight Advisor agree with `jurisdiction_not_provided`, `source_intent_not_varroa_assessment`, and `treatment_history_not_modelled` as blocking reason names?
- Does HiveSight Advisor agree that `treatment_history.status = not_modelled` and `recent_treatment_count = null` correctly distinguish missing domain modelling from no recent treatment?
