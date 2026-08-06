# HiveSight Advisor Alignment: Dual-Seam Acceptance Specification Pattern

Date: 2026-08-06
Source: HiveSight Slice 0030 Dual-Seam Acceptance Specification Pilot

## Purpose

HiveSight has proved a narrow acceptance-testing pattern that may be useful for HiveSight Advisor as the two projects begin sharing treatment-advice workflows.

The goal is not to make every test Gherkin, and not to force every scenario through every client. The goal is to keep important cross-client behaviours described once in client-neutral domain language, then execute that same behaviour through whichever technical seams matter.

## What HiveSight Implemented

HiveSight now has one canonical feature file:

```text
acceptance/features/varroa/visible-varroa-review-outcome.feature
```

The same feature executes through:

- Core API binding: `pytest-bdd`
- Web UI binding: `playwright-bdd`

The Gherkin does not mention HTTP methods, routes, button labels, selectors, or database tables. Those details live in seam-specific step bindings.

## Proven Example

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

This scenario is executable through both HiveSight's API and browser. It replaced a drifted pair of tests where the API side asserted two markers and the browser side asserted one.

## Recommended Shared Rule

For cross-project behaviours between HiveSight and HiveSight Advisor:

- Put living product behaviours in capability-organised feature files.
- Keep feature text client-neutral and domain-led.
- Bind the same feature through API, browser, service, or adapter seams only where each seam adds real confidence.
- Keep API contract tests, low-level tests, and browser-only visual tests separate.
- Keep historical slice documents as signoff evidence, not as the living executable catalogue.

## What This Means For Advisor

Advisor does not need to copy HiveSight's exact runner setup. It should align on the principles:

- Gherkin describes the behaviour in terms the product owner can review.
- Technical bindings prove that behaviour at the relevant seam.
- Cross-repo treatment-advice behaviours should use comparable language so the two projects do not drift.

For the treatment-advice integration, likely shared acceptance areas are:

- HiveSight requests treatment advice from Advisor using a treatment-relevant Varroa context.
- Advisor returns a treatment recommendation with a durable answer identifier and contract version.
- HiveSight records the recommendation as part of a Treatment Evidence Chain.
- A beekeeper accepts or declines the recommendation without rewriting the original advice.
- Later treatment completion and follow-up evidence can be related back to the original recommendation.

## Open Alignment Questions For Advisor

- Which Advisor behaviours should become canonical Gherkin scenarios rather than API-only contract tests?
- What endpoint and response fields should Advisor expose for treatment recommendation intake and replayable evidence?
- What stable `advisor_answer_id` and `contract_version` format should HiveSight store?
- Which scenarios should run in both repos, and which should remain repo-local?

## Verification Result From HiveSight Pilot

HiveSight `pnpm verify:slice` now reports the shared feature separately:

- `Shared Gherkin pilot - Core API`: passed
- `Shared Gherkin pilot - Web UI`: passed

The full Slice 0030 verification also passed Core API tests, Analysis Service tests, Web TypeScript checks, dev-script tests, and the existing browser acceptance suite.
