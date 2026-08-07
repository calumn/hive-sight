# Vertical Slice 0032: Photo-Visible Varroa Evidence Summary Catalogue Migration

Status: implemented; focused catalogue/API BDD checks and full `pnpm verify:slice` passed on 2026-08-07.

## Purpose

Move the current Photo-visible Varroa evidence summary acceptance behaviour out of legacy slice-history Gherkin and into the living capability-based acceptance catalogue.

This slice does not change the Varroa evidence summary product behaviour. It makes the current API-level behaviour easier to find, easier to report, and closer to the frame-level mite-count and HiveSight Advisor treatment-advice path.

## Source Inputs

- `architecture/acceptance-catalogue-inventory.md`: names Photo visible Varroa evidence summary as the next recommended migration candidate.
- `architecture/vertical-slice-0026-frame-level-varroa-result-summary.md`: historical accepted behaviour and implementation evidence.
- `services/core-api/tests/features/vertical_slice_0026_photo_visible_varroa_evidence_summary.feature`: pre-migration legacy executable scenarios.
- `services/core-api/tests/test_vertical_slice_0026_bdd.py`: pre-migration Core API BDD binding.
- `acceptance/features/varroa/visible-varroa-review-outcome.feature`: existing canonical Varroa feature style.
- `scripts/verify-slice.mjs`: acceptance-catalogue report configuration.
- `sdlc-delivery-acceptance-bdd`: client-neutral feature and seam-label guidance.

## Signed-Off Acceptance Scenarios

Accepted for canonical catalogue placement on 2026-08-07. These are copied from the existing Slice 0026 living behaviour and only reframed for canonical catalogue placement.

```gherkin
@api
Feature: Photo-visible Varroa evidence summary

  Scenario: Dataset Curator sees a photo-visible result from reviewed bee outcomes
    Given a Training Data Collection Inspection Photo has completed Training Crops
    And eligible complete bees on those crops have Varroa Review Outcomes
    When the Dataset Curator opens the Varroa Review stage
    Then HiveSight reports reviewed bee count, visible-Varroa bee count, visible mite marker count, active negative count, not-determined count, unreviewed eligible count, and ineligible bee count
    And HiveSight shows review completion and determinate Varroa coverage
    And HiveSight labels the result as photo-visible evidence, not a treatment recommendation

  Scenario: Visible mite marker count is separated from bee-positive count
    Given one reviewed bee has two Varroa markers
    And another reviewed bee has no visible Varroa
    When HiveSight calculates the photo-visible Varroa evidence summary
    Then HiveSight reports one visible-Varroa bee
    And HiveSight reports two visible mite markers
    And HiveSight does not treat marker count and positive bee count as the same measure

  Scenario: Unresolved or unreviewed bees reduce coverage
    Given a photo has eligible complete bees without determinate Varroa outcomes
    When HiveSight calculates the photo-visible Varroa evidence summary
    Then HiveSight includes those bees in the eligible denominator
    And HiveSight reports review completion and determinate Varroa coverage below 100%
    And HiveSight shows a coverage warning

  Scenario: Ineligible bees are excluded from the visible Varroa denominator
    Given a photo has partial visible bees or bees with unreliable orientation
    When HiveSight calculates the photo-visible Varroa evidence summary
    Then HiveSight reports them as ineligible or not assessed for Varroa
    And HiveSight excludes them from the eligible complete-bee denominator
    And HiveSight keeps their count visible in the evidence breakdown

  Scenario: Unfinished crops are disclosed but not counted
    Given a Training Data Collection Inspection Photo has one completed Training Crop
    And the same photo has one unfinished Training Crop
    When HiveSight calculates the photo-visible Varroa evidence summary
    Then HiveSight includes the completed crop in the evidence counts
    And HiveSight excludes the unfinished crop from bee, marker, positive, negative, and coverage counts
    And HiveSight shows that one unfinished crop was not included

  Scenario: Advisor context is available only as evidence, not advice
    Given a photo has a photo-visible Varroa evidence summary with at least one determinate eligible bee outcome
    When an integration client checks whether Advisor-ready Varroa context exists
    Then HiveSight reports that Varroa evidence context is available with caveats
    And HiveSight does not produce a treatment recommendation
```

## User Path

