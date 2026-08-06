# Vertical Slice 0029.5: Advisor Treatment Recommendation Intake And Acceptance

Status: implemented; acceptance scenarios formally accepted on 2026-08-06; HiveSight Advisor Slice 0011 contract update incorporated. HiveSight-side stub implementation is aligned to Advisor's `treatment_plan_v1` response shape; the real Advisor adapter remains a later opt-in integration path.

Numbering note: this slice intentionally uses `0029.5` because it belongs after Slice 0029 Advisor Varroa Context Assembly API. Varroa Corpus Governance is now an unnumbered future candidate; Slice 0030 is reserved for the accepted Dual-Seam Acceptance Specification Pilot.

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
- `hivesight-advisor-integration-contract` skill: HiveSight Advisor exposes `POST /integrations/hivesight/treatment-plans` with `hive_id`, `jurisdiction_code`, and `situational_context`, authenticated by `X-HiveSight-Service-Key`.

## HiveSight Advisor Review Outcome

HiveSight Advisor reviewed this slice on 2026-08-06 and confirmed the main direction:

- HiveSight remains the sole caller into HiveSight Advisor.
- HiveSight should continue to call `POST /integrations/hivesight/treatment-plans`.
- Advisor Slice 0011 updated the request body to:
  - `hive_id`: string, treated by Advisor as an opaque HiveSight identifier;
  - `jurisdiction_code`: stable external jurisdiction code, currently `uk` or `us`;
  - `situational_context`: string, used by Advisor as the RAG query text.
- Advisor currently accepts only prose `situational_context`. HiveSight should transform its richer Slice 0029 context into concise Advisor-facing prose rather than expecting Advisor to consume a structured evidence object.
- Advisor Slice 0011 response bodies include:
  - `contract_version`: `treatment_plan_v1`;
  - `answer_id`: Advisor's durable recommendation identifier;
  - `text`;
  - `grounding_status`: `grounded` | `partial` | `ungrounded`;
  - `citations`: list of passage/document provenance objects.
- Repeated unresolved treatment-plan requests for the same Hive are idempotent on the Advisor side and return the existing pending recommendation rather than creating a competing one.

The previous Advisor-side contract-readiness blockers are therefore closed by Advisor Slice 0011. One HiveSight-side integration concern remains parked: when HiveSight later exposes reverse-direction callbacks for Advisor, it should use a direction-specific inbound service-auth header such as `X-Advisor-Service-Key` rather than reusing Advisor's `X-HiveSight-Service-Key`.

## Grilling Decisions

