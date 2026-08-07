CREATE TABLE IF NOT EXISTS varroa_photo_analysis_runs (
    id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL REFERENCES workspaces(id),
    inspection_id uuid NOT NULL REFERENCES inspections(id),
    inspection_photo_id uuid NOT NULL REFERENCES inspection_photos(id),
    status text NOT NULL CHECK (
        status IN ('running', 'completed', 'partial', 'failed', 'no_usable_bees')
    ),
    review_status text NOT NULL CHECK (
        review_status IN (
            'unreviewed',
            'accepted',
            'rejected',
            'inconclusive',
            'needs_expert_review'
        )
    ),
    review_note text,
    total_detected_bees integer NOT NULL CHECK (total_detected_bees >= 0),
    eligible_bees integer NOT NULL CHECK (eligible_bees >= 0),
    analysed_bees integer NOT NULL CHECK (analysed_bees >= 0),
    failed_bees integer NOT NULL CHECK (failed_bees >= 0),
    mites_found integer NOT NULL CHECK (mites_found >= 0),
    mite_ratio_basis text NOT NULL,
    adapter_type text NOT NULL,
    adapter_version text NOT NULL,
    model_reference text NOT NULL,
    command_contract_version text,
    started_at timestamptz NOT NULL,
    completed_at timestamptz,
    failure_code text,
    failure_message text,
    caveat text NOT NULL,
    advisor_evidence_eligible boolean NOT NULL DEFAULT false
);

CREATE INDEX IF NOT EXISTS varroa_photo_analysis_runs_photo_idx
    ON varroa_photo_analysis_runs (workspace_id, inspection_photo_id, started_at);

CREATE TABLE IF NOT EXISTS varroa_photo_analysis_bee_results (
    id uuid PRIMARY KEY,
    photo_analysis_run_id uuid NOT NULL REFERENCES varroa_photo_analysis_runs(id),
    training_crop_id uuid NOT NULL REFERENCES training_crops(id),
    bee_annotation_id uuid NOT NULL REFERENCES oriented_bee_ellipses(id),
    status text NOT NULL CHECK (status IN ('completed', 'failed')),
    mites_found integer NOT NULL CHECK (mites_found >= 0),
    detections jsonb NOT NULL,
    adapter_type text NOT NULL,
    adapter_version text NOT NULL,
    model_reference text NOT NULL,
    command_contract_version text,
    detector_answer_id text,
    failure_code text,
    failure_message text,
    raw_error_payload text,
    head_up_normalized_crop jsonb
);

CREATE INDEX IF NOT EXISTS varroa_photo_analysis_bee_results_run_idx
    ON varroa_photo_analysis_bee_results (photo_analysis_run_id);