Given a maintainer or product reviewer wants the current photo-visible Varroa evidence summary behaviour,
when they inspect the living acceptance catalogue or run slice verification,
then they can find and execute the summary behaviour under the Varroa capability rather than under a historical slice number.

## Preconditions

- Slice 0031 acceptance inventory exists and identifies this as the next migration candidate.
- The existing Slice 0026 API-level BDD scenarios pass before migration.
- The migrated feature remains API-only and is tagged `@api`.
- No browser BDD binding is created in this slice because the existing browser acceptance coverage for Varroa image interaction is deliberately browser-specific.

## End-To-End Behaviour

Create the canonical feature at:

```text
acceptance/features/varroa/photo-visible-varroa-evidence-summary.feature
```

The canonical feature contains the signed-off Slice 0026 scenarios, tagged `@api`.

Rename or replace the Core API binding so its name is capability-based rather than slice-numbered:

```text
services/core-api/tests/test_photo_visible_varroa_evidence_summary_api_bdd.py
```

The binding executes the canonical feature through the existing Core API test application. The old Slice 0026 feature file is no longer executed as the living specification. The Slice 0026 architecture document remains historical delivery evidence.

`pnpm verify:slice` adds this feature to `Acceptance catalogue - Core API` and to the BDD Feature Area Summary as its own Varroa feature area.

Update `architecture/acceptance-catalogue-inventory.md` so the migrated feature moves from Legacy Core API Gherkin into Canonical Acceptance Catalogue.

## Layers Touched

- Web UI: not touched.
- Core API: no product API changes; Core API BDD binding is moved to the canonical feature.
- Analysis Service: not touched.
- Storage: not touched.
- Queue or async boundary: not touched.
- Contracts: no external API contract shape changes.
- Observability: slice verification report includes Photo-visible Varroa evidence summary as a BDD feature area.
- Documentation: update the acceptance inventory, Slice 0032 status, roadmap/observations if implementation completes.

## Test Seams

- Seam: canonical Gherkin catalogue
- Behaviour verified: Photo-visible Varroa evidence summary exists under `acceptance/features/varroa` and is tagged `@api`.
- Test style: catalogue inventory/label guard.

- Seam: Core API acceptance binding
- Behaviour verified: the six signed-off summary scenarios execute through the Core API from the canonical feature file.
- Test style: API-level `pytest-bdd`.

- Seam: slice verification reporting
- Behaviour verified: `pnpm verify:slice` reports selected, run, complete, failed, and skipped counts for the migrated feature area.
- Test style: full slice verification report.

## Data Shape

No product data shape changes.

Delivery-test assets changed by this slice:

- canonical Varroa feature file for Photo-visible Varroa evidence summary;
- capability-named Core API BDD binding;
- acceptance-catalogue inventory rows;
- slice verification BDD area metadata.

## Out Of Scope

- Changing the Photo-visible Varroa evidence summary API response.
- Changing Varroa Review Outcome calculation rules.
- Adding browser BDD coverage for the summary card.
- Migrating Slice 0027 Varroa detector adapter scenarios.
- Migrating older dataset, inspection, model, or review queue legacy features.
- Deleting historical slice architecture documents.
- Calling HiveSight Advisor or changing treatment recommendation behaviour.

## Acceptance Criteria

- [x] The signed-off Photo-visible Varroa evidence summary scenarios exist once in `acceptance/features/varroa/photo-visible-varroa-evidence-summary.feature`.
- [x] The canonical feature is tagged `@api` and uses client-neutral domain language.
- [x] The Core API BDD binding executes the canonical feature from a capability-named test module.
- [x] The legacy Slice 0026 feature file is no longer the living executable specification.
- [x] Focused catalogue guard tests pass.
- [x] `pnpm verify:slice` reports the migrated feature under `Acceptance catalogue - Core API` and in the BDD Feature Area Summary.
- [x] `architecture/acceptance-catalogue-inventory.md` records the feature as canonical and removes its `migrate now` status from the legacy section.
- [x] Slice 0026 remains historical delivery evidence and is not rewritten as the current catalogue.

## Open Questions

None blocking design signoff.

The only intended decision is whether the six existing Slice 0026 scenarios are accepted as-is for canonical catalogue placement. If the wording needs tightening, change it before implementation rather than migrating and rewording in one move.