- Slice 0029.5 includes acceptance into a planned Hive Treatment Course so the first Treatment Evidence Chain reaches a beekeeper-owned treatment plan, but it stops before applications, completion, cancellation, outcome, or course editing.
- HiveSight stores the full source context internally for audit, but sends Advisor a narrower treatment-plan request payload shaped for Advisor's existing endpoint.
- Product behaviour must hard-block Advisor calls when `advisor_request_readiness.can_request_advice = false`; tests may inject a ready context through a stubbed context-builder seam.
- Requesting advice, accepting advice, and declining advice are Beekeeper or Workspace-owner actions, not Dataset Curator capability actions.
- Accepted courses preserve Advisor text and optional structured plan data as snapshots. Structured fields are optional because Advisor's current built endpoint returns text, grounding status, and citations.
- Accept and decline decisions are not reversible in this slice. Later course cancellation or supersession belongs to treatment lifecycle work.
- Slice 0029.5 does not notify HiveSight Advisor when a recommendation is accepted or declined. Advisor callback or resume integration belongs to a later cross-system workflow slice.
- HiveSight allows only one pending Varroa Treatment Recommendation per Hive. Retrying while a Hive has a pending recommendation returns the existing pending recommendation; a later accepted or declined recommendation can be followed by a new request snapshot if the Beekeeper deliberately asks again.
- Advisor citations are stored both in the raw response payload and as structured citation data for display and audit. They are displayed as a separate reference list; HiveSight must not assume Advisor response text contains inline citation markers.
- Planned Hive Treatment Courses created from accepted recommendations are not editable in this slice.
- Manual Hive Treatment Course entry without an Advisor recommendation is a separate roadmap item, not part of Slice 0029.5.
- Local development, automated tests, and normal slice verification use a deterministic stub Advisor treatment-plan adapter by default. The real HiveSight Advisor adapter is opt-in configuration and should be covered by a separate smoke/integration check.
- Before implementation, HiveSight Advisor should review this slice and confirm the exact treatment-plan request and response shape HiveSight should build against.
- Advisor Slice 0011 resolved the real-adapter contract blockers around Advisor idempotency, jurisdiction identifiers, response contract versioning, and `answer_id` provenance.
- Slice 0029.5 creates an explicit lightweight `TreatmentEvidenceChain` id rather than implying the chain from foreign keys.
- The chain starts from an immutable `AdvisorVarroaContextSnapshot`, not only from an Inspection Photo, because the same photo may produce different advice context over time.
- Accepting a recommendation snapshots beekeeper decision context: who accepted it, when, optional note, recommendation id, and evidence-chain id.
- Decline notes are optional.
- Recommendation state leaves room for later staleness or supersession, but Slice 0029.5 does not auto-expire pending recommendations.
- `jurisdiction_code` is required before HiveSight calls Advisor. HiveSight must send a stable external code and must not depend on Advisor's internal jurisdiction primary keys.
- Advisor responses are labelled as suggested treatment plans requiring beekeeper decision, not authoritative applied treatment.
- Treatment records should have a generic enough concern/purpose field, but Slice 0029.5 supports only `varroa` behaviour.
- Planned treatment courses created in this slice do not require planned dates.
- Treatment recommendation and course persistence must work in both in-memory and Postgres-backed paths; Postgres verification is part of acceptance closeout.
- Read routes are required so the stored recommendation, planned course, and chain provenance can be verified without a UI.
- The shared `hivesight-advisor-integration-contract` skill has been updated after Advisor Slice 0011 implemented the settled real call shape.
- Slice 0029.5 is API-only. The future `Ask Advisor` UI trigger belongs behind a genuine user-facing Varroa Assessment flow, not Training Data Collection evidence.
- Training Data Collection evidence remains blocked in product behaviour. Tests may use a synthetic ready context seam, but product advice requires real Advisor-ready Varroa Assessment context.
- Accepted planned courses are visible as `planned` treatment history, but they do not imply treatment has been applied.
- Adapter provenance must distinguish `stub` from `hivesight_advisor`; production-like configuration must not allow stub-backed advice to create beekeeper treatment history.
- Recommendation decisions are current fields on `TreatmentRecommendation` in this slice, not a separate immutable decision-history table.
- Accept and decline operations are idempotent for repeated same-state requests. Accept creates at most one planned course. Decline cannot reverse an accepted recommendation.
- Domain uniqueness rules are enough for this slice; no generic client-supplied idempotency key is introduced.
- HiveSight stores the exact outbound Advisor request payload and exact inbound Advisor response payload as provenance snapshots, even when summary fields are also extracted.
- A new request is blocked when the Hive already has an open planned Varroa treatment course, unless the request is reading back the recommendation that created that course.
- Recommendation and course records denormalise `workspace_id`, `apiary_id`, and `hive_id`, but do not snapshot human-readable Apiary or Hive names in this slice.
- Slice 0029.5 remains scoped to a single Inspection Photo because Slice 0029 context assembly is photo-scoped.
- Workspace access governs recommendation and treatment-course visibility; records are not visible only to the requesting user.
- No notifications, reminders, or follow-up scheduling are included.
- Failed Advisor calls create failed request snapshots and failed evidence-chain records, but no Treatment Recommendation.
- Blocked readiness attempts also create context snapshots and blocked evidence-chain records, but no Advisor call and no Treatment Recommendation.
- Manual retry after a failed Advisor request creates a new chain pointing back to the same source context rather than reusing the failed chain.
- `AdvisorVarroaContextSnapshot` stores the full Slice 0029 response payload, and is created only when advice is requested.
- Blocked and failed advice attempts are visible in a dedicated chain-history read model, not folded into the Treatment Recommendation list.
- Chain-history list endpoints return summaries by default; single-chain detail may include raw context, request, and response payloads.
- Snapshot retention/minimisation policy is deferred governance work. Slice 0029.5 retains provenance snapshots durably.
- Observability covers blocked readiness attempts, failed Advisor requests, recommendation creation, acceptance, and decline.

## Signed-Off Acceptance Scenarios

Formally accepted on 2026-08-06.

