# Vertical Slice 0029.5: Advisor Treatment Recommendation Intake And Acceptance

Status: designed; acceptance scenarios pending signoff.

Numbering note: this slice intentionally uses `0029.5` because it belongs after Slice 0029 Advisor Varroa Context Assembly API and before the already-designed Slice 0030 Varroa Corpus Governance.

## Purpose

Create the first durable Treatment Evidence Chain from HiveSight Varroa evidence to HiveSight Advisor treatment advice and a beekeeper-owned planned treatment course.

Slice 0029 assembles Advisor Varroa context but does not call HiveSight Advisor, store advice, or create treatment history. Slice 0029.5 adds the first thin integration and treatment-history path:

- HiveSight builds a current Advisor Varroa context for one Hive and Inspection Photo.
- HiveSight calls HiveSight Advisor's treatment-plan endpoint through a replaceable adapter.
- HiveSight stores the outbound request snapshot and Advisor response as a pending Treatment Recommendation.
- The beekeeper can accept that pending recommendation into a separate planned Hive Treatment Course.

The recommendation does not become the treatment course. The course does not prove treatment happened. Actual Treatment Applications, treatment completion, treatment outcomes, and Advisor learning export governance remain later slices.

## Source Inputs

- `CONTEXT.md`: Varroa Assessment, Treatment Recommendation, Hive Treatment Course, Treatment Application, Treatment Outcome, Treatment Evidence Chain.
- `requirements/requirements.md`: FR-025 Advisor Treatment Recommendation Intake, FR-026 Treatment Recommendation Decision, FR-027 Hive Treatment Course, FR-030 Treatment Evidence Chain, FR-031 Advisor Learning Dataset Governance.
- `requirements/product-spec.md`: Future Advisor treatment workflow scenarios.
- `requirements/decision-log.md`: 2026-08-06 Treatment Recommendation And Treatment Course Are Separate Records.
- `requirements/roadmap.md`: Treatment And Advisor Integration tranche.
- `architecture/vertical-slice-0029-advisor-varroa-context-api.md`: Advisor Varroa context assembly and readiness blockers.
- `hivesight-advisor-integration-contract` skill: HiveSight Advisor exposes `POST /integrations/hivesight/treatment-plans` with `hive_id`, `jurisdiction_id`, and `situational_context`, authenticated by `X-HiveSight-Service-Key`.

## Proposed Acceptance Scenarios

Pending formal acceptance.

```gherkin
Feature: Advisor Treatment Recommendation Intake And Acceptance

  Scenario: HiveSight stores Advisor treatment advice as a pending recommendation
    Given a Beekeeper can access a Hive with available Advisor Varroa context
    And HiveSight has the jurisdiction and situational context required for an Advisor treatment-plan request
    When the Beekeeper requests Advisor treatment advice for that Hive evidence
    Then HiveSight sends the Advisor request through the configured Advisor treatment-plan adapter
    And HiveSight stores the Advisor request snapshot
    And HiveSight stores the Advisor response as a pending Treatment Recommendation
    And the Treatment Recommendation is linked to the source Varroa context, Hive, Apiary, Workspace, Inspection, and Inspection Photo
    And HiveSight does not create a Hive Treatment Course yet

  Scenario: HiveSight blocks treatment advice when the evidence is not ready
    Given a Beekeeper can access a Hive with Advisor Varroa context
    But the context has request-readiness blockers
    When the Beekeeper requests Advisor treatment advice
    Then HiveSight does not call HiveSight Advisor
    And HiveSight does not create a Treatment Recommendation
    And HiveSight returns the readiness blockers that prevented the request

  Scenario: Beekeeper accepts a pending recommendation into a separate planned treatment course
    Given HiveSight has a pending Treatment Recommendation for a Hive
    When the Beekeeper accepts the recommendation
    Then HiveSight records the recommendation decision as accepted
    And HiveSight creates a separate planned Hive Treatment Course for the same Hive
    And the Hive Treatment Course keeps a provenance link to the Treatment Recommendation
    And the Treatment Evidence Chain remains traceable from source Varroa context to Advisor request, Advisor response, beekeeper decision, and planned course

  Scenario: Beekeeper declines a pending recommendation without creating treatment history
    Given HiveSight has a pending Treatment Recommendation for a Hive
    When the Beekeeper declines the recommendation with an optional note
    Then HiveSight records the recommendation decision as declined
    And HiveSight keeps the original Advisor response unchanged
    And HiveSight does not create a Hive Treatment Course

  Scenario: Advisor request and response are preserved for audit without exposing private details for learning
    Given HiveSight has stored a Treatment Recommendation and related Treatment Evidence Chain
    When the records are read back through the Hive treatment API
    Then HiveSight shows the source evidence link, Advisor request provenance, Advisor response provenance, and beekeeper decision
    And HiveSight does not expose those records as Advisor learning, retrieval, or RAG material
    And HiveSight does not anonymise or export the records in this slice
```

