# Domain Model Diagram

This diagram shows the conceptual domain model for BeehiveMonitor. It complements `domain-model.md` and uses the canonical language in `CONTEXT.md`.

```mermaid
erDiagram
    ACCOUNT ||--o{ APIARY : owns
    APIARY ||--o{ HIVE : contains
    HIVE ||--o{ INSPECTION : has
    INSPECTION ||--o{ INSPECTION_PHOTO : contains
    INSPECTION ||--o{ FRAME_LABEL : defines
    FRAME_LABEL ||--o{ INSPECTION_PHOTO : groups

    INSPECTION_PHOTO ||--o{ ANALYSIS_RESULT : has
    MODEL_VERSION ||--o{ ANALYSIS_RESULT : produces
    ANALYSIS_RESULT ||--o{ BEE_ANNOTATION : contains
    ANALYSIS_RESULT ||--o{ VARROA_ANNOTATION : contains
    BEE_ANNOTATION ||--o{ VARROA_ANNOTATION : may_host
    ANALYSIS_RESULT ||--o| INSPECTION_SUMMARY : contributes_to
    INSPECTION ||--o| INSPECTION_SUMMARY : has

    INSPECTION_PHOTO ||--o{ USER_CORRECTION : receives
    BEE_ANNOTATION ||--o{ USER_CORRECTION : may_be_corrected_by
    VARROA_ANNOTATION ||--o{ USER_CORRECTION : may_be_corrected_by
    USER_CORRECTION ||--o{ REVIEW_DECISION : reviewed_by
    BEE_ANNOTATION ||--o{ REVIEW_DECISION : reviewed_by
    VARROA_ANNOTATION ||--o{ REVIEW_DECISION : reviewed_by

    ACCOUNT ||--o{ CONSENT_RECORD : records
    INSPECTION ||--o{ CONSENT_RECORD : may_have
    INSPECTION_PHOTO ||--o{ CONSENT_RECORD : may_have
    USER_CORRECTION ||--o{ CONSENT_RECORD : may_have

    DATASET_VERSION ||--o{ REVIEW_DECISION : includes_approved_evidence
    DATASET_VERSION ||--o{ BENCHMARK_EVALUATION : used_by
    MODEL_VERSION ||--o{ BENCHMARK_EVALUATION : evaluated_by
    BENCHMARK_EVALUATION ||--o{ REVIEW_DECISION : approved_by

    ACCOUNT {
        string id
        string display_name
        string status
    }

    APIARY {
        string id
        string account_id
        string name
        string status
    }

    HIVE {
        string id
        string apiary_id
        string name_or_code
        string status
    }

    INSPECTION {
        string id
        string hive_id
        date inspection_date
        string status
    }

    FRAME_LABEL {
        string id
        string inspection_id
        string label
    }

    INSPECTION_PHOTO {
        string id
        string inspection_id
        string original_file_reference
        string upload_status
        string image_quality_status
    }

    ANALYSIS_RESULT {
        string id
        string photo_id
        string model_version_id
        int complete_visible_bee_count
        int partial_visible_bee_count
        int likely_varroa_on_complete_bees
        string status
    }

    INSPECTION_SUMMARY {
        string id
        string inspection_id
        float visible_varroa_rate
        string quality_warning_status
    }

    BEE_ANNOTATION {
        string id
        string analysis_result_id
        string visibility_class
        string source
        string review_status
    }

    VARROA_ANNOTATION {
        string id
        string analysis_result_id
        string association_state
        string source
        string review_status
    }

    USER_CORRECTION {
        string id
        string photo_id
        string correction_type
        string review_status
    }

    REVIEW_DECISION {
        string id
        string subject_type
        string subject_id
        string decision
    }

    CONSENT_RECORD {
        string id
        string subject_type
        string subject_id
        string status
        string scope
    }

    MODEL_VERSION {
        string id
        string version_label
        string release_status
    }

    DATASET_VERSION {
        string id
        string version_label
        string dataset_role
    }

    BENCHMARK_EVALUATION {
        string id
        string model_version_id
        string dataset_version_id
        string status
    }
```

## Reading The Diagram

- The left side is the beekeeper workflow: account, apiary, hive, inspection, photos, and analysis.
- The middle is the evidence layer: analysis results, bee annotations, Varroa annotations, summaries, and corrections.
- The lower/right side is model governance: review decisions, consent records, dataset versions, model versions, and benchmark evaluations.
- `Inspection Summary` is derived from photo-level analysis results and should be recalculable.
- `User Correction` is review evidence, not ground truth or training data until consent and review decisions allow it.