```gherkin
Feature: Advisor Treatment Recommendation Intake And Acceptance

  Scenario: HiveSight stores Advisor treatment advice as a pending recommendation with an evidence chain
    Given a Beekeeper can access a Hive with Advisor-ready Varroa Assessment context for one Inspection Photo
    And the Hive has no open planned Varroa treatment course
    And HiveSight has a jurisdiction for the Advisor treatment-plan request
    When the Beekeeper requests Advisor treatment advice for that Hive evidence
    Then HiveSight sends the Advisor request through the configured Advisor treatment-plan adapter
    And HiveSight stores the full Advisor Varroa context snapshot
    And HiveSight stores the Advisor request snapshot
    And HiveSight stores the Advisor response as a pending Treatment Recommendation
    And the pending Treatment Recommendation is labelled as a suggested treatment plan requiring beekeeper decision
    And the Treatment Evidence Chain links the source context, request snapshot, response, Hive, Apiary, Workspace, Inspection, and Inspection Photo
    And HiveSight does not create a Hive Treatment Course yet

  Scenario: HiveSight blocks treatment advice when the evidence is not Advisor-ready
    Given a Beekeeper can access a Hive with Advisor Varroa context
    But the context has request-readiness blockers
    When the Beekeeper requests Advisor treatment advice
    Then HiveSight does not call HiveSight Advisor
    And HiveSight does not create a Treatment Recommendation
    And HiveSight stores the full Advisor Varroa context snapshot
    And HiveSight records a blocked Treatment Evidence Chain with the readiness blockers
    And the blocked advice attempt is visible in the Hive's advice-attempt history

  Scenario: HiveSight records an Advisor call failure without creating advice
    Given a Beekeeper can access a Hive with Advisor-ready Varroa Assessment context for one Inspection Photo
    And the Hive has no open planned Varroa treatment course
    And the configured Advisor treatment-plan adapter fails to return usable advice
    When the Beekeeper requests Advisor treatment advice
    Then HiveSight stores the full Advisor Varroa context snapshot
    And HiveSight stores the failed Advisor request snapshot with adapter provenance
    And HiveSight records a failed Treatment Evidence Chain
    And HiveSight does not create a Treatment Recommendation
    And the failed advice attempt is visible in the Hive's advice-attempt history

  Scenario: Beekeeper accepts a pending recommendation into a separate planned treatment course
    Given HiveSight has a pending Treatment Recommendation for a Hive
    When the Beekeeper accepts the recommendation
    Then HiveSight records the recommendation decision as accepted
    And HiveSight creates a separate planned Hive Treatment Course for the same Hive
    And the planned course is visible in Hive treatment-course history with status planned
    And the Hive Treatment Course keeps a provenance link to the Treatment Recommendation
    And the planned course snapshots the beekeeper decision context
    And the Treatment Evidence Chain remains traceable from source context to Advisor request, Advisor response, beekeeper decision, and planned course

  Scenario: Beekeeper declines a pending recommendation without creating treatment history
    Given HiveSight has a pending Treatment Recommendation for a Hive
    When the Beekeeper declines the recommendation with an optional note
    Then HiveSight records the recommendation decision as declined
    And HiveSight keeps the original Advisor response unchanged
    And HiveSight does not create a Hive Treatment Course

  Scenario: Repeated advice request for a Hive with a pending recommendation returns the existing recommendation
    Given HiveSight has one pending Varroa Treatment Recommendation for a Hive
    When the Beekeeper requests Advisor treatment advice again for the same Hive
    Then HiveSight returns the existing pending Treatment Recommendation
    And HiveSight does not create a duplicate pending recommendation

  Scenario: Repeated acceptance returns the existing planned treatment course
    Given HiveSight has a pending Treatment Recommendation for a Hive
    And the Beekeeper has already accepted that recommendation once
    When the Beekeeper accepts the same recommendation again
    Then HiveSight returns the same planned Hive Treatment Course both times
    And HiveSight creates only one planned Hive Treatment Course

  Scenario: Repeated decline returns the existing declined recommendation
    Given HiveSight has a declined Treatment Recommendation for a Hive
    When the Beekeeper declines the same recommendation again
    Then HiveSight returns the same declined Treatment Recommendation both times
    And HiveSight does not create a Hive Treatment Course

  Scenario: Decline cannot reverse acceptance
    Given HiveSight has an accepted Treatment Recommendation for a Hive
    When the Beekeeper tries to decline the accepted recommendation
    Then HiveSight blocks the decline
    And HiveSight keeps the existing planned Hive Treatment Course

  Scenario: Production-like configuration rejects stub-backed treatment advice
    Given HiveSight is running in production-like configuration
    And the configured Advisor treatment-plan adapter is the deterministic stub
    When a Beekeeper requests Advisor treatment advice
    Then HiveSight blocks the request before creating treatment advice
    And HiveSight does not create a Treatment Recommendation
    And HiveSight does not create a Hive Treatment Course

  Scenario: Open planned Varroa treatment blocks a new Advisor recommendation
    Given a Hive already has an open planned Varroa treatment course
    When the Beekeeper requests a new Advisor treatment recommendation for that Hive
    Then HiveSight blocks the request
    And HiveSight explains that an open planned Varroa treatment course already exists
    And HiveSight does not call HiveSight Advisor
    And HiveSight does not create a new Treatment Recommendation

  Scenario: HiveSight exposes chain history separately from recommendation history
    Given a Hive has a blocked advice attempt, a failed advice attempt, a pending recommendation, and an accepted recommendation
    When the Beekeeper reads the Hive's Advisor treatment advice-attempt history
    Then HiveSight lists each Treatment Evidence Chain with a summary state
    And blocked and failed attempts are not shown as Treatment Recommendations

  Scenario: HiveSight exposes single-chain provenance details for audit
    Given HiveSight has stored a Treatment Evidence Chain for Advisor treatment advice
    When the Beekeeper reads a single Treatment Evidence Chain
    Then HiveSight includes the source context summary, request provenance, response provenance where present, decision where present, and planned course where present

  Scenario: Advisor request and response are preserved for audit without exposing records for learning
    Given HiveSight has stored a Treatment Recommendation and related Treatment Evidence Chain
    When the Beekeeper reads the single Treatment Evidence Chain
    Then HiveSight can return the full source context, outbound request payload, and inbound response payload for audit
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
- stores an immutable Advisor Varroa context snapshot;
- records a blocked Treatment Evidence Chain and refuses to call Advisor when the context has readiness blockers;
- builds the Advisor request payload with HiveSight's canonical `hive_id`, `jurisdiction_code`, and `situational_context`;
- calls Advisor through `HiveSightAdvisorTreatmentPlanAdapter`;
- stores the exact request snapshot sent through the adapter;
- records a failed Treatment Evidence Chain and creates no Treatment Recommendation when Advisor fails to return usable advice;
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
- Core API: Add routes to request Advisor treatment advice, read Treatment Recommendations, accept a recommendation, decline a recommendation, read treatment courses, list advice attempts, and read a single Treatment Evidence Chain.
- Analysis Service: Not touched.
- Storage: Add durable persistence for Treatment Evidence Chains, Advisor Varroa context snapshots, Advisor request snapshots, failed request snapshots, Treatment Recommendations, recommendation decisions, and planned Hive Treatment Courses.
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
  - `jurisdiction_code`
  - `situational_context`
  - `request_payload`
  - `request_status`: `sent` | `failed`
  - `error_summary`, nullable
  - `adapter_type`
  - `adapter_version`
  - `created_by_user_id`
  - `created_at`

- `TreatmentEvidenceChain`
  - `treatment_evidence_chain_id`
  - `workspace_id`
  - `apiary_id`
  - `hive_id`
  - `inspection_id`
  - `inspection_photo_id`
  - `concern`: `varroa`
  - `state`: `blocked_not_ready` | `advisor_request_failed` | `recommendation_pending` | `recommendation_accepted` | `recommendation_declined`
  - `blocked_reasons`
  - `created_by_user_id`
  - `created_at`
  - `updated_at`

- `AdvisorVarroaContextSnapshot`
  - `advisor_varroa_context_snapshot_id`
  - `treatment_evidence_chain_id`
  - `workspace_id`
  - `apiary_id`
  - `hive_id`
  - `inspection_id`
  - `inspection_photo_id`
  - `advisor_context_contract_version`
  - `context_payload`
  - `context_summary`
  - `created_by_user_id`
  - `created_at`

- `TreatmentRecommendation`
  - `treatment_recommendation_id`
  - `treatment_evidence_chain_id`
  - `advisor_treatment_request_snapshot_id`
  - `workspace_id`
  - `apiary_id`
  - `hive_id`
  - `concern`: `varroa`
  - `status`: `pending` | `accepted` | `declined` | `superseded`
  - `advisor_response_payload`
  - `recommendation_text`
  - `grounding_status`
  - `citations`
  - `advisor_answer_id`, nullable only when no usable Advisor response is available
  - `adapter_type`: `stub` | `hivesight_advisor`
  - `adapter_version`
  - `advisor_response_contract_version`, nullable only when no usable Advisor response is available
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
  - `accepted_by_user_id`
  - `accepted_at`
  - `acceptance_note`
  - `created_by_user_id`
  - `created_at`

Minimum API routes:

- `POST /v1/hives/{hive_id}/advisor-treatment-recommendations`
- `GET /v1/hives/{hive_id}/treatment-recommendations`
- `POST /v1/treatment-recommendations/{treatment_recommendation_id}/accept`
- `POST /v1/treatment-recommendations/{treatment_recommendation_id}/decline`
- `GET /v1/hives/{hive_id}/treatment-courses`
- `GET /v1/hives/{hive_id}/advisor-treatment-advice-attempts`
- `GET /v1/treatment-evidence-chains/{treatment_evidence_chain_id}`

## HiveSight Advisor Follow-Up Questions

Advisor Slice 0011 answered the blocking request/response contract questions:

- HiveSight sends `jurisdiction_code`, not Advisor's internal jurisdiction id.
- HiveSight persists Advisor response `contract_version = treatment_plan_v1`.
- HiveSight persists Advisor `answer_id` as the cross-service recommendation identifier.
- Advisor returns the existing pending recommendation for repeated unresolved treatment-plan requests for the same Hive.

Before enabling reverse-direction calls from Advisor into HiveSight, agree the HiveSight inbound service-auth header name. The current recommendation is `X-Advisor-Service-Key`.

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
