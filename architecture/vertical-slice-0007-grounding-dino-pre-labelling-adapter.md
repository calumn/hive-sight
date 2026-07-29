# Vertical Slice 0007: Grounding DINO Pre-Labelling Adapter

## Purpose

Prove that HiveSight can use a separate, swappable pre-labelling helper to create AI-assisted Draft Annotations for bee labelling, starting with a Grounding DINO adapter behind the existing pre-labeller dependency seam.

This slice makes the "robot first guess" vaguely real while preserving the governance rules already established: Grounding DINO output is Draft Annotation evidence only, human review remains mandatory, Dataset Role assignment remains explicit, and the future HiveSight product recognition model is not trained, evaluated, or promoted in this slice.

## Source Inputs

- `CONTEXT.md`: Draft Annotation, Reviewed Annotation, Annotation Source, Dataset Curator, Internal Capability, Dataset Item, Dataset Role, Model Candidate, Benchmark Evaluation.
- `requirements/ai-assisted-annotation-and-model-training-baseline.md`: AI-assisted annotation bootstrap, human review required, bee-first bootstrap, distinct labelling and product feedback workflows, provenance required, first model family decision required.
- `requirements/product-spec.md`: "Reviewer creates reviewed bee annotations from AI-assisted draft annotations" and benchmark protection scenarios.
- `architecture/domain-model.md`: Draft Annotation, Reviewed Annotation, Annotation Source, Dataset Curator, Internal Capability, Dataset Item, Training Run, Model Candidate.
- `architecture/adr/0001-service-oriented-architecture.md`: Core API owns product workflow and authorization; model training and evaluation remain separate from V1 runtime services.
- `architecture/vertical-slice-0005-ai-assisted-bee-annotation-bootstrap.md`: Dataset Labelling Session, deterministic pre-labeller seam, Draft Annotation provenance, pre-labeller run evidence.
- `architecture/vertical-slice-0006-dataset-role-assignment.md`: Dataset Item creation and the decision that Slice 7 should focus on a separate pre-labelling helper before heavy annotation-editor UI.

## User Path

Given a Dataset Curator starts AI-assisted dataset labelling for an uploaded Inspection Photo
And the Core API is configured to use the Grounding DINO pre-labelling adapter
When the Dataset Labelling Workflow invokes the pre-labeller seam
Then the adapter attempts to create bee-only Draft Annotations using Grounding DINO
And the Draft Annotations are projected through the existing labelling evidence UI
And the pre-labeller run records model, checkpoint, prompt, thresholds, runtime mode, adapter version, and failure evidence where relevant
And the Dataset Curator must still review, correct later, or reject the draft suggestions before they become Reviewed Annotations

## Preconditions

- Vertical Slice 0005 is implemented and demoable.
- Vertical Slice 0006 may be implemented first if Dataset Item assignment remains the agreed order; Slice 7 itself does not require Dataset Items to run.
- The caller is a registered User with internal `dataset_curator` capability.
- The Workspace has accepted the Workspace Data Use Agreement.
- The selected Inspection Photo belongs to the caller's Workspace.
- The existing `BeePrelabeler` or equivalent pre-labeller interface remains the workflow seam.
- The deterministic pre-labeller remains available for tests and fallback.
- Grounding DINO is treated as a local runtime adapter for this slice. No hosted image transfer is introduced.
- If Grounding DINO runtime dependencies, model weights, or checkpoint files are unavailable, the workflow records `prelabel_failed` evidence instead of silently falling back to deterministic success.

## End-To-End Behaviour

The Dataset Curator follows the existing dataset-labelling path and starts labelling for one Inspection Photo.

The Core API selects the configured pre-labeller adapter through settings. Supported Slice 7 values are:

- `deterministic`
- `grounding_dino`

`deterministic` keeps the existing Slice 5 behaviour and remains the default for automated tests unless the test explicitly opts into the Grounding DINO adapter.

`grounding_dino` loads or calls a local Grounding DINO runtime adapter. The adapter uses a bee-focused prompt such as `honey bee . partial honey bee` and configured thresholds to produce candidate boxes. The adapter maps Grounding DINO output into HiveSight's existing Draft Annotation shape:

- `annotation_type`
- normalized geometry
- `coordinate_space = normalized`
- source image dimensions
- confidence
- `source = ai_assisted_draft`
- `workflow_type = dataset_labelling`

Grounding DINO-specific details are recorded as pre-labeller provenance, not spread across the product workflow. At minimum the pre-labeller run records provider, adapter version, model/checkpoint identifier, prompt text, box threshold, text threshold, runtime mode, started/finished timestamps, status, and error details when relevant.

