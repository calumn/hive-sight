CREATE TABLE IF NOT EXISTS repository_records (
    record_type text NOT NULL,
    record_id text NOT NULL,
    payload jsonb NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (record_type, record_id)
);

CREATE SEQUENCE IF NOT EXISTS source_image_human_id_seq;
CREATE SEQUENCE IF NOT EXISTS training_crop_human_id_seq;
CREATE SEQUENCE IF NOT EXISTS dataset_item_human_id_seq;

CREATE TABLE IF NOT EXISTS users (
    id uuid PRIMARY KEY,
    display_name text,
    contact_identifier text,
    status text NOT NULL DEFAULT 'active',
    registered_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS workspaces (
    id uuid PRIMARY KEY,
    display_name text,
    status text NOT NULL DEFAULT 'active',
    data_use_agreement_status text NOT NULL DEFAULT 'missing',
    data_use_agreement_terms_version text,
    data_use_agreement_accepted_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS workspace_memberships (
    id uuid PRIMARY KEY,
    user_id uuid NOT NULL REFERENCES users(id),
    workspace_id uuid NOT NULL REFERENCES workspaces(id),
    role text NOT NULL,
    status text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (user_id, workspace_id, role)
);

CREATE TABLE IF NOT EXISTS internal_capabilities (
    id uuid PRIMARY KEY,
    user_id uuid NOT NULL REFERENCES users(id),
    capability text NOT NULL,
    status text NOT NULL DEFAULT 'active',
    granted_at timestamptz NOT NULL DEFAULT now(),
    revoked_at timestamptz,
    UNIQUE (user_id, capability)
);

CREATE TABLE IF NOT EXISTS apiaries (
    id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL REFERENCES workspaces(id),
    name text NOT NULL,
    status text NOT NULL DEFAULT 'active',
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS hives (
    id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL REFERENCES workspaces(id),
    apiary_id uuid NOT NULL REFERENCES apiaries(id),
    name text NOT NULL,
    status text NOT NULL DEFAULT 'active',
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS frame_standards (
    id text PRIMARY KEY,
    display_name text NOT NULL,
    hive_type text NOT NULL,
    frame_use text NOT NULL,
    top_bar_length_mm integer,
    bottom_bar_length_mm integer,
    side_bar_height_mm integer,
    measurement_unit text NOT NULL DEFAULT 'mm',
    source_note text NOT NULL,
    status text NOT NULL
);

CREATE TABLE IF NOT EXISTS hive_configurations (
    id uuid PRIMARY KEY,
    hive_id uuid NOT NULL REFERENCES hives(id),
    workspace_id uuid NOT NULL REFERENCES workspaces(id),
    hive_type text NOT NULL,
    frame_use text NOT NULL,
    frame_standard_id text NOT NULL REFERENCES frame_standards(id),
    notes text,
    status text NOT NULL,
    effective_from date NOT NULL,
    effective_to date,
    configured_by_user_id uuid NOT NULL REFERENCES users(id),
    configured_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS one_current_hive_configuration_per_hive
    ON hive_configurations (hive_id)
    WHERE status = 'current';

CREATE TABLE IF NOT EXISTS inspections (
    id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL REFERENCES workspaces(id),
    hive_id uuid NOT NULL REFERENCES hives(id),
    inspection_date date NOT NULL,
    intent text NOT NULL CHECK (intent IN ('training_data_collection', 'varroa_assessment')),
    status text NOT NULL DEFAULT 'active',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS source_images (
    id uuid PRIMARY KEY,
    human_readable_id text NOT NULL UNIQUE,
    workspace_id uuid NOT NULL REFERENCES workspaces(id),
    source_type text NOT NULL CHECK (source_type IN ('inspection_photo')),
    object_key text NOT NULL,
    original_filename text NOT NULL,
    media_type text NOT NULL,
    file_size_bytes bigint NOT NULL,
    source_width_px integer NOT NULL,
    source_height_px integer NOT NULL,
    content_hash text NOT NULL,
    content_hash_algorithm text NOT NULL,
    source_group_key text,
    provenance_summary text,
    permission_status text NOT NULL,
    metadata_minimisation_status text NOT NULL,
    metadata_checked_at timestamptz NOT NULL,
    lifecycle_status text NOT NULL CHECK (lifecycle_status IN ('accepted', 'rejected', 'archived')),
    created_at timestamptz NOT NULL,
    CHECK (source_width_px > 0),
    CHECK (source_height_px > 0),
    UNIQUE (workspace_id, object_key)
);

CREATE TABLE IF NOT EXISTS inspection_photos (
    id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL REFERENCES workspaces(id),
    source_image_id uuid NOT NULL REFERENCES source_images(id),
    inspection_id uuid NOT NULL REFERENCES inspections(id),
    upload_status text NOT NULL,
    uploaded_at timestamptz NOT NULL,
    uploaded_by_user_id uuid NOT NULL REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS training_crops (
    id uuid PRIMARY KEY,
    human_readable_id text NOT NULL UNIQUE,
    workspace_id uuid NOT NULL REFERENCES workspaces(id),
    source_image_id uuid NOT NULL REFERENCES source_images(id),
    inspection_photo_id uuid REFERENCES inspection_photos(id),
    crop_x integer NOT NULL CHECK (crop_x >= 0),
    crop_y integer NOT NULL CHECK (crop_y >= 0),
    crop_width integer NOT NULL CHECK (crop_width > 0),
    crop_height integer NOT NULL CHECK (crop_height > 0),
    source_image_width_px integer NOT NULL CHECK (source_image_width_px > 0),
    source_image_height_px integer NOT NULL CHECK (source_image_height_px > 0),
    crop_image_width_px integer NOT NULL CHECK (crop_image_width_px > 0),
    crop_image_height_px integer NOT NULL CHECK (crop_image_height_px > 0),
    curriculum_stage text NOT NULL,
    review_status text NOT NULL,
    visible_bee_status text NOT NULL,
    exclusion_reason text,
    notes text,
    created_by_user_id uuid NOT NULL REFERENCES users(id),
    created_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS oriented_bee_ellipses (
    id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL REFERENCES workspaces(id),
    source_image_id uuid NOT NULL REFERENCES source_images(id),
    inspection_photo_id uuid NOT NULL REFERENCES inspection_photos(id),
    training_crop_id uuid NOT NULL REFERENCES training_crops(id),
    annotation_type text NOT NULL CHECK (annotation_type IN ('complete_visible_bee', 'partial_visible_bee')),
    center_x numeric NOT NULL CHECK (center_x >= 0),
    center_y numeric NOT NULL CHECK (center_y >= 0),
    radius_x numeric NOT NULL CHECK (radius_x > 0),
    radius_y numeric NOT NULL CHECK (radius_y > 0),
    rotation_degrees numeric NOT NULL,
    coordinate_space text NOT NULL,
    source_image_width_px integer NOT NULL,
    source_image_height_px integer NOT NULL,
    source text NOT NULL,
    created_by_user_id uuid NOT NULL REFERENCES users(id),
    created_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS dataset_items (
    id uuid PRIMARY KEY,
    human_readable_id text NOT NULL UNIQUE,
    workspace_id uuid NOT NULL REFERENCES workspaces(id),
    source_image_id uuid NOT NULL REFERENCES source_images(id),
    inspection_photo_id uuid NOT NULL REFERENCES inspection_photos(id),
    labelling_session_id uuid,
    training_crop_id uuid UNIQUE REFERENCES training_crops(id),
    source_evidence_type text NOT NULL,
    dataset_role text NOT NULL CHECK (dataset_role IN ('training', 'validation', 'benchmark', 'excluded')),
    status text NOT NULL CHECK (status IN ('active', 'superseded', 'withdrawn')),
    source_group_key text,
    image_quality_status text NOT NULL,
    reviewed_annotation_ids jsonb NOT NULL,
    ellipse_snapshot jsonb NOT NULL,
    provenance_snapshot jsonb NOT NULL,
    permission_snapshot jsonb NOT NULL,
    hive_configuration_snapshot jsonb,
    supersedes_dataset_item_id uuid REFERENCES dataset_items(id),
    superseded_by_dataset_item_id uuid REFERENCES dataset_items(id),
    assigned_by_user_id uuid NOT NULL REFERENCES users(id),
    assigned_at timestamptz NOT NULL,
    assignment_note text,
    exclusion_reason text,
    benchmark_protected boolean NOT NULL,
    CHECK (dataset_role <> 'benchmark' OR source_group_key IS NOT NULL)
);

CREATE UNIQUE INDEX IF NOT EXISTS benchmark_source_image_guard
    ON dataset_items (source_image_id)
    WHERE dataset_role = 'benchmark' AND status = 'active';

CREATE UNIQUE INDEX IF NOT EXISTS benchmark_source_group_guard
    ON dataset_items (workspace_id, source_group_key)
    WHERE dataset_role = 'benchmark' AND status = 'active' AND source_group_key IS NOT NULL;

CREATE INDEX IF NOT EXISTS inspection_photos_workspace_inspection_idx
    ON inspection_photos (workspace_id, inspection_id);

CREATE INDEX IF NOT EXISTS training_crops_workspace_photo_idx
    ON training_crops (workspace_id, inspection_photo_id);

CREATE INDEX IF NOT EXISTS dataset_items_workspace_role_idx
    ON dataset_items (workspace_id, dataset_role);
