# Vertical Slice 0015.2: Model Candidate Crop Pre-Labelling

Status: planned.

## Purpose

Let a Dataset Curator use a completed Bee Detector Model Candidate to propose Candidate Annotations on the currently selected Training Crop, then accept, edit, or reject those proposals under human governance.

This slice turns the first successful YOLO OBB Training Run into a visible, usable pre-labelling helper. The goal is not model promotion or production inference. The goal is to learn whether the current HiveSight Bee Detector candidate can reduce crop annotation effort while preserving the separation between AI proposal and human-reviewed evidence.

## Source Inputs

- `CONTEXT.md`
- `requirements/model-requirements.md`
- `requirements/ai-assisted-annotation-and-model-training-baseline.md`
- `requirements/bee-annotation-repository-and-curriculum-training-baseline.md`
- `architecture/adr/0002-oriented-ellipse-canonical-bee-annotations.md`
- `architecture/adr/0003-postgres-for-durable-product-and-model-governance-metadata.md`
- `architecture/adr/0005-retire-grounding-dino-for-bee-candidate-annotation.md`
- `architecture/vertical-slice-0015-yolo-obb-training-baseline.md`
- `architecture/vertical-slice-0015.1-training-run-progress-and-recovery.md`
- Real local feedback from the first successful YOLO OBB Training Run.

## User Path

Given a Dataset Curator has a completed Bee Detector Training Run with a Model Candidate
And the Dataset Curator opens a Training Crop that is not yet review-complete
When the Dataset Curator clicks **Suggest bees**
Then HiveSight runs the selected Model Candidate against the Training Crop
And displays proposed bee Candidate Annotations over the crop
And the Dataset Curator can accept, edit, or reject each proposal
And accepted or edited proposals become reviewed Oriented Bee Ellipses with AI-assisted provenance.

## Preconditions

- Slice 0015 is implemented and can create a completed Bee Detector Model Candidate.
- Slice 0015.1 is implemented and Training Run failures/progress are observable.
- The active stack can run with `pnpm dev:all:yolo-training`.
- A Dataset Curator has internal dataset/model governance capability.
- Workspace Data Use Agreement is accepted.
- The selected Training Crop has retrievable image content.
- At least one completed Bee Detector Model Candidate exists for the Workspace.
- Candidate Annotations remain untrusted until reviewed by a human.

## End-To-End Behaviour

The Dataset Curator opens the existing Training Crop editor. The editor shows the selected crop and its current reviewed ellipses.

If a completed Bee Detector Model Candidate exists, the UI shows a compact **Suggest bees** action near the crop editing controls. The UI defaults to the latest completed Bee Detector Model Candidate in the Workspace and shows it clearly, for example `Using HS-MC-000001`. If more than one completed candidate exists, the UI includes a simple selector while still defaulting to the latest candidate.

**Suggest bees** is available only while the crop is editable. If a crop is `review_complete` or `excluded`, the curator must reopen the crop before asking for suggestions.

When the curator clicks **Suggest bees**, the Web UI calls the Core API with:

- `workspace_id`
- `training_crop_id`
- selected `model_candidate_id`, optional for latest eligible candidate
- optional confidence threshold, defaulting to `0.10`

The Core API:

- verifies Dataset Curator capability
- verifies the Training Crop belongs to the Workspace
- verifies the Model Candidate belongs to the Workspace
- verifies the Model Candidate was created by a completed Bee Detector Training Run
- blocks suggestions if the selected crop's Dataset Item was included in the selected Model Candidate's own frozen Dataset Version
- loads the crop image bytes through the existing Source Image / Inspection Photo content path
- runs the model through a replaceable `BeeDetectorInferenceAdapter`
- converts model-specific YOLO OBB predictions into HiveSight Candidate Annotation geometry
- returns Candidate Annotations sorted by confidence descending, capped initially at 50 suggestions, without writing them as reviewed evidence

