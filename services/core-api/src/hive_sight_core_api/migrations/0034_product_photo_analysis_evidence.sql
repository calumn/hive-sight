ALTER TABLE varroa_photo_analysis_runs
    ADD COLUMN IF NOT EXISTS bees_with_likely_varroa integer NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS current_stage text;

ALTER TABLE varroa_photo_analysis_bee_results
    ALTER COLUMN training_crop_id DROP NOT NULL,
    ALTER COLUMN bee_annotation_id DROP NOT NULL,
    ADD COLUMN IF NOT EXISTS inspection_photo_id uuid REFERENCES inspection_photos(id),
    ADD COLUMN IF NOT EXISTS source_geometry_snapshot jsonb;

CREATE INDEX IF NOT EXISTS varroa_photo_analysis_bee_results_photo_idx
    ON varroa_photo_analysis_bee_results (inspection_photo_id);
