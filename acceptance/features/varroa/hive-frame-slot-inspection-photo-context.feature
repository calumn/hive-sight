@api
Feature: Hive frame slot inspection photo context

  Scenario: Varroa assessment inspection starts with brood slot coverage
    Given a Beekeeper has configured a hive with 10 active brood Hive Frame Slots
    And the Workspace has an accepted Workspace Data Use Agreement
    When the Beekeeper creates a Varroa Assessment Inspection for that hive
    Then HiveSight shows one pending Inspection Frame Observation for each active brood slot
    And HiveSight prevents photos from being attached to those pending observations

  Scenario: Beekeeper inspects a brood slot before attaching side photos
    Given a Varroa Assessment Inspection has a pending observation for brood slot 6
    When the Beekeeper marks brood slot 6 inspected
    Then HiveSight asks whether the observed frame is continuous with the previous observation
    When the Beekeeper records that the observed frame is continuous with the previous observation
    And the Beekeeper attaches one side A photo and one side B photo to that observation
    Then HiveSight shows both photos under the same Inspection Frame Observation
    And HiveSight shows side A and side B as separate frame-side evidence

  Scenario: HiveSight rejects side-photo combinations that would skew frame evidence
    Given an inspected brood slot observation already has a side A photo and a side B photo
    When the Beekeeper tries to attach another side A photo
    Then HiveSight rejects the photo
    When the Beekeeper tries to attach an unknown-side photo
    Then HiveSight rejects the photo
    Given an inspected brood slot observation has one unknown-side photo
    When the Beekeeper tries to attach a side A photo
    Then HiveSight rejects the photo

  Scenario: Skipped and inactive brood slots break same-frame continuity
    Given a Varroa Assessment Inspection has brood slot observations
    When the Beekeeper marks an active brood slot skipped
    Then HiveSight shows the observation as skipped
    And HiveSight shows frame continuity as not continuous or unknown
    And HiveSight prevents photos from being attached to that observation
    When a historical brood slot is inactive for the current hive brood slot count
    Then HiveSight shows the observation as inactive
    And HiveSight shows frame continuity as not continuous or unknown
    And HiveSight prevents photos from being attached to that observation

  Scenario: Brood slot count changes preserve historical slot identity
    Given a hive has 12 brood Hive Frame Slots with historical observations
    When the Beekeeper changes the active brood slot count to 10
    Then HiveSight archives brood slots 11 and 12 for future inspections
    And HiveSight keeps their historical observations and photos visible
    When the Beekeeper changes the active brood slot count back to 12
    Then HiveSight reactivates the same brood slots 11 and 12
    And new inspections use those same slot identities