For the first adapter slice, the UI does not need complex model controls. It should show which pre-labeller produced the suggestions and whether the run succeeded or failed. The Dataset Curator can still use the same review controls from Slice 5 to approve draft suggestions. The UI must not describe the suggestions as ground truth or as output from the future HiveSight trained product recognition model.

If the Grounding DINO adapter returns no usable bee boxes, the labelling session can still be created with a successful pre-labeller run and zero Draft Annotations, but the UI and API should clearly show that no draft suggestions were produced. Human-from-scratch annotation remains out of scope, so that case is observable but not fixable inside this slice.

If the adapter fails because dependencies, weights, image loading, runtime execution, or output parsing fail, the session records `prelabel_failed`, preserves failure details, and exposes that state through the API and UI. Starting labelling again returns the failed session until a later explicit retry workflow is implemented.

## Layers Touched

- Web UI: Shows pre-labeller provider, model/checkpoint, prompt, threshold summary, run status, and failure state on the existing dataset-labelling surface. It reuses the existing draft annotation overlay and review controls.
- Core API: Adds pre-labeller provider settings, Grounding DINO adapter wiring, adapter provenance projection, and failure mapping through the existing Dataset Labelling Workflow.
- Analysis Service: Not touched for this slice. Grounding DINO is a dataset-labelling pre-labeller adapter, not the product Analysis Service runtime.
- Storage: Reuses original Inspection Photo storage and current development metadata. Adds only the minimum pre-labeller run provenance fields needed to distinguish deterministic and Grounding DINO runs.
- Queue or async boundary: Not touched. Slice 7 may run pre-labelling synchronously for one photo, but the adapter should remain isolated so a later slice can move it behind a worker if runtime cost is too high.
- Contracts: Extends pre-labeller run contract with provider/config provenance and no-suggestions/failure evidence.
- Observability: Adds test-visible evidence for selected provider, adapter version, prompt, thresholds, model/checkpoint, runtime mode, successful no-suggestion runs, and failed runs.
- Verification reporting: `pnpm verify:slice` should include Core API tests, API-level BDD, Web type-check, browser acceptance, and a clear note whether Grounding DINO runtime tests ran or were skipped because local model assets were unavailable.

## Test Seams

- Seam: Pre-labeller provider selection
- Behaviour verified: settings choose `deterministic` or `grounding_dino`; unknown provider values fail clearly at startup or dependency creation.
- Test style: Core API dependency/unit tests.

- Seam: `BeePrelabeler` interface
- Behaviour verified: Dataset Labelling Workflow depends only on the pre-labeller interface and not on Grounding DINO implementation details.
- Test style: Core API workflow tests with deterministic fake adapters.

- Seam: Grounding DINO adapter mapping
- Behaviour verified: adapter output boxes, labels, and scores map into HiveSight Draft Annotations with normalized geometry, bee-only annotation types, confidence, source, and workflow provenance.
- Test style: Adapter unit tests using a fake local Grounding DINO runner or captured minimal output, not full model inference.

- Seam: Grounding DINO failure handling
- Behaviour verified: missing runtime, missing weights, invalid output, image loading failure, or adapter exception records `prelabel_failed` evidence instead of silent deterministic fallback.
- Test style: Core API workflow/unit tests with failing fake adapter.

- Seam: Pre-labeller run provenance
- Behaviour verified: provider, adapter version, model/checkpoint, prompt, box threshold, text threshold, runtime mode, started/finished timestamps, status, and error details are projected in labelling evidence.
- Test style: Core API route/workflow tests and TypeScript client parsing.

- Seam: API-level BDD acceptance
- Behaviour verified: a Dataset Curator starts labelling with a separate Grounding DINO pre-labeller helper; suggestions remain Draft Annotations requiring human review; failure is observable when the helper is unavailable.
- Test style: pytest-bdd feature scenarios aimed at the Core API. Full model runtime may be marked as environment-dependent.

- Seam: Web UI labelling surface
- Behaviour verified: Dataset Curator can see which helper produced suggestions and can still approve draft suggestions through the existing review flow.
- Test style: Playwright browser acceptance using deterministic or fake Grounding DINO adapter output.

## Data Shape

Minimum additions or extensions:

- Pre-labeller provider: `deterministic`, `grounding_dino`.
- Pre-labeller run provenance: `provider`, `adapter_version`, `model_id`, `checkpoint_id`, `prompt_text`, `box_threshold`, `text_threshold`, `runtime_mode`, `suggestion_count`.
- Runtime mode: `local`.
- Pre-labeller run status: existing `succeeded`, `failed`.
- Failure code examples: `prelabeler_unavailable`, `prelabeler_model_missing`, `prelabeler_image_load_failed`, `prelabeler_invalid_output`, `prelabel_failed`.
- Draft Annotation: existing Slice 5 shape remains unchanged, but Grounding DINO-created annotations use `source = ai_assisted_draft`, `workflow_type = dataset_labelling`, and pre-labeller provenance from the run.

