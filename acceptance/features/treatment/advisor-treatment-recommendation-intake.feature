@api
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
