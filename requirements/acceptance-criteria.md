# Acceptance Criteria

Acceptance criteria are provisional and will be refined as requirements are reviewed.

## Apiary and Hive Management

- A user can create an apiary with a name.
- A user can create a hive associated with an apiary.
- A user can view hives grouped by apiary.

## Inspection Events

- A user can create an inspection event for a selected hive.
- An inspection event records at least the hive, date, and associated photos.
- A user can return to an inspection and see its uploaded photos and analysis status.

## Photo Upload and Association

- A user can upload one or more photos to an inspection event.
- The system preserves the association between each photo and its inspection.
- The system supports multiple photos for the same inspection.
- The system can distinguish, or later allow the user to distinguish, photos that belong to the same frame.

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

- The system calculates a visible Varroa estimate as likely Varroa detections associated with complete visible bees per 100 estimated complete visible bees.
- The system reports likely Varroa detections associated with partial bees or unassociated visible Varroa as additional evidence.
- The system presents an inspection-level estimate when multiple photos are associated with the inspection.
- The system clearly indicates when the estimate is based on limited or low-confidence image data.
- The system clearly states that the estimate is based only on bees visible in uploaded photos.

## Photo And Annotation Storage

- The system stores the original uploaded photo.
- The system stores structured annotation data for detected bees, likely Varroa detections, and user corrections.
- The system can render a tagged-up image from the original photo and stored annotation data.

## Web UI

- A user can complete the first workflow in a browser: create apiary, create hive, create inspection, upload photos, view analysis results.

## Ownership And Permissions

- In version one, apiaries, hives, inspections, photos, analysis results, annotations, and corrections are owned by a single user account or simple account boundary.
- The system prevents one user from viewing or modifying another user's apiaries, hives, inspections, photos, analysis results, annotations, or corrections.

## Upload And Storage

- The system accepts configurable image formats and upload size limits.
- The system preserves original uploaded photos.
- The system records when an upload is rejected because of unsupported format, excessive size, or unsuitable image evidence.

## Consent For Model Improvement

- The system does not automatically use uploaded photos or corrections for model improvement.
- The system records consent status before photos or corrections become eligible for training, validation, or benchmark review.
- The exact consent capture flow may be deferred, but consent eligibility must be traceable at photo or inspection level.

## Traceability and AI-SDLC Evidence

- Each approved requirement has a unique ID.
- Each approved requirement has at least one source or rationale.
- Each approved requirement has acceptance criteria or an explicit reason why criteria are deferred.
- AI-generated requirements contributions are recorded in the AI-SDLC observation log.
