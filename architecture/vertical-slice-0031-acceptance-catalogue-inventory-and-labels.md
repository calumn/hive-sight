# Vertical Slice 0031: Acceptance Catalogue Inventory And Labels

Status: implemented; focused catalogue guard tests and full `pnpm verify:slice` passed on 2026-08-07.

## Purpose

Make HiveSight's acceptance-test landscape explicit enough that future Gherkin migration is deliberate rather than archaeological.

This slice creates a living inventory of current acceptance-style coverage, labels each behaviour by the seam it genuinely belongs to, and adds light regression guards so canonical catalogue features cannot drift into unlabelled or misleading test evidence.

It does not migrate every historical slice test. It gives us the map needed to choose future migrations cleanly.

## Source Inputs

- `architecture/vertical-slice-0030-dual-seam-acceptance-specification-pilot.md`: established the shared acceptance-catalogue pilot.
- `architecture/hivesight-advisor-dual-seam-acceptance-alignment.md`: records the client-neutral Gherkin and seam-specific binding approach.
- `architecture/parking-lot.md`: PARK-0001 follow-on work to inventory and label active API BDD and browser acceptance tests.
- `requirements/roadmap.md`: Testing And Quality candidate `Acceptance Catalogue Inventory And Labels`.
- `sdlc-delivery-acceptance-bdd`: catalogue placement, seam choice, and scenario-writing guidance.
- `sdlc-delivery-test-automation-reporting`: verification-report honesty and summarised evidence guidance.

## Signed-Off Acceptance Scenarios

Accepted for implementation on 2026-08-07.

```gherkin
Feature: Acceptance catalogue inventory

  Scenario: Delivery maintainer inventories current acceptance coverage
    Given HiveSight has canonical catalogue features, legacy API BDD features, and browser acceptance tests
    When the delivery maintainer reviews the acceptance catalogue inventory
    Then each listed behaviour has a capability area
    And each listed behaviour has a coverage classification
    And each listed behaviour has a migration recommendation

  Scenario: Canonical catalogue features declare their supported seams
    Given HiveSight has canonical catalogue features
    When the acceptance catalogue labels are checked
    Then every canonical catalogue feature declares at least one supported seam
    And unsupported seam labels are rejected

  Scenario: Slice verification summarises catalogue execution by feature area
    Given HiveSight has canonical catalogue features with API or Web UI bindings
    When slice verification runs
    Then the verification report summarises selected, run, complete, failed, and skipped scenarios by feature area and seam
```

## User Path

Given a maintainer wants to understand which acceptance behaviours are current, historical, shared, API-only, browser-only, service-only, or lower-level,
when they open the inventory and run slice verification,
then they can see what exists now, what is intentionally left where it is, and which behaviour should be migrated next.

## Preconditions

- Slice 0030's canonical acceptance catalogue exists under `acceptance/features/<capability>/...`.
- Core API catalogue execution already filters catalogue scenarios by `@api`.
- Web UI catalogue execution already filters catalogue scenarios by `@web`.
- Legacy slice-history tests remain valid delivery evidence until a capability is deliberately migrated.

## End-To-End Behaviour

Create a durable inventory document at:

```text
architecture/acceptance-catalogue-inventory.md
```

The inventory groups current acceptance-style coverage into:

- canonical capability catalogue features;
- legacy Core API Gherkin features and bindings;
- browser BDD bindings;
- plain browser acceptance specs;
- harness and reporting guards.

Each inventory row records:

- capability area;
- behaviour name;
- current location;
- current execution seam;
- coverage classification;
- migration recommendation;
- notes for known drift risk or deliberate non-migration.

Canonical catalogue features must carry valid seam labels such as `@api` and `@web`. A focused guard checks that catalogue features are not missing seam labels and do not introduce unsupported seam labels.

`pnpm verify:slice` continues to publish the BDD Feature Area Summary so the report says, by feature area and seam, how much catalogue behaviour was selected and completed.

## Layers Touched

- Web UI: no product UI changes; browser acceptance inventory only.
- Core API: no product API changes; test harness/catalogue checks only.
- Analysis Service: not touched.
- Storage: not touched.
- Queue or async boundary: not touched.
- Contracts: not touched; no external API contract shape changes.
- Observability: verification-report summary remains explicit about BDD feature area execution.
- Documentation: add the living inventory and update roadmap/parking-lot status if implementation closes this follow-on item.

## Test Seams

- Seam: catalogue feature metadata
- Behaviour verified: every canonical feature declares at least one known supported seam.
- Test style: focused repository-level or Core API test harness guard.

- Seam: acceptance inventory document
- Behaviour verified: current acceptance-style test files are represented with capability, classification, and migration recommendation.
- Test style: lightweight inventory consistency check where practical; otherwise reviewed documentation evidence plus `pnpm verify:slice`.

- Seam: slice verification reporting
- Behaviour verified: BDD Feature Area Summary reports selected, run, complete, failed, and skipped counts by feature area and seam.
- Test style: existing `pnpm verify:slice` report generation plus focused script check if needed.

## Data Shape

No product data shape changes.

Delivery metadata introduced by this slice:

- coverage classification labels:
  - `shared`;
  - `api-only`;
  - `web-only`;
  - `service-only`;
  - `legacy historical evidence`;
  - `lower-level / do not migrate`;
- migration recommendations:
  - `migrate now`;
  - `migrate when touched`;
  - `keep as legacy evidence`;
  - `keep as browser-specific coverage`;
  - `do not migrate`.

## Out Of Scope

- Moving all historical API Gherkin features into `acceptance/features`.
- Rewriting all browser acceptance specs as Gherkin.
- Deleting legacy slice-history tests.
- Adding new product behaviour.
- Changing Advisor-facing API contracts.
- Making every canonical feature run through both API and browser seams.

## Acceptance Criteria

- [x] `architecture/acceptance-catalogue-inventory.md` lists the current canonical catalogue features.
- [x] The inventory lists current legacy Core API Gherkin features and bindings.
- [x] The inventory lists current browser BDD bindings and plain browser acceptance specs.
- [x] Each inventory row has a capability area, coverage classification, and migration recommendation.
- [x] Canonical catalogue features are guarded so they must declare at least one supported seam label.
- [x] Unsupported canonical seam labels fail a focused check.
- [x] `pnpm verify:slice` reports BDD feature-area counts by feature area and seam.
- [x] The inventory names the next recommended capability migration candidate.
- [x] Roadmap and parking-lot entries are updated to reflect the promoted/completed status of this work.

## Open Questions

None blocking design signoff.

The main implementation judgement is how much of the inventory should be machine-checked in this slice. The default should stay light: guard canonical catalogue labels now, and avoid building a heavy registry until the catalogue has more migrated behaviours.
