# Vertical Slice 0036: Hive Frame Slot And Inspection Photo Side Context

Status: planned.

## Purpose

Let a Beekeeper capture brood-box frame-position context during an Inspection without turning HiveSight into a permanent physical-frame inventory system.

This slice adds lightweight Hive Frame Slots for brood-box positions, creates Inspection Frame Observations for those slots during a Varroa Assessment Inspection, and lets a Beekeeper attach one or two side-labelled Inspection Photos only after explicitly marking a slot as inspected. It preserves when a brood slot was skipped, inactive, or inspected so future frame-position comparison and same-frame continuity claims do not rely on filenames or missing-data guesses.

This slice does not calculate a new inspection-level result, complete an Inspection, infer brood pattern, or compare treatment outcomes. It creates the durable frame-position evidence needed before those later workflows can be trusted.

## Source Inputs

- `CONTEXT.md`: Hive Frame Slot, Inspection Frame Observation, Frame Side, Inspection, Inspection Photo, Frame Label.
- `architecture/domain-model.md`: Hive Frame Slot and Inspection Frame Observation relationship model.
- `architecture/domain-model-diagram.md`: Hive to Hive Frame Slot to Inspection Frame Observation to Inspection Photo relationship.
- `requirements/product-spec.md`: hive inspection photo capture scenarios and lightweight frame-position handling.
- `requirements/requirements.md`: FR-005 Multiple Photos Per Frame and NFR-003 Data Organisation.
- `requirements/acceptance-criteria.md`: distinguishing photos that belong to the same Hive Frame Slot, Inspection Frame Observation, and Frame Side.
- `requirements/model-requirements.md`: dataset leakage prevention for same slot, same observed frame, duplicate, near-duplicate, and paired side photos.
- `architecture/parking-lot.md`: PARK-0060 Inspection Completion And Pending Brood Slot Closure.

## Acceptance Scenarios

These scenarios were reviewed and approved on 2026-08-17.

```gherkin
@api @web
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
```

## User Path

Given a Beekeeper has a Hive with configured brood frame slots,
when they create or open a Varroa Assessment Inspection,
then HiveSight shows a brood-slot coverage surface where each slot starts pending or inactive.

When the Beekeeper marks an active brood slot inspected,
then HiveSight asks whether the observed frame is continuous with the previous observation before side photos can be attached.

When the Beekeeper attaches photos,
then HiveSight allows only a valid side set for that observed frame: no photos, one unknown-side photo, one side A photo, one side B photo, or one side A plus one side B.

## Preconditions

- The actor has access to the Workspace.
- The Workspace Data Use Agreement is accepted before photo upload.
- The Hive has Hive Configuration.
- The Hive has, or can derive, active brood Hive Frame Slots from configured brood slot count.
- The Inspection intent is `varroa_assessment`.
- Existing Training Data Collection workflows remain usable with legacy photo intake; this slice focuses on Varroa Assessment brood-slot context.

## End-To-End Behaviour

Add a lightweight brood-slot setup and inspection coverage path.

Hive Configuration records an editable brood slot count. HiveSight may default that count from hive type or brood box type where known, but the Beekeeper can override it because beekeepers may use spacer boards or pack different frame counts into the same box type.

HiveSight maintains Hive Frame Slots for brood positions:

- increasing the active brood slot count creates or reactivates slots up to the new count;
- reducing the active brood slot count archives slots above the new count for future inspections;
- archived slots remain visible in historical inspection evidence;
- re-increasing the count reactivates the same slot records rather than creating new identities.

When a Varroa Assessment Inspection is created or initialized for frame context, HiveSight creates Inspection Frame Observations for every brood Hive Frame Slot with history:

- active slots start as `pending`;
- archived or out-of-count slots start as `inactive`;
- inactive observations are retained in the inspection coverage grid so historical slot continuity is visible.

The Beekeeper must explicitly resolve an active observation:

- `inspected`: the slot/frame was looked at during this hive opening;
- `skipped`: the active slot was deliberately not inspected.

Marking an observation `inspected` requires an explicit continuity answer:

- `continuous_with_previous_observation`: the Beekeeper believes this slot's frame content is meaningfully continuous with the previous observation chain;
- `not_continuous_or_unknown`: the frame content changed, moved, was replaced, or continuity cannot be trusted.

`skipped` and `inactive` observations record continuity as `not_continuous_or_unknown` and break same-frame comparison chains. They remain useful as slot-position evidence and coverage evidence.

Photos can attach only to `inspected` observations. Attaching a photo must not silently mark a slot inspected. The UI and API require the Beekeeper to mark the observation inspected and answer continuity first.

Photo side rules for one Inspection Frame Observation:

- no photos is valid;
- one `unknown` photo is valid;
- one `side_a` photo is valid;
- one `side_b` photo is valid;
- one `side_a` plus one `side_b` is valid;
- `unknown` cannot coexist with any other side;
- more than one photo for a side is invalid;
- more than two photos total is invalid.

Frame Side labels are relative within one Inspection Frame Observation. HiveSight must not assume `side_a` in one inspection is the same physical side as `side_a` in another inspection. Historical comparison in this slice is at Hive Frame Slot / observed-frame level, not side-to-side across inspections.

## Layers Touched

