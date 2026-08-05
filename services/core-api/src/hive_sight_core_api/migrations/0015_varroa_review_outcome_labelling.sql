ALTER TABLE oriented_bee_ellipses
    ADD COLUMN IF NOT EXISTS orientation_reliability text NOT NULL DEFAULT 'reliable',
    ADD COLUMN IF NOT EXISTS varroa_review_suitability text NOT NULL DEFAULT 'unassessed',
    ADD COLUMN IF NOT EXISTS suspected_visible_varroa boolean NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS varroa_review_suitability_updated_by_user_id uuid REFERENCES users(id),
    ADD COLUMN IF NOT EXISTS varroa_review_suitability_updated_at timestamptz,
    ADD COLUMN IF NOT EXISTS suspected_visible_varroa_updated_by_user_id uuid REFERENCES users(id),
    ADD COLUMN IF NOT EXISTS suspected_visible_varroa_updated_at timestamptz;

CREATE TABLE IF NOT EXISTS varroa_review_outcomes (
    id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL REFERENCES workspaces(id),
    inspection_photo_id uuid NOT NULL REFERENCES inspection_photos(id),
    training_crop_id uuid NOT NULL REFERENCES training_crops(id),
    bee_annotation_id uuid NOT NULL REFERENCES oriented_bee_ellipses(id),
    outcome text NOT NULL CHECK (
        outcome IN ('visible_varroa_present', 'no_visible_varroa', 'not_determined')
    ),
    sampling_purpose text NOT NULL,
    dataset_selection_method text NOT NULL,
    review_strength text NOT NULL,
    annotation_source text NOT NULL,
    notes text,
    source_context_snapshot jsonb NOT NULL,
    bee_annotation_geometry_snapshot jsonb NOT NULL,
    training_crop_review_status_snapshot text NOT NULL,
    transform_metadata jsonb NOT NULL,
    markers jsonb NOT NULL,
    created_by_user_id uuid NOT NULL REFERENCES users(id),
    created_at timestamptz NOT NULL,
    updated_by_user_id uuid NOT NULL REFERENCES users(id),
    updated_at timestamptz NOT NULL,
    UNIQUE (workspace_id, bee_annotation_id)
);

CREATE INDEX IF NOT EXISTS varroa_review_outcomes_workspace_crop_idx
    ON varroa_review_outcomes (workspace_id, training_crop_id);