The UI overlays Candidate Annotations differently from reviewed ellipses. Candidate overlays should be visually distinct and labelled as proposals, not facts.

For each Candidate Annotation, the curator can:

- accept as a complete visible bee
- accept as a partial visible bee
- edit geometry and then accept
- reject

Accepted or edited proposals are persisted as canonical Oriented Bee Ellipses on the Training Crop. Their Annotation Source records that the proposal came from a `model_candidate`, and their Review Method records that they were `human_reviewed_candidate`. The persisted provenance also records the Model Candidate id, the original candidate confidence, the inference threshold, the raw YOLO OBB geometry, and whether the proposal was accepted unchanged or accepted with edits.

Rejected proposals remain transient in this slice. Rejection removes the suggestion from the crop editor and creates no reviewed evidence. Durable rejected-candidate history is parked for a later Candidate Annotation audit workflow.

The curator can still draw human-from-scratch ellipses in the same editor. Human-from-scratch ellipses must remain distinguishable from model-assisted ellipses in Dataset Version reports.

## Governance Decisions Embedded In The Slice

### Candidate Annotation Is Not Ground Truth

Model output is a Candidate Annotation only. It is not a Reviewed Annotation, Dataset Item, ground truth, or model-quality claim until a human has accepted or corrected it.

### Human Review Boundary

The accept/edit action is the trust boundary. The model may propose geometry and class, but the curator is responsible for the final reviewed ellipse.

### Automation Bias Visibility

Accepted model-assisted ellipses must be traceable as `human_reviewed_candidate`, not silently mixed with `human_from_scratch`. Future Dataset Versions and reports must be able to show how much of the training data came from model-assisted review.

### Crop-Level First

This slice runs inference on one Training Crop at a time. Full source-photo or full-frame pre-labelling is deliberately deferred until crop-level behaviour is understandable and the first model has enough useful signal.

### Latest Candidate Is A Convenience, Not Approval

Using the latest completed Model Candidate is a local curator convenience. It does not mean the candidate is approved, promoted, benchmarked, or user-facing.

### Self-Dataset Suggestion Block

Candidate suggestions are blocked when the selected Training Crop's Dataset Item appears in the selected Model Candidate's own Dataset Version.

This is stricter than necessary for annotation assistance, but it prevents the early habit of judging model usefulness on crops the model has already seen. Unassigned crops are allowed, and later Dataset Item assignments do not retroactively block older Model Candidates unless the Dataset Item id is actually present in that candidate's frozen Dataset Version.

### Bee Class Handling

YOLO may return class labels, but Slice 0015.2 treats the Bee Detector primarily as a geometry suggester. Suggestions default to `complete_visible_bee` for acceptance, and the curator can accept as `partial_visible_bee` instead.

The raw model-proposed class is preserved as debugging provenance. Reliability of complete-vs-partial model classification is parked because it may materially affect later Varroa denominator and crop-generation behaviour.

### Zero Suggestions Is Not Failure

An inference run that returns zero suggestions is successful if the model executed correctly. The UI should show the model candidate id and threshold used, such as `0 suggestions from HS-MC-000001 at threshold 0.10`.

## Layers Touched

- Web UI: Add **Suggest bees** to the editable Training Crop editor; render Candidate Annotations separately from reviewed ellipses; add accept/edit/reject/clear controls for suggestions; show the selected Model Candidate id/status; add a simple threshold selector; allow selecting among completed candidates when more than one exists.
- Core API: Add crop pre-labelling endpoint for Bee Detector Model Candidate inference; validate Workspace, Training Crop, Model Candidate, Dataset Curator capability, and self-dataset blocking; return transient Candidate Annotation proposals.
- Analysis Service: Not touched in this slice. This remains a dataset-curation helper, not beekeeper-facing analysis.
- Storage: Persist accepted/edited proposals as Oriented Bee Ellipses with model-candidate provenance. Do not persist rejected proposals in this slice.
- Queue or async boundary: Use synchronous request/response inference for one crop initially. If local inference becomes slow, add an async pre-labelling run later.
- Contracts: Add request/response shapes for crop-level Candidate Annotation proposals and accepted candidate provenance fields.
- Observability: Log model-candidate inference request, model candidate id, training crop id, proposal count, threshold, adapter type, selected weights artifact, and failure code.
- Developer tooling: Reuse `pnpm dev:all:yolo-training`. Add `pnpm model:qa:bee:prelabel` if implementation cost stays small; by default it uses the latest completed Model Candidate and latest editable crop, printing both ids.