## User Path

Given a beekeeper-facing Varroa evidence flow has enough information to request advice,
When the Beekeeper chooses to ask HiveSight Advisor for treatment advice,
Then HiveSight persists the request and response as a pending Treatment Recommendation.

Given the Beekeeper trusts the recommendation enough to act,
When they accept it,
Then HiveSight creates a separate planned Hive Treatment Course that remains linked to the original evidence and recommendation.

## Preconditions

- The user is authenticated through normal HiveSight Core API access and can access the Workspace containing the Hive.
- The Hive belongs to one Apiary and Workspace.
- The request references an Inspection Photo belonging to an Inspection for the same Hive.
- HiveSight can assemble Advisor Varroa context for the selected evidence using the Slice 0029 context builder.
- Advisor advice is requested only when `advisor_request_readiness.can_request_advice = true`.
- The first implementation may satisfy readiness through a controlled dev or test path, but production-facing behaviour must not bypass readiness blockers silently.
- HiveSight has a configured Advisor treatment-plan adapter:
  - real adapter calls HiveSight Advisor's `POST /integrations/hivesight/treatment-plans`;
  - stub adapter returns deterministic contract-shaped advice for local tests and acceptance fixtures.
- HiveSight does not interpret, improve, or rewrite the treatment recommendation text returned by Advisor.

## End-To-End Behaviour

HiveSight adds a treatment recommendation workflow behind the Core API.

Requesting advice:

- validates Hive, Workspace, Inspection, and Inspection Photo relationships;
- assembles current Advisor Varroa context using the Slice 0029 context builder;
- refuses to call Advisor when the context has readiness blockers;
- builds the Advisor request payload with HiveSight's canonical `hive_id`, `jurisdiction_id`, and `situational_context`;
- calls Advisor through `HiveSightAdvisorTreatmentPlanAdapter`;
- stores the exact request snapshot sent through the adapter;
- stores the Advisor response payload and provenance as a Treatment Recommendation with status `pending`;
- returns the pending recommendation and chain identifiers to HiveSight.

Accepting advice:

- requires a pending Treatment Recommendation in the same Workspace;
- records a beekeeper decision of `accepted`, with user id and timestamp;
- creates a separate Hive Treatment Course in status `planned`;
- copies the Advisor-recommended plan details into the course as the initial plan snapshot;
- links the course back to the recommendation and evidence chain.

Declining advice:

- requires a pending Treatment Recommendation in the same Workspace;
- records a beekeeper decision of `declined`, with user id, timestamp, and optional note;
- leaves the original Advisor response unchanged;
- creates no treatment course.

This slice should expose enough API behaviour for HiveSight Advisor blueprinting and future UI work. A polished beekeeper-facing treatment screen is deferred until the treatment course, application, and outcome lifecycle are richer.

## Layers Touched

- Web UI: Not required for this slice. A later UI slice can add buttons and treatment history screens once the API behaviour is stable.
- Core API: Add routes to request Advisor treatment advice, read Treatment Recommendations, accept a recommendation, and decline a recommendation.
- Analysis Service: Not touched.
- Storage: Add durable persistence for Advisor request snapshots, Treatment Recommendations, recommendation decisions, Treatment Evidence Chain ids, and planned Hive Treatment Courses.
- Queue or async boundary: Not required initially; the Advisor call is synchronous through an adapter. A later slice may move it to a background workflow if latency or failure recovery demands it.
- Contracts: Add HiveSight Core API request/response models for recommendations, decisions, evidence-chain provenance, and planned treatment courses. Update the shared integration contract only after the real Advisor call path is implemented and verified.
- Observability: Log advice-request-created, advice-request-blocked, advisor-call-succeeded, advisor-call-failed, recommendation-accepted, and recommendation-declined events with Workspace, Hive, recommendation, and evidence-chain ids.