- Web UI: add or extend Hive setup/configuration controls for brood slot count; show brood-slot observation grid for Varroa Assessment inspections; let the Beekeeper mark active slots inspected or skipped; ask continuity when marking inspected; attach side-labelled photos only to inspected observations; show inactive slots as historical/not-in-use context.
- Core API: add Hive Frame Slot endpoints or extend Hive Configuration/Hive response shape; add Inspection Frame Observation listing and update commands; extend photo intake/update contract with observation id and frame side; enforce observation status, continuity, and photo side invariants.
- Analysis Service: not touched.
- Storage: persist Hive Frame Slots, Inspection Frame Observations, observation status, continuity status, frame side on Inspection Photos, and archived/reactivated slot state; add migrations and live Postgres verification.
- Queue or async boundary: not touched.
- Contracts: internal Web/Core API contracts change; no HiveSight Advisor contract change.
- Observability: add structured domain errors for invalid observation/photo side transitions if local Core API patterns support it.

## Test Seams

- Seam: Hive frame slot configuration
- Behaviour verified: brood slot count creates, archives, and reactivates stable Hive Frame Slot identities without losing historical observations.
- Test style: focused Core API workflow tests plus Postgres persistence test.

- Seam: Inspection frame observation workflow
- Behaviour verified: Varroa Assessment Inspection creates pending/inactive brood-slot observations; active observations can be marked inspected or skipped; inspected requires continuity; skipped and inactive break continuity.
- Test style: API-level BDD plus focused Core API tests.

- Seam: Inspection photo side assignment
- Behaviour verified: photos attach only to inspected observations; valid side sets are accepted; duplicate sides, unknown-plus-side, photos on skipped/inactive/pending observations, and more than two photos are rejected.
- Test style: focused Core API regression tests around `InspectionPhotoAccess` and photo listing/response shape.

- Seam: Web brood-slot coverage surface
- Behaviour verified: Beekeeper can resolve brood slots, answer continuity, attach side photos, and see pending/skipped/inspected/inactive state without losing existing Varroa Assessment analysis controls.
- Test style: focused Playwright browser acceptance.

## Data Shape

Minimum new or extended concepts:

- `HiveFrameSlot`
  - `hive_frame_slot_id`
  - `hive_id`
  - optional `hive_configuration_id`
  - `frame_use`, initially focused on `brood`
  - `slot_number` or `slot_code`
  - optional `display_label`
  - `status`: `active`, `archived`
  - timestamps

- `InspectionFrameObservation`
  - `inspection_frame_observation_id`
  - `inspection_id`
  - `hive_frame_slot_id`
  - `observation_status`: `pending`, `inspected`, `skipped`, `inactive`
  - `continuity_status`: `pending`, `continuous_with_previous_observation`, `not_continuous_or_unknown`
  - optional `inspection_order`
  - optional notes
  - timestamps

- `InspectionPhotoResponse` extension
  - optional `inspection_frame_observation_id`
  - optional `hive_frame_slot_id` for display convenience if local API patterns support denormalised response fields
  - optional `frame_side`: `side_a`, `side_b`, `unknown`

- Hive Configuration extension
  - editable `brood_slot_count`

## Out Of Scope

- Permanent physical wooden-frame or comb inventory.
- Tracking frame movement between slots.
- Slot-layout version history beyond active/archive slot state.
- Super-box mandatory coverage.
- Brood-pattern analysis.
- Treatment outcome comparison.
- Inspection completion or a blocking `Complete inspection` action.
- Bulk `mark all pending skipped` convenience action.
- Side-to-side continuity across inspections.
- Detail photos, retakes, or more than two photos per observed frame.
- Changing Varroa Photo Analysis confidence policy or Advisor evidence eligibility.
- Changing Training Data Collection workflow beyond preserving existing photo intake compatibility.

## Acceptance Criteria

- [ ] Hive Configuration supports an editable brood slot count with sensible defaulting where current hive type data allows it.
- [ ] Hive Frame Slots are created, archived, and reactivated without losing historical observations or photos.
- [ ] Varroa Assessment inspections expose one Inspection Frame Observation for every active brood slot and historical inactive brood slot.
- [ ] Active brood observations start `pending`; inactive brood observations start `inactive`.
- [ ] A Beekeeper can mark active observations `inspected` or `skipped`.
- [ ] Marking `inspected` requires an explicit continuity answer.
- [ ] `skipped` and `inactive` observations record continuity as `not_continuous_or_unknown`.
- [ ] Photos can attach only to `inspected` observations.
- [ ] One observed frame can have no photos, one unknown-side photo, one side A photo, one side B photo, or side A plus side B.
- [ ] Unknown-side photos cannot coexist with side A or side B photos.
- [ ] Duplicate side photos and more than two photos for one observation are rejected.
- [ ] Existing photo upload/listing workflows keep working when frame context is unknown or not yet applied.
- [ ] API-level BDD covers brood-slot observation creation and side-photo invariants.
- [ ] Focused Core API tests cover slot count increase/decrease/reactivation and invalid photo transitions.
- [ ] Browser acceptance covers the brood-slot coverage surface and side-photo attachment path.
- [ ] Postgres migration and restart persistence verification are completed before closeout.
- [ ] `pnpm verify:slice` passes before implementation closeout.

## Open Questions

- Should Slice 0036 include a minimal route to edit brood slot count after hive creation, or only support it through the existing Hive Configuration edit surface if one exists?
- Should legacy uploaded photos be assignable to an Inspection Frame Observation after upload in the first implementation, or only at upload time?
- Should the Web UI show inactive historical slots in the main brood grid or in a collapsed historical section?
- Should API-level BDD be added to the shared acceptance catalogue for both Core API and future Web binding, or start API-bound only with browser-specific Playwright coverage?