## Test Seams

- Seam: Bee Detector inference adapter
- Behaviour verified: fake adapter returns deterministic YOLO-style oriented predictions for a crop.
- Test style: Core API workflow/unit tests with fake adapter.

- Seam: Model Candidate eligibility
- Behaviour verified: only completed Bee Detector Model Candidates from the same Workspace can generate crop proposals, and failed/abandoned Training Runs with stray weights are not eligible.
- Test style: Core API route tests.

- Seam: self-dataset blocking
- Behaviour verified: suggestions are blocked when the selected crop's Dataset Item was included in the Model Candidate's own Dataset Version; unassigned crops are allowed.
- Test style: Core API route/workflow tests.

- Seam: Candidate Annotation response contract
- Behaviour verified: returned proposals include geometry, default accept class, raw model class, confidence, threshold, raw YOLO OBB geometry, model candidate provenance, and do not create reviewed ellipses automatically.
- Test style: Core API route tests and API-level BDD.

- Seam: Accepting a proposal
- Behaviour verified: accepting or editing a proposal creates an Oriented Bee Ellipse with `annotation_source=model_candidate`, `model_candidate_id`, `review_method=human_reviewed_candidate`, confidence, threshold, raw geometry, and accepted unchanged/with-edits provenance.
- Test style: Core API route/workflow tests.

- Seam: Rejecting a proposal
- Behaviour verified: rejecting a proposal does not create reviewed ellipse evidence or Dataset Item eligibility.
- Test style: Core API or Web UI test depending on whether rejected proposals are persisted.

- Seam: Web UI
- Behaviour verified: Dataset Curator can click **Suggest bees**, see proposed overlays, accept one, edit one, reject one, clear suggestions, see zero suggestions as a successful result, and see accepted proposals become normal reviewed crop ellipses with provenance.
- Test style: Playwright acceptance with fake inference adapter.

- Seam: Real model smoke check
- Behaviour verified: the latest completed local YOLO OBB Model Candidate can run inference on a crop without crashing and returns zero or more proposals.
- Test style: explicit local QA lane, not normal CI.

## Data Shape

### Candidate Bee Annotation Proposal

Minimum response fields:

- `candidate_annotation_id`: generated response id; may be transient
- `workspace_id`
- `training_crop_id`
- `model_candidate_id`
- `model_purpose`: `bee_detector`
- `annotation_type`: `complete_visible_bee` or `partial_visible_bee`
- `default_accept_annotation_type`: initially `complete_visible_bee`
- `raw_model_class`: raw class id/name returned by the adapter
- `confidence`
- `confidence_threshold`
- `center_x`
- `center_y`
- `radius_x`
- `radius_y`
- `rotation_degrees`
- `raw_yolo_obb_points`: original model-space oriented box points, retained for debugging accepted suggestions
- `geometry_source`: `yolo_obb_to_oriented_ellipse_v1`
- `annotation_source`: `model_candidate`
- `created_at`

### Candidate Pre-Labelling Request

- `workspace_id`
- `training_crop_id`
- `model_candidate_id`: optional; defaults to latest completed Bee Detector candidate
- `confidence_threshold`: optional; default `0.10`
- `max_suggestions`: optional; default and initial cap `50`

### Candidate Review Request

For accepted or edited proposals:

