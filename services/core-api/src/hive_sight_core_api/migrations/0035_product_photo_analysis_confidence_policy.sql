ALTER TABLE varroa_photo_analysis_runs
    ADD COLUMN IF NOT EXISTS confidence_policy_version text NOT NULL DEFAULT 'product_photo_confidence_policy_v1',
    ADD COLUMN IF NOT EXISTS confidence_policy_status text NOT NULL DEFAULT 'not_assessable' CHECK (
        confidence_policy_status IN (
            'development_evidence_only',
            'advisor_candidate_possible',
            'blocked_by_confidence_policy',
            'blocked_by_coverage_policy',
            'not_assessable'
        )
    ),
    ADD COLUMN IF NOT EXISTS advisor_evidence_eligibility text NOT NULL DEFAULT 'ineligible' CHECK (
        advisor_evidence_eligibility IN (
            'ineligible',
            'development_integration_only',
            'product_candidate'
        )
    ),
    ADD COLUMN IF NOT EXISTS confidence_policy_caveats jsonb NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS confidence_policy_caveat_messages jsonb NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS bee_localisation_policy_status text NOT NULL DEFAULT 'not_assessable' CHECK (
        bee_localisation_policy_status IN (
            'development_evidence_only',
            'policy_satisfied',
            'blocked_by_confidence_policy',
            'blocked_by_coverage_policy',
            'not_assessable'
        )
    ),
    ADD COLUMN IF NOT EXISTS bee_orientation_policy_status text NOT NULL DEFAULT 'not_assessable' CHECK (
        bee_orientation_policy_status IN (
            'development_evidence_only',
            'policy_satisfied',
            'blocked_by_confidence_policy',
            'blocked_by_coverage_policy',
            'not_assessable'
        )
    ),
    ADD COLUMN IF NOT EXISTS varroa_detection_policy_status text NOT NULL DEFAULT 'not_assessable' CHECK (
        varroa_detection_policy_status IN (
            'development_evidence_only',
            'policy_satisfied',
            'blocked_by_confidence_policy',
            'blocked_by_coverage_policy',
            'not_assessable'
        )
    ),
    ADD COLUMN IF NOT EXISTS unassessed_complete_bees integer NOT NULL DEFAULT 0 CHECK (unassessed_complete_bees >= 0),
    ADD COLUMN IF NOT EXISTS low_confidence_detection_count integer NOT NULL DEFAULT 0 CHECK (low_confidence_detection_count >= 0);

ALTER TABLE varroa_photo_analysis_runs
    DROP COLUMN IF EXISTS advisor_evidence_eligible;
