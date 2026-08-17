ALTER TABLE hive_configurations
    ADD COLUMN IF NOT EXISTS brood_slot_count integer NOT NULL DEFAULT 10;

ALTER TABLE inspection_photos
    ADD COLUMN IF NOT EXISTS inspection_frame_observation_id uuid,
    ADD COLUMN IF NOT EXISTS hive_frame_slot_id uuid,
    ADD COLUMN IF NOT EXISTS frame_side text;

CREATE INDEX IF NOT EXISTS inspection_photos_frame_observation_idx
    ON inspection_photos (inspection_frame_observation_id);

CREATE INDEX IF NOT EXISTS inspection_photos_hive_frame_slot_idx
    ON inspection_photos (hive_frame_slot_id);