- `workspace_id`
- `candidate_annotation_id` or inline candidate geometry
- `model_candidate_id`
- `candidate_confidence`
- `confidence_threshold`
- `raw_model_class`
- `raw_yolo_obb_points`
- `annotation_type`
- reviewed geometry fields
- `review_decision`: `accepted` or `accepted_with_edits`
- optional note

Rejected proposals:

- `workspace_id`
- `review_decision`: `rejected`
- optional reason

Rejected proposals are transient in this slice, so the reject action may be client-only. The API should not require durable rejection records.

### Oriented Bee Ellipse Provenance

Accepted model-assisted annotations need enough provenance to report:

- Annotation Source: `model_candidate`
- Review Method: `human_reviewed_candidate`
- Pre-Labelling Model Version / Model Candidate id
- original candidate confidence
- inference threshold
- raw model class
- raw YOLO OBB points
- whether geometry was accepted unchanged or edited

If the existing `OrientedBeeEllipseResponse` cannot carry this cleanly, this slice should add the smallest compatible fields rather than overloading notes text.

Dataset Version and baseline reports should count model-assisted reviewed annotations separately from human-from-scratch annotations once these provenance fields exist.

## Suggested API Endpoints

- `POST /v1/model-candidates/{model_candidate_id}/training-crops/{training_crop_id}/candidate-annotations`
- or `POST /v1/training-crops/{training_crop_id}/candidate-annotations`

Preferred endpoint during implementation:

- `POST /v1/training-crops/{training_crop_id}/candidate-annotations`

Rationale: the UI is crop-centred and can pass `model_candidate_id` explicitly or leave it null for latest eligible candidate.

Accepted candidates may reuse the existing ellipse creation endpoint if the request can carry provenance. If not, add a narrow candidate-review endpoint:

- `POST /v1/training-crops/{training_crop_id}/candidate-annotations/{candidate_annotation_id}/review`

## UI Expectations

The Training Crop editor should keep the primary visual work area dominant.

Near the crop controls:

- show **Suggest bees**
- show selected Model Candidate, e.g. `HS-MC-000001`
- show a simple Model Candidate selector if more than one completed candidate exists
- show a compact threshold selector or numeric input, default `0.10`
- show a small count such as `4 suggestions`
- show `Suggestions are from an unapproved Model Candidate and require human review.`

Candidate overlays:

- use a distinct visual style from reviewed ellipses
- do not look complete or trusted
- can be selected individually
- show confidence and proposed class only in selected suggestion detail, not on every overlay

Candidate controls:

- accept as complete bee
- accept as partial bee
- edit then accept
- reject
- clear all suggestions
- no accept-all action in this slice

After acceptance:

- the annotation appears in the normal reviewed ellipse list
- provenance remains visible enough for the curator to understand it was model-assisted
- the Dataset Item/reporting path can distinguish it from human-from-scratch evidence

Candidate suggestions are cleared automatically when the curator switches crop or source photo. Accepting or editing a candidate removes that candidate suggestion from the transient suggestion list.

If the crop has no Dataset Item, suggestions are allowed. If the crop has a Dataset Item created after the selected Model Candidate's Dataset Version, suggestions are allowed unless that Dataset Item id is actually in the candidate's frozen Dataset Version.

If the selected crop image content is missing, the endpoint returns a clear failure. Missing content is not treated as zero suggestions.

## Out Of Scope

- Full-frame or full-photo pre-labelling.
- Automatic acceptance of model predictions.
- Model Candidate promotion or approval.
- Benchmark Evaluation.
- Varroa detection or mite proposals.
- Training the model from newly accepted candidate-assisted annotations in the same action.
- Active learning selection of which crops to label next.
- Blind-review comparison workflow.
- Persisted rejected-candidate history.
- Durable Candidate Annotation entity/audit ledger.
- Production worker/process orchestration for inference.
- Automatic duplicate suppression or overlap deduplication.
- Accept-all suggestions.
- Trusting model complete-vs-partial classification.

