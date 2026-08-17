# Acceptance Criteria

Acceptance criteria are provisional and will be refined as requirements are reviewed.

Implementation traceability note: the Varroa Detection and Infection-Rate Estimate criteria describe the product target. As of Slice 0013, implemented slices have proven bee annotation, dataset foundations, and bee-detector training preparation only; real Varroa detection and Varroa-rate calculation remain future functional/model work.

## Apiary and Hive Management

- A registered User receives a default Workspace and owner Workspace Membership during onboarding.
- A User acting as the primary Beekeeper can create an apiary with a name.
- A User acting as the primary Beekeeper can create a hive associated with an apiary.
- A User acting as the primary Beekeeper can view hives grouped by apiary.

## Inspections

- A User acting as the primary Beekeeper can create an inspection for a selected hive.
- An inspection records at least the hive, date, and associated photos.
- A user can return to an inspection and see its uploaded photos and analysis status.

## Photo Upload and Association

- A person must be registered as a User before uploading an inspection photo.
- A registered User must be logged in before uploading an inspection photo.
- The logged-in User must have an active Workspace Membership for the Workspace that owns the inspection.
- The Workspace must have an accepted Workspace Data Use Agreement before upload is allowed.
- A User acting as the primary Beekeeper can upload one or more photos to an inspection.
- The system preserves the association between each photo and its inspection.
- The system supports multiple photos for the same inspection.
- The system can distinguish, or later allow the user to distinguish, photos that belong to the same Hive Frame Slot, Inspection Frame Observation, and frame side.

## Bee Counting

- For each submitted photo, the system produces an estimated complete visible bee count.
- For each submitted photo, the system reports partial visible bees separately where possible.
- The bee count is stored with the image analysis result.
- The user can see the bee count for each analysed image.
- The user can optionally view detected bee markers on the image.

## Varroa Detection

- For each submitted photo, the system produces an estimated count of likely visible Varroa mites on bees.
- The Varroa count is stored with the image analysis result.
- The user can see the Varroa count for each analysed image.
- The system presents results as AI-assisted estimates, not guaranteed diagnoses.
- The user can view tagged-up photos showing likely Varroa detections.
- The user can mark a likely Varroa detection as incorrect.
- The user can mark a missed likely Varroa location.

## Infection-Rate Estimate

- When model and methodology promotion gates are met, the system calculates a photo-visible Varroa estimate as likely Varroa detections associated with eligible complete visible bees per 100 eligible complete visible bees in a declared reconciled frame population.
- The system reports likely Varroa detections associated with partial bees or unassociated visible Varroa as additional evidence.
- A sampled estimate identifies its Varroa Sampling Plan, achieved coverage, and uncertainty; an inadequate result is suppressed rather than shown as a precise rate.
- The system does not aggregate potentially overlapping photos of the same frame into an inspection-level rate without source-frame reconciliation.
- The system clearly indicates when the estimate is based on limited or low-confidence image data.
- The system clearly states that the estimate is based only on bees visible in uploaded photos.

## Photo And Annotation Storage

- The system stores the original uploaded photo.
- The system stores structured annotation data for detected bees, likely Varroa detections, and user corrections.
- The system can render a tagged-up image from the original photo and stored annotation data.

## Web UI

- A user can complete the first workflow in a browser: create apiary, create hive, create inspection, upload photos, view analysis results.
- Browser acceptance tests can exercise implemented Web UI workflows through the same visible path a Beekeeper uses.
- Browser acceptance tests verify that visual evidence views render the uploaded photo and annotation overlays well enough to detect broken or misaligned evidence rendering.

## Test Evidence And Slice Verification

- A developer can run one slice verification command from the command line before closing a slice.
- The slice verification report records the service tests, API-level BDD scenarios, Web TypeScript checks, and browser acceptance tests that were executed.
- The slice verification report records pass/fail status, commands run, concise summaries, and failure artifact locations where available.
- The slice verification report does not claim formal code coverage percentages unless separate coverage tooling is added.
- Slice 0030 establishes a limited shared Gherkin pilot: one client-neutral feature runs through API and browser bindings. Plain Playwright remains the browser-acceptance default for un-migrated workflows, and broader migration remains a future prioritisation decision.

## Ownership And Permissions

- In version one, apiaries, hives, inspections, photos, analysis results, annotations, and corrections are owned by a Workspace.
- User access to a Workspace is authorized through Workspace Membership.
- Version one creates one owner Workspace Membership for the registered User and does not expose invitations or non-owner roles.
- The system prevents a User without the relevant Workspace Membership from viewing or modifying another Workspace's apiaries, hives, inspections, photos, analysis results, annotations, or corrections.

## Upload And Storage

- The system accepts configurable image formats and upload size limits.
- The system preserves original uploaded photos.
- The system records when an upload is rejected because of unsupported format, excessive size, or unsuitable image evidence.

## Workspace Data Use Agreement And Model Improvement

- The system does not automatically use uploaded photos or corrections for model improvement.
- The Workspace owner must accept the Workspace Data Use Agreement before upload and analysis features can be used.
- The system records Workspace Data Use Agreement status and terms version before photos or corrections become eligible for training, validation, or benchmark review.
- Workspace Data Use Agreement eligibility must be traceable through the Workspace boundary.

## Traceability and AI-SDLC Evidence

- Each approved requirement has a unique ID.
- Each approved requirement has at least one source or rationale.
- Each approved requirement has acceptance criteria or an explicit reason why criteria are deferred.
- AI-generated requirements contributions are recorded in the AI-SDLC observation log.
