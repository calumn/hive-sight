# Vertical Slice 0009.5: Ellipse Annotation Usability Controls

## Purpose

Improve the Training Crop annotation UI so a Dataset Curator can accurately fit oriented bee ellipses well enough for future training data use.

Slice 9 proved the core Training Crop and oriented ellipse workflow. This slice makes that workflow usable for real annotation work by placing the controls next to the crop being edited and completing the basic movement, rotation, and radius controls.

## Source Inputs

- `CONTEXT.md`
- `architecture/vertical-slice-0009-training-crop-ellipse-annotation.md`
- `architecture/adr/0002-oriented-ellipse-canonical-bee-annotations.md`

## User Path

Given a Dataset Curator is editing an unlocked Training Crop with an oriented bee ellipse
When the Dataset Curator adjusts the ellipse geometry
Then the UI supports movement, rotation, and radius adjustment in both directions
And the controls remain visually adjacent to the crop image being edited.

## Preconditions

- User is logged in.
- User has active Workspace Membership for the source Inspection Photo's Workspace.
- User has dataset curator capability.
- Workspace Data Use Agreement is accepted.
- Source Inspection has intent `training_data_collection`.
- Source Inspection Photo has been uploaded.
- Training Crop exists and is not `review_complete` or `excluded`.
- At least one oriented bee ellipse exists before ellipse controls are enabled.

## End-To-End Behaviour

The Dataset Curator opens the Training Crop annotation panel, selects a source photo, selects or creates a Training Crop, and creates an oriented bee ellipse.

The crop image and the active ellipse controls are presented together so the curator does not need to visually jump past unrelated status text, metric cards, or explanatory copy while adjusting the bee. The controls should be directly next to, immediately below, or otherwise visually attached to the crop surface depending on viewport size.

Layout rule:

- On wide desktop/tablet viewports, show the crop surface and active ellipse controls side-by-side.
- On narrow/mobile viewports, show the crop surface first and the active ellipse controls immediately below it.
- Move metric/status content below the combined crop editing tool so it does not sit between the image and the controls.

For the selected ellipse, the Dataset Curator can:

- nudge left by 5 px
- nudge right by 5 px
- nudge up by 5 px
- nudge down by 5 px
- rotate clockwise by 5 degrees
- rotate anti-clockwise by 5 degrees
- reduce horizontal radius by 5 px
- increase horizontal radius by 5 px
- reduce vertical radius by 5 px
- increase vertical radius by 5 px
- change annotation type between `complete_visible_bee` and `partial_visible_bee`
- delete the selected ellipse

This slice remains button-based. It does not introduce direct drag editing, resize handles, keyboard shortcuts, zoom, or pan.

The UI should show compact read-only geometry values for the selected ellipse:

- center x
- center y
- radius x
- radius y
- rotation degrees

These values support precision annotation and browser acceptance assertions, but are not editable text fields in this slice.

The UI should disable obviously invalid adjustment buttons before calling the API:

- Radius values cannot be reduced below 5 px.
- Movement buttons are disabled if the next 5 px nudge would move the rotated ellipse outside the crop bounds.
- Radius growth buttons are disabled if the next 5 px growth would move the rotated ellipse outside the crop bounds.
- Rotation buttons are disabled if the next 5 degree rotation would move the rotated ellipse outside the crop bounds.

The API remains the source of truth for geometry validation.

The UI continues to call the existing Training Crop ellipse update API. If the API rejects an adjustment because the ellipse would move outside crop bounds, the UI surfaces the existing API error and keeps the last valid ellipse state.

Terminal Training Crops remain locked. The UI must keep adjustment controls disabled when the selected crop is `review_complete` or `excluded`.

## Layers Touched

- Web UI: improve Training Crop annotation layout and add missing ellipse adjustment controls.
- Core API: not touched.
- Analysis Service: not touched.
- Storage: not touched.
- Queue or async boundary: not touched.
- Contracts: not touched.
- Observability: not touched beyond existing API error display.

## Test Seams

- Seam: Web UI
- Behaviour verified: selected ellipse can be nudged left, right, up, and down.
- Test style: Playwright browser acceptance.