## Acceptance Criteria

- [ ] Dataset Curator can request bee suggestions for the selected Training Crop from a completed Bee Detector Model Candidate.
- [ ] UI defaults to latest completed Model Candidate and provides a selector when more than one completed candidate exists.
- [ ] Suggestions are available only for editable crops; completed/excluded crops must be reopened first.
- [ ] The request is rejected when the user lacks Dataset Curator capability.
- [ ] The request is rejected when the Model Candidate is missing, belongs to another Workspace, is not a Bee Detector, or was not created by a completed Training Run.
- [ ] Suggestions are blocked when the selected crop's Dataset Item was included in the selected Model Candidate's own Dataset Version.
- [ ] Unassigned crops and later-assigned Dataset Items not present in the candidate's frozen Dataset Version are allowed.
- [ ] Candidate Annotations are displayed distinctly from reviewed Oriented Bee Ellipses.
- [ ] Candidate Annotations are not persisted as reviewed evidence merely by being generated.
- [ ] Zero suggestions is shown as a successful inference result, not as a failure.
- [ ] Dataset Curator can accept a candidate as a complete visible bee.
- [ ] Dataset Curator can accept a candidate as a partial visible bee.
- [ ] Dataset Curator can edit candidate geometry before accepting.
- [ ] Dataset Curator can reject or clear candidate suggestions without creating reviewed evidence.
- [ ] Accepted or edited candidates persist as Oriented Bee Ellipses with Annotation Source `model_candidate`.
- [ ] Accepted or edited candidates preserve Model Candidate id, review method `human_reviewed_candidate`, candidate confidence, threshold, raw model class, raw YOLO OBB geometry, and accepted unchanged/with-edits status.
- [ ] Human-from-scratch annotations remain supported and distinguishable.
- [ ] Dataset Version/report summaries distinguish human-from-scratch and human-reviewed-candidate annotation evidence.
- [ ] Suggestions run against the crop image, not the whole source image.
- [ ] The real inference adapter uses the selected Model Candidate's stored weights artifact, not a configured default base weights path.
- [ ] API returns at most 50 suggestions sorted by confidence descending.
- [ ] The UI warns that suggestions are from an unapproved Model Candidate and require human review.
- [ ] The UI does not offer accept-all.
- [ ] Fast tests use a deterministic fake inference adapter and do not require Ultralytics.
- [ ] A real-adapter QA check can run the latest local YOLO OBB Model Candidate against a crop and report zero or more proposals.
- [ ] API-level BDD covers candidate proposal generation and human-reviewed acceptance.
- [ ] Playwright acceptance covers the crop editor suggestion workflow.
- [ ] `pnpm verify:slice` remains green without real YOLO inference dependencies.

## Closed Decisions

- Default to the latest completed Bee Detector Model Candidate; show a selector when multiple completed candidates exist.
- Use threshold `0.10` by default, with a simple UI control.
- Keep proposals transient; persist only accepted or edited reviewed ellipses.
- Do not persist rejected suggestions in this slice.
- Preserve accepted unchanged versus accepted with edits.
- Store Model Candidate id, candidate confidence, threshold, raw model class, and raw YOLO OBB geometry on accepted/edited model-assisted ellipses.
- Block suggestions on crops included in the selected Model Candidate's own frozen Dataset Version.
- Allow suggestions on unassigned crops.
- Run inference against the crop image only.
- Convert YOLO OBB to oriented ellipse using center, half-width/half-height radii, and orientation; conversion version `yolo_obb_to_oriented_ellipse_v1`.
- Use the selected Model Candidate's stored weights artifact for real inference.
- Treat zero suggestions as success.
- Do not add accept-all or automatic deduplication in this slice.
- Add API-level BDD and Playwright acceptance coverage.
- Keep real YOLO inference out of `pnpm verify:slice`; use a separate QA command if small.