## Test Seams

- Seam: Advisor readiness guard
- Behaviour verified: HiveSight does not call Advisor or create a recommendation when Slice 0029 context readiness is blocked.
- Test style: focused Core API/service tests and API-level BDD.

- Seam: Advisor treatment-plan adapter
- Behaviour verified: real and stub adapters share the same request/response contract shape; the service stores the exact request and response snapshots.
- Test style: adapter contract tests with a deterministic stub and a narrowly scoped integration smoke when the real Advisor service is available.

- Seam: Treatment Recommendation persistence
- Behaviour verified: pending recommendations survive a Postgres-backed readback with source Varroa context, request snapshot, response provenance, status, and Workspace/Hive relationships intact.
- Test style: focused repository/API tests, including a Postgres migration/restart-survival guard where practical.

- Seam: Recommendation decision
- Behaviour verified: accepting a pending recommendation creates a separate planned Hive Treatment Course; declining records a decision and creates no course.
- Test style: focused Core API tests and BDD.

- Seam: Treatment Evidence Chain
- Behaviour verified: the chain can be traversed from planned course back to recommendation, Advisor request/response, source Varroa context, Hive, Inspection, and Inspection Photo.
- Test style: API/service tests and one end-to-end acceptance scenario.

## Data Shape

Minimum new records:

- `AdvisorTreatmentRequestSnapshot`
  - `advisor_treatment_request_snapshot_id`
  - `treatment_evidence_chain_id`
  - `workspace_id`
  - `apiary_id`
  - `hive_id`
  - `inspection_id`
  - `inspection_photo_id`
  - `advisor_context_contract_version`
  - `advisor_request_contract_version`
  - `jurisdiction_id`
  - `situational_context`
  - `request_payload`
  - `adapter_type`
  - `adapter_version`
  - `created_by_user_id`
  - `created_at`

- `TreatmentRecommendation`
  - `treatment_recommendation_id`
  - `treatment_evidence_chain_id`
  - `advisor_treatment_request_snapshot_id`
  - `workspace_id`
  - `apiary_id`
  - `hive_id`
  - `status`: `pending` | `accepted` | `declined`
  - `advisor_response_payload`
  - `recommendation_text`
  - `grounding_status`
  - `citations`
  - `response_received_at`
  - `decision_by_user_id`
  - `decision_at`
  - `decision_note`

- `HiveTreatmentCourse`
  - `hive_treatment_course_id`
  - `treatment_evidence_chain_id`, nullable for later manual courses
  - `source_treatment_recommendation_id`, nullable
  - `workspace_id`
  - `apiary_id`
  - `hive_id`
  - `purpose`: `varroa`
  - `status`: `planned`
  - `planned_course_snapshot`
  - `created_by_user_id`
  - `created_at`

Minimum API routes:

- `POST /v1/hives/{hive_id}/advisor-treatment-recommendations`
- `GET /v1/hives/{hive_id}/treatment-recommendations`
- `POST /v1/treatment-recommendations/{treatment_recommendation_id}/accept`
- `POST /v1/treatment-recommendations/{treatment_recommendation_id}/decline`
- `GET /v1/hives/{hive_id}/treatment-courses`

## Out Of Scope

- Recording actual Treatment Applications or doses.
- Marking a treatment course complete, cancelled, failed, or successful.
- Linking follow-up inspections to treatment outcomes.
- Manual Hive Treatment Course entry without an Advisor recommendation.
- User-facing treatment schedule editing.
- Threshold logic deciding whether treatment is needed inside HiveSight.
- HiveSight rewriting, summarising, or validating Advisor advice beyond storage and provenance.
- Advisor-side recommendation graph changes.
- Durable background suspend/resume between HiveSight and Advisor.
- Advisor learning, RAG, retrieval, export, anonymisation, or permitted-use governance.
- Public beekeeper UI polish for treatment history.