- Seam: Web UI
- Behaviour verified: selected ellipse can be rotated clockwise and anti-clockwise.
- Test style: Playwright browser acceptance.

- Seam: Web UI
- Behaviour verified: selected ellipse radius can be adjusted on both axes in both directions.
- Test style: Playwright browser acceptance.

- Seam: Web UI
- Behaviour verified: controls are rendered adjacent to the crop surface rather than separated by metric/status content.
- Test style: Playwright browser acceptance using stable test hooks and visibility/order assertions.

- Seam: Web UI
- Behaviour verified: visible read-only geometry values change by the expected increment after each control action.
- Test style: Playwright browser acceptance.

- Seam: Web TypeScript
- Behaviour verified: UI code remains type-safe against existing Training Crop API contracts.
- Test style: `pnpm --filter @hive-sight/web check`.

API-level BDD is not added in this slice because the API contract and domain semantics are unchanged from Slice 9.

## Data Shape

No API or persistence data shape changes.

Existing `Oriented Bee Ellipse` fields remain:

- center x
- center y
- radius x
- radius y
- rotation degrees
- annotation type
- coordinate space

Existing geometry increments remain:

- movement: 5 px
- radius: 5 px
- rotation: 5 degrees

UI-side geometry constraints:

- minimum `radius_x`: 5 px
- minimum `radius_y`: 5 px
- invalid next-step movement, radius growth, or rotation controls are disabled where the UI can calculate the rotated ellipse bounds cleanly
- API validation remains final

## Out Of Scope

- API contract changes.
- New Training Crop states.
- Drag handles.
- Direct mouse/touch drag editing.
- Keyboard shortcuts.
- Zoom and pan.
- Snap-to-bee or model-assisted refinement.
- Bulk ellipse editing.
- Dataset export.
- Bee Annotation Repository.
- Model training.
- Reopen workflow for completed or excluded crops.

## Acceptance Criteria

- [ ] The selected Training Crop image and its ellipse controls are visually adjacent in the UI.
- [ ] Metric/status text no longer sits between the crop image and the active ellipse controls.
- [ ] A Dataset Curator can nudge a selected ellipse left by 5 px.
- [ ] A Dataset Curator can nudge a selected ellipse right by 5 px.
- [ ] A Dataset Curator can nudge a selected ellipse up by 5 px.
- [ ] A Dataset Curator can nudge a selected ellipse down by 5 px.
- [ ] A Dataset Curator can rotate a selected ellipse clockwise by 5 degrees.
- [ ] A Dataset Curator can rotate a selected ellipse anti-clockwise by 5 degrees.
- [ ] A Dataset Curator can increase and reduce horizontal radius in 5 px increments.
- [ ] A Dataset Curator can increase and reduce vertical radius in 5 px increments.
- [ ] The selected ellipse's center, radii, and rotation are displayed as compact read-only values.
- [ ] Browser acceptance asserts exact visible geometry changes after nudge, rotation, and radius controls.
- [ ] A Dataset Curator can still switch a selected ellipse between `complete_visible_bee` and `partial_visible_bee`.
- [ ] A Dataset Curator can still delete an unlocked selected ellipse.
- [ ] Controls are disabled when the selected crop is `review_complete` or `excluded`.
- [ ] Obvious invalid controls are disabled before they would send an invalid API request.
- [ ] Radius shrink controls disable at 5 px.
- [ ] Movement, radius growth, and rotation controls disable when the next increment would place the rotated ellipse outside crop bounds.
- [ ] Existing API validation still prevents an ellipse from being moved or resized outside crop bounds.
- [ ] Existing Slice 9 crop completion workflow still works after the layout change.
- [ ] Browser acceptance covers the added movement, rotation, radius, and control-placement behaviours.
- [ ] No API-level BDD scenarios are added because the slice is UI-only.
- [ ] `pnpm verify:slice` passes.

## Open Questions

- Should keyboard shortcuts be added in a later annotation-productivity slice?
- Should zoom and pan be the next usability improvement after complete button controls?
- Should direct drag handles replace or supplement button controls once the underlying workflow is stable?