Minimum settings:

- `HIVESIGHT_PRELABELER`: `deterministic` or `grounding_dino`.
- `HIVESIGHT_GROUNDING_DINO_MODEL_ID`: model/config identifier.
- `HIVESIGHT_GROUNDING_DINO_CHECKPOINT`: local checkpoint path or identifier.
- `HIVESIGHT_GROUNDING_DINO_PROMPT`: default bee prompt.
- `HIVESIGHT_GROUNDING_DINO_BOX_THRESHOLD`: numeric threshold.
- `HIVESIGHT_GROUNDING_DINO_TEXT_THRESHOLD`: numeric threshold.

Minimum API shapes:

- Existing start labelling request remains unchanged.
- Existing labelling evidence response includes extended `prelabeler_run` provenance.
- Blocked/failure response codes are not required for runtime failure if failure is recorded on the session, but dependency misconfiguration should be visible as `prelabeler_unavailable` or `prelabel_failed`.

## Out Of Scope

- Training a HiveSight recognition model.
- Evaluating, benchmarking, or promoting a Model Candidate.
- Using Grounding DINO output as ground truth.
- Hosted pre-labelling services or image transfer to third-party APIs.
- SAM/SAM 2 segmentation integration.
- YOLO training, export, or inference.
- Annotation geometry editing, adding missed bees, deleting false positives, or human-from-scratch annotation.
- Automatic threshold tuning.
- Dataset Version creation or dataset export.
- Benchmark Evaluation execution.
- Queue/worker execution for long-running pre-labelling.
- Production model asset packaging or installer experience.
- Production auth provider integration.

## Acceptance Criteria

- [ ] Core API can be configured to use `deterministic` pre-labeller.
- [ ] Core API can be configured to use `grounding_dino` pre-labeller.
- [ ] Dataset Labelling Workflow depends on a pre-labeller interface rather than Grounding DINO concrete code.
- [ ] Deterministic pre-labeller remains available for fast tests and local fallback.
- [ ] Unknown pre-labeller provider configuration fails clearly.
- [ ] Grounding DINO adapter maps fake or captured runner output into bee-only Draft Annotations.
- [ ] Grounding DINO-created Draft Annotations preserve `source = ai_assisted_draft` and `workflow_type = dataset_labelling`.
- [ ] Grounding DINO-created Draft Annotations remain subject to human review before they can become Reviewed Annotations.
- [ ] Pre-labeller run evidence records provider, adapter version, model/checkpoint, prompt, thresholds, runtime mode, status, timestamps, and suggestion count.
- [ ] Grounding DINO runtime failure records `prelabel_failed` session evidence and does not silently fall back to deterministic success.
- [ ] A successful run with zero suggestions is observable and does not create Reviewed Annotations or Dataset Items.
- [ ] Web UI shows the selected pre-labelling helper and run status on the dataset-labelling surface.
- [ ] Web UI keeps machine suggestions labelled as Draft Annotations requiring curator review.
- [ ] API-level BDD covers separate pre-labeller helper success and unavailable-helper failure.
- [ ] Browser acceptance covers the Dataset Curator seeing helper provenance and approving draft suggestions.
- [ ] `pnpm verify:slice` includes Slice 7 checks and notes whether full local Grounding DINO runtime inference was executed or skipped.

## Decisions For This Slice

- Grounding DINO is the first real-ish pre-labelling helper candidate.
- Grounding DINO is used only as a separate pre-labelling helper, not as the future HiveSight trained product recognition model.
- The existing deterministic pre-labeller remains the test/default adapter unless configuration selects Grounding DINO.
- Dependency injection is the boundary: Dataset Labelling Workflow depends on a `BeePrelabeler`-style interface.
- Grounding DINO adapter details remain in adapter code and pre-labeller run provenance.
- Slice 7 is local-first and does not send images to hosted services.
- Missing Grounding DINO runtime or model assets should produce visible failure evidence, not silent fake success.
- Full local model inference may be environment-dependent; adapter mapping and workflow behaviour must still be testable without the real model.

## Open Questions

- Should the default local development provider remain `deterministic`, with `grounding_dino` opt-in, or should dev startup try Grounding DINO when assets are present?
- What exact Grounding DINO implementation/package/checkpoint should be the first target?
- Where should local model weights live, and should they be gitignored/manual-download assets rather than committed files?
- What initial prompt should we use: `bee`, `honey bee`, `honey bee . partial honey bee`, or something more brood-frame-specific?
- What initial box/text thresholds should be configurable defaults?
- Should Slice 7 include an installation note/script for Grounding DINO dependencies, or only define the adapter contract and fake-runner tests first?
