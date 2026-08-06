# Vertical Slice 0030: Dual-Seam Acceptance Specification Pilot

Status: designed; Gherkin acceptance signed off 2026-08-06.

## Purpose

Prove that one client-neutral Gherkin feature can be the living acceptance specification for a HiveSight behaviour and can execute through both the Core API and the Web UI.

The pilot migrates one current Varroa Review behaviour rather than attempting a broad test reorganisation. It establishes the catalogue, runner, reporting, and historical-document rules needed for later capability-by-capability migration.

## Source Inputs

- `requirements/product-spec.md`: product-facing Gherkin and testing strategy.
- `requirements/acceptance-criteria.md`: API-level BDD, browser acceptance, and slice-verification evidence.
- `architecture/vertical-slice-0025-varroa-review-outcome-labelling.md`: accepted historical source of the selected behaviour.
- `architecture/parking-lot.md`: PARK-0001 UI-Level Gherkin Harness.
- `sdlc-delivery-acceptance-bdd`, `sdlc-delivery-acceptance-scenario-signoff`, and `sdlc-delivery-test-automation-reporting`: delivery rules.

## Signed-Off Acceptance Scenario

```gherkin
Feature: Varroa review outcome

  Scenario: Dataset Curator records visible Varroa evidence with two mite markers
    Given a Dataset Curator has opened an eligible bee for Varroa review
    When the Dataset Curator records visible Varroa with two mite markers
    Then HiveSight preserves a visible-Varroa review outcome for that bee
    And HiveSight preserves two mite markers for that bee
    And HiveSight reports one visible-Varroa bee and two visible Varroa markers
    And HiveSight shows the saved markers when the review is reopened
```

## User Path

Given a Dataset Curator has opened an eligible bee for Varroa review,
when they record visible Varroa with two mite markers,
then the same observed outcome is proven through both the Core API and the browser without the specification naming HTTP, controls, selectors, or storage internals.

## Preconditions

- The existing Core API `pytest-bdd` lane remains available.
- The existing stub Playwright profile remains available and deterministic.
- The browser binding uses a maintained Gherkin-to-Playwright bridge while retaining native Playwright execution, reporting, traces, screenshots, and live-API profile support.
- Slice 0025 remains historical delivery evidence; its document is not rewritten as a living test catalogue.

## End-To-End Behaviour

Create the canonical feature at:

```text
acceptance/features/varroa/visible-varroa-review-outcome.feature
```

The exact signed-off scenario above is the only living specification for this pilot behaviour. Core API bindings execute it through HTTP against the existing test application. Browser bindings execute the same feature through the actual Web UI in Chromium using `playwright-bdd`.

The existing Slice 0025 API feature stops executing the migrated scenario but keeps its other scenarios. The existing Slice 0025 browser specification is reduced to browser-specific visual and interaction coverage: paired image rendering, zoom and pan, source-crop context, overlay placement, and marker-containment behaviour. It no longer makes a competing one-marker business-outcome claim.

`pnpm verify:slice` reports the API and browser executions as separate checks. Both run in their current deterministic default lanes; live Postgres/browser verification remains an additional persistence-confidence path, not a second mandatory execution of the shared feature.

## Layers Touched

- Web UI: add `playwright-bdd`, configure the shared feature location, implement browser step bindings, and retain focused visual regression coverage.
- Core API: point `pytest-bdd` bindings to the shared feature and remove the duplicate legacy scenario binding.
- Analysis Service: Not touched.
- Storage: Not touched.
- Queue or async boundary: Not touched.
- Contracts: Not touched; API and event contract testing remain a separate future work package.
- Observability: label API and browser shared-feature execution separately in slice verification output.
- Delivery skills: update generic BDD guidance and the skills index with the client-neutral, canonical-feature, dual-seam rules.

## Test Seams

- Seam: canonical Gherkin feature discovery
- Behaviour verified: the API and browser bindings reference the same capability-organised `.feature` file.
- Test style: focused catalogue/runner guard.

- Seam: Core API acceptance binding
- Behaviour verified: an eligible bee can retain a visible-Varroa outcome with exactly two markers and shows that saved evidence on reopen.
- Test style: API-level `pytest-bdd`.

- Seam: browser acceptance binding
- Behaviour verified: a Dataset Curator performs the same signed-off behaviour through the Web UI and sees the same saved counts and markers on reopen.
- Test style: browser-level `playwright-bdd` in Chromium.

- Seam: visual Varroa Review interaction
- Behaviour verified: browser-only image, zoom, pan, source-context, overlay, and placement-containment behaviour remains protected without duplicating the business outcome scenario.
- Test style: focused Playwright regression tests.

## Data Shape

No product data shape changes.

Delivery-test assets introduced by this slice:

- canonical feature path and capability directory;
- API and browser binding modules;
- browser Gherkin runner configuration;
- verification-report labels for each execution seam.

## Out Of Scope

- Migrating all historic Gherkin or browser acceptance tests.
- Creating a complete API, OpenAPI, event-schema, or Advisor contract-test suite.
- Replacing lower-level workflow, persistence, authorisation, or visual regression tests with Gherkin.
- Requiring every future scenario to run through both seams when it is meaningfully API-only or browser-only.
- Production behaviour, product data, migrations, or Advisor integration changes.

## Acceptance Criteria

- [ ] The signed-off Varroa Review scenario exists once in a capability-organised canonical feature file.
- [ ] The feature contains no HTTP method, button, selector, route, or storage wording.
- [ ] `pytest-bdd` executes the canonical feature through the Core API.
- [ ] `playwright-bdd` executes the same canonical feature through the Web UI.
- [ ] Both bindings prove two markers, one visible-Varroa bee, and saved marker visibility after reopening.
- [ ] The legacy Slice 0025 browser test retains browser-specific visual/interaction checks but no competing one-marker outcome assertion.
- [ ] Slice 0025 remains historical acceptance evidence and links to the living canonical feature.
- [ ] `pnpm verify:slice` reports distinct API and browser results for the shared feature.
- [ ] The generic BDD skill and skills index record the new client-neutral, dual-seam practice without HiveSight-specific wording.
- [ ] Focused API and browser checks, Web type-check, and `pnpm verify:slice` pass.

## Open Questions

None blocking implementation.

Follow-on migration order remains a human prioritisation decision after this pilot has demonstrated maintenance cost and reporting quality.
