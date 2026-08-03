from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date, datetime
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

from hive_sight_core_api.db import apply_migrations
from hive_sight_core_api.dev_store import (
    InMemoryProductDataStore,
    WorkspaceMembershipRecord,
    WorkspaceRecord,
)
from hive_sight_core_api.dev_users import DEV_USERS, DevUserSeed
from hive_sight_core_api.models import (
    AnalysisResultResponse,
    AnalysisRunResponse,
    AnnotationResponse,
    ApiaryResponse,
    ArtifactResponse,
    BenchmarkEvaluationResponse,
    DatasetVersionResponse,
    DatasetItemResponse,
    DatasetLabellingSessionResponse,
    HiveConfigurationResponse,
    HiveResponse,
    InspectionPhotoResponse,
    InspectionResponse,
    ModelCandidateResponse,
    OrientedBeeEllipseResponse,
    ReviewDecisionResponse,
    TrainingRunResponse,
    TrainingCropResponse,
)

MODEL_RECORD_TYPES: dict[str, type] = {
    "apiary": ApiaryResponse,
    "hive": HiveResponse,
    "hive_configuration": HiveConfigurationResponse,
    "inspection": InspectionResponse,
    "inspection_photo": InspectionPhotoResponse,
    "analysis_run": AnalysisRunResponse,
    "analysis_result": AnalysisResultResponse,
    "annotation": AnnotationResponse,
    "review_decision": ReviewDecisionResponse,
    "dataset_labelling_session": DatasetLabellingSessionResponse,
    "training_crop": TrainingCropResponse,
    "training_crop_ellipse": OrientedBeeEllipseResponse,
    "dataset_item": DatasetItemResponse,
    "dataset_version": DatasetVersionResponse,
    "training_run": TrainingRunResponse,
    "benchmark_evaluation": BenchmarkEvaluationResponse,
    "model_candidate": ModelCandidateResponse,
    "artifact": ArtifactResponse,
}


class PostgresProductDataStore(InMemoryProductDataStore):
    """Write-through Postgres adapter for the narrow Slice 0014 repository path."""

    def __init__(self, database_url: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.database_url = database_url
        apply_migrations(database_url)
        self._load_records()

    def ensure_dev_session(self, user_id: UUID):
        session = super().ensure_dev_session(user_id)
        self._persist_core_identity(user_id=user_id, workspace_id=session.workspace_id)
        return session

    def seed_development_users(self) -> None:
        super().seed_development_users()
        for seed in DEV_USERS:
            self._persist_payload("user", seed.user_id, {"user_id": str(seed.user_id)})
            self._persist_workspace(seed.workspace_id)
            self._persist_model("apiary", seed.apiary_id, self.apiaries[seed.apiary_id])
            self._persist_model("hive", seed.hive_id, self.hives[seed.hive_id])
            self._upsert_apiary_projection(self.apiaries[seed.apiary_id])
            self._upsert_hive_projection(self.hives[seed.hive_id])
            membership = next(
                membership
                for membership in self.memberships
                if membership.user_id == seed.user_id
                and membership.workspace_id == seed.workspace_id
                and membership.role == seed.workspace_membership_role
            )
            self._persist_payload(
                "workspace_membership",
                f"{membership.user_id}:{membership.workspace_id}:{membership.role}",
                _jsonable(asdict(membership)),
            )
            self._upsert_seeded_user_projection(seed)
            self._upsert_workspace_projection(seed.workspace_id)

    def accept_data_use_agreement(self, *args: Any, **kwargs: Any):
        response = super().accept_data_use_agreement(*args, **kwargs)
        self._persist_workspace(response.workspace_id)
        self._upsert_workspace_projection(response.workspace_id)
        return response

    def create_apiary(self, *args: Any, **kwargs: Any):
        response = super().create_apiary(*args, **kwargs)
        self._persist_model("apiary", response.apiary_id, response)
        self._upsert_apiary_projection(response)
        return response

    def create_hive(self, *args: Any, **kwargs: Any):
        response = super().create_hive(*args, **kwargs)
        self._persist_model("hive", response.hive_id, response)
        self._upsert_hive_projection(response)
        return response

    def save_hive_configuration(self, configuration: HiveConfigurationResponse):
        response = super().save_hive_configuration(configuration)
        self._persist_model("hive_configuration", response.hive_configuration_id, response)
        self._upsert_hive_configuration_projection(response)
        return response

    def save_inspection(self, inspection: InspectionResponse):
        response = super().save_inspection(inspection)
        self._persist_model("inspection", response.inspection_id, response)
        self._upsert_inspection_projection(response)
        return response

    def record_inspection_photo(self, *args: Any, **kwargs: Any):
        photo = super().record_inspection_photo(*args, **kwargs)
        self._persist_model("inspection_photo", photo.inspection_photo_id, photo)
        self._upsert_source_image_and_photo_projection(
            photo=photo,
            width_px=kwargs.get("source_image_width_px") or 1,
            height_px=kwargs.get("source_image_height_px") or 1,
            content_hash=kwargs.get("content_hash") or "unknown",
            content_hash_algorithm=kwargs.get("content_hash_algorithm") or "unknown",
        )
        return photo

    def record_analysis_run(self, analysis_run: AnalysisRunResponse):
        response = super().record_analysis_run(analysis_run)
        self._persist_model("analysis_run", response.analysis_run_id, response)
        return response

    def record_review_decision(self, *args: Any, **kwargs: Any):
        response = super().record_review_decision(*args, **kwargs)
        self._persist_model("review_decision", response.review_decision_id, response)
        return response

    def record_dataset_labelling_session(self, *args: Any, **kwargs: Any):
        response = super().record_dataset_labelling_session(*args, **kwargs)
        self._persist_model("dataset_labelling_session", response.labelling_session_id, response)
        return response

    def record_dataset_labelling_annotation(self, *args: Any, **kwargs: Any):
        response = super().record_dataset_labelling_annotation(*args, **kwargs)
        self._persist_model("annotation", response.annotation_id, response)
        return response

    def update_labelling_session_metadata(self, *args: Any, **kwargs: Any):
        response = super().update_labelling_session_metadata(*args, **kwargs)
        self._persist_model("dataset_labelling_session", response.labelling_session_id, response)
        return response

    def mark_labelling_session_review_in_progress(self, labelling_session_id: UUID) -> None:
        super().mark_labelling_session_review_in_progress(labelling_session_id)
        session = self.dataset_labelling_sessions.get(labelling_session_id)
        if session is not None:
            self._persist_model("dataset_labelling_session", session.labelling_session_id, session)

    def record_dataset_item(self, *args: Any, **kwargs: Any):
        response = super().record_dataset_item(*args, **kwargs)
        self._persist_model("dataset_item", response.dataset_item_id, response)
        self._upsert_dataset_item_projection(response)
        return response

    def save_training_crop(self, crop: TrainingCropResponse):
        response = super().save_training_crop(crop)
        self._persist_model("training_crop", response.training_crop_id, response)
        self._upsert_training_crop_projection(response)
        return response

    def save_training_crop_ellipse(self, ellipse: OrientedBeeEllipseResponse):
        response = super().save_training_crop_ellipse(ellipse)
        self._persist_model("training_crop_ellipse", response.annotation_id, response)
        self._upsert_ellipse_projection(response)
        return response

    def delete_training_crop_ellipse_record(self, annotation_id: UUID) -> None:
        super().delete_training_crop_ellipse_record(annotation_id)
        self._delete_record("training_crop_ellipse", annotation_id)
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute("DELETE FROM oriented_bee_ellipses WHERE id = %s", (annotation_id,))

    def save_dataset_item(self, dataset_item: DatasetItemResponse):
        response = super().save_dataset_item(dataset_item)
        self._persist_model("dataset_item", response.dataset_item_id, response)
        self._upsert_dataset_item_projection(response)
        return response

    def save_dataset_version(self, dataset_version: DatasetVersionResponse):
        response = super().save_dataset_version(dataset_version)
        self._persist_model("dataset_version", response.dataset_version_id, response)
        return response

    def save_training_run(self, training_run: TrainingRunResponse):
        response = super().save_training_run(training_run)
        self._persist_model("training_run", response.training_run_id, response)
        return response

    def save_benchmark_evaluation(self, evaluation: BenchmarkEvaluationResponse):
        response = super().save_benchmark_evaluation(evaluation)
        self._persist_model(
            "benchmark_evaluation",
            response.benchmark_evaluation_id,
            response,
        )
        return response

    def delete_training_run(self, training_run_id: UUID) -> None:
        super().delete_training_run(training_run_id)
        self._delete_record("training_run", training_run_id)

    def remove_dataset_and_model_evidence_for_workspace(
        self,
        workspace_id: UUID,
    ) -> dict[str, int]:
        dataset_item_ids = [
            dataset_item_id
            for dataset_item_id, dataset_item in self.dataset_items.items()
            if dataset_item.workspace_id == workspace_id
        ]
        dataset_version_ids = [
            dataset_version_id
            for dataset_version_id, dataset_version in self.dataset_versions.items()
            if dataset_version.workspace_id == workspace_id
        ]
        training_run_ids = [
            training_run_id
            for training_run_id, training_run in self.training_runs.items()
            if training_run.workspace_id == workspace_id
        ]
        model_candidate_ids = [
            model_candidate_id
            for model_candidate_id, model_candidate in self.model_candidates.items()
            if model_candidate.workspace_id == workspace_id
        ]
        benchmark_evaluation_ids = [
            benchmark_evaluation_id
            for benchmark_evaluation_id, benchmark_evaluation in self.benchmark_evaluations.items()
            if benchmark_evaluation.workspace_id == workspace_id
        ]
        artifact_owner_ids = set(dataset_version_ids) | set(training_run_ids) | set(
            benchmark_evaluation_ids
        )
        artifact_ids = [
            artifact_id
            for artifact_id, artifact in self.artifacts.items()
            if artifact.owner_id in artifact_owner_ids
        ]
        counts = super().remove_dataset_and_model_evidence_for_workspace(workspace_id)
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute("DELETE FROM dataset_items WHERE workspace_id = %s", (workspace_id,))
            for record_type, record_ids in (
                ("dataset_item", dataset_item_ids),
                ("dataset_version", dataset_version_ids),
                ("training_run", training_run_ids),
                ("benchmark_evaluation", benchmark_evaluation_ids),
                ("model_candidate", model_candidate_ids),
                ("artifact", artifact_ids),
            ):
                for record_id in record_ids:
                    cursor.execute(
                        "DELETE FROM repository_records WHERE record_type = %s AND record_id = %s",
                        (record_type, str(record_id)),
                    )
        return counts

    def save_model_candidate(self, model_candidate: ModelCandidateResponse):
        response = super().save_model_candidate(model_candidate)
        self._persist_model("model_candidate", response.model_candidate_id, response)
        return response

    def save_artifact(self, artifact: ArtifactResponse):
        response = super().save_artifact(artifact)
        self._persist_model("artifact", response.artifact_id, response)
        return response

    def _connect(self):
        import psycopg

        return psycopg.connect(self.database_url)

    def _load_records(self) -> None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT record_type, record_id, payload FROM repository_records")
            rows = cursor.fetchall()
        for record_type, record_id, payload in rows:
            if isinstance(payload, str):
                payload = json.loads(payload)
            if record_type == "user":
                self.users.add(UUID(record_id))
            elif record_type == "workspace":
                self.workspaces[UUID(record_id)] = WorkspaceRecord(
                    workspace_id=UUID(payload["workspace_id"]),
                    data_use_agreement_status=payload["data_use_agreement_status"],
                    data_use_agreement_terms_version=payload["data_use_agreement_terms_version"],
                    data_use_agreement_accepted_at=_parse_datetime(
                        payload["data_use_agreement_accepted_at"]
                    ),
                )
            elif record_type == "workspace_membership":
                self.memberships.append(
                    WorkspaceMembershipRecord(
                        user_id=UUID(payload["user_id"]),
                        workspace_id=UUID(payload["workspace_id"]),
                        role=payload["role"],
                        status=payload["status"],
                    )
                )
            elif record_type in MODEL_RECORD_TYPES:
                model = MODEL_RECORD_TYPES[record_type].model_validate(payload)
                self._assign_loaded_model(record_type, model)

    def _assign_loaded_model(self, record_type: str, model: Any) -> None:
        if record_type == "apiary":
            self.apiaries[model.apiary_id] = model
        elif record_type == "hive":
            self.hives[model.hive_id] = model
        elif record_type == "hive_configuration":
            self.hive_configurations[model.hive_id] = model
        elif record_type == "inspection":
            self.inspections[model.inspection_id] = model
        elif record_type == "inspection_photo":
            self.inspection_photos[model.inspection_photo_id] = model
        elif record_type == "analysis_run":
            self.analysis_runs[model.analysis_run_id] = model
        elif record_type == "analysis_result":
            self.analysis_results[model.analysis_run_id] = model
        elif record_type == "annotation":
            self.annotations[model.annotation_id] = model
        elif record_type == "review_decision":
            self.review_decisions[model.review_decision_id] = model
        elif record_type == "dataset_labelling_session":
            self.dataset_labelling_sessions[model.labelling_session_id] = model
        elif record_type == "training_crop":
            self.training_crops[model.training_crop_id] = model
        elif record_type == "training_crop_ellipse":
            self.training_crop_ellipses[model.annotation_id] = model
        elif record_type == "dataset_item":
            self.dataset_items[model.dataset_item_id] = model
        elif record_type == "dataset_version":
            self.dataset_versions[model.dataset_version_id] = model
        elif record_type == "training_run":
            self.training_runs[model.training_run_id] = model
        elif record_type == "benchmark_evaluation":
            self.benchmark_evaluations[model.benchmark_evaluation_id] = model
        elif record_type == "model_candidate":
            self.model_candidates[model.model_candidate_id] = model
        elif record_type == "artifact":
            self.artifacts[model.artifact_id] = model

    def _persist_core_identity(self, user_id: UUID, workspace_id: UUID) -> None:
        self._persist_payload("user", user_id, {"user_id": str(user_id)})
        self._persist_workspace(workspace_id)
        self._upsert_workspace_projection(workspace_id)
        for membership in self.memberships:
            if membership.user_id == user_id and membership.workspace_id == workspace_id:
                self._persist_payload(
                    "workspace_membership",
                    f"{membership.user_id}:{membership.workspace_id}:{membership.role}",
                    _jsonable(asdict(membership)),
                )
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO users (id, display_name, contact_identifier)
                VALUES (%s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                (user_id, "HiveSight Dev User", "dev-user"),
            )
            cursor.execute(
                """
                INSERT INTO workspaces (id, data_use_agreement_status, data_use_agreement_terms_version, data_use_agreement_accepted_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    data_use_agreement_status = EXCLUDED.data_use_agreement_status,
                    data_use_agreement_terms_version = EXCLUDED.data_use_agreement_terms_version,
                    data_use_agreement_accepted_at = EXCLUDED.data_use_agreement_accepted_at
                """,
                (
                    workspace_id,
                    self.workspaces[workspace_id].data_use_agreement_status,
                    self.workspaces[workspace_id].data_use_agreement_terms_version,
                    self.workspaces[workspace_id].data_use_agreement_accepted_at,
                ),
            )
            cursor.execute(
                """
                INSERT INTO workspace_memberships (id, user_id, workspace_id, role, status)
                VALUES (%s, %s, %s, 'owner', 'active')
                ON CONFLICT (user_id, workspace_id, role) DO NOTHING
                """,
                (
                    uuid5(NAMESPACE_URL, f"hivesight:membership:{user_id}:{workspace_id}:owner"),
                    user_id,
                    workspace_id,
                ),
            )
    def _upsert_seeded_user_projection(self, seed: DevUserSeed) -> None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO users (id, display_name, contact_identifier)
                VALUES (%s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    display_name = EXCLUDED.display_name,
                    contact_identifier = EXCLUDED.contact_identifier
                """,
                (seed.user_id, seed.display_name, seed.code),
            )
            cursor.execute(
                """
                INSERT INTO workspace_memberships (id, user_id, workspace_id, role, status)
                VALUES (%s, %s, %s, %s, 'active')
                ON CONFLICT (user_id, workspace_id, role) DO UPDATE SET status = 'active'
                """,
                (
                    uuid5(
                        NAMESPACE_URL,
                        f"hivesight:membership:{seed.user_id}:{seed.workspace_id}:{seed.workspace_membership_role}",
                    ),
                    seed.user_id,
                    seed.workspace_id,
                    seed.workspace_membership_role,
                ),
            )
            cursor.execute("DELETE FROM internal_capabilities WHERE user_id = %s", (seed.user_id,))
            for capability, enabled in (
                ("reviewer", seed.reviewer_capability),
                ("dataset_curator", seed.dataset_curator_capability),
            ):
                if enabled:
                    cursor.execute(
                        """
                        INSERT INTO internal_capabilities (id, user_id, capability, status)
                        VALUES (%s, %s, %s, 'active')
                        ON CONFLICT (user_id, capability) DO UPDATE SET status = 'active'
                        """,
                        (
                            uuid5(
                                NAMESPACE_URL,
                                f"hivesight:capability:{seed.user_id}:{capability}",
                            ),
                            seed.user_id,
                            capability,
                        ),
                    )

    def _persist_workspace(self, workspace_id: UUID) -> None:
        workspace = self.workspaces[workspace_id]
        self._persist_payload("workspace", workspace_id, _jsonable(asdict(workspace)))

    def _upsert_workspace_projection(self, workspace_id: UUID) -> None:
        workspace = self.workspaces[workspace_id]
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO workspaces (
                    id,
                    data_use_agreement_status,
                    data_use_agreement_terms_version,
                    data_use_agreement_accepted_at
                )
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    data_use_agreement_status = EXCLUDED.data_use_agreement_status,
                    data_use_agreement_terms_version = EXCLUDED.data_use_agreement_terms_version,
                    data_use_agreement_accepted_at = EXCLUDED.data_use_agreement_accepted_at
                """,
                (
                    workspace.workspace_id,
                    workspace.data_use_agreement_status,
                    workspace.data_use_agreement_terms_version,
                    workspace.data_use_agreement_accepted_at,
                ),
            )

    def _persist_model(self, record_type: str, record_id: UUID, model: Any) -> None:
        self._persist_payload(record_type, record_id, model.model_dump(mode="json"))

    def _persist_payload(self, record_type: str, record_id: UUID | str, payload: dict[str, Any]) -> None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                    INSERT INTO repository_records (record_type, record_id, payload, updated_at)
                    VALUES (%s, %s, %s::jsonb, now())
                    ON CONFLICT (record_type, record_id) DO UPDATE SET
                        payload = EXCLUDED.payload,
                        updated_at = EXCLUDED.updated_at
                    """,
                (record_type, str(record_id), json.dumps(_jsonable(payload))),
            )

    def _delete_record(self, record_type: str, record_id: UUID) -> None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM repository_records WHERE record_type = %s AND record_id = %s",
                (record_type, str(record_id)),
            )

    def _upsert_apiary_projection(self, apiary: ApiaryResponse) -> None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                    INSERT INTO apiaries (id, workspace_id, name)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name
                    """,
                (apiary.apiary_id, apiary.workspace_id, apiary.name),
            )

    def _upsert_hive_projection(self, hive: HiveResponse) -> None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                    INSERT INTO hives (id, workspace_id, apiary_id, name)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name
                    """,
                (hive.hive_id, hive.workspace_id, hive.apiary_id, hive.name),
            )

    def _upsert_hive_configuration_projection(
        self,
        configuration: HiveConfigurationResponse,
    ) -> None:
        frame_standard = configuration.frame_standard
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                    """
                    INSERT INTO frame_standards (
                        id, display_name, hive_type, frame_use, top_bar_length_mm,
                        bottom_bar_length_mm, side_bar_height_mm, measurement_unit, source_note, status
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (
                        frame_standard.frame_standard_id,
                        frame_standard.display_name,
                        frame_standard.hive_type,
                        frame_standard.frame_use,
                        frame_standard.top_bar_length_mm,
                        frame_standard.bottom_bar_length_mm,
                        frame_standard.side_bar_height_mm,
                        frame_standard.measurement_unit,
                        frame_standard.source_note,
                        frame_standard.status,
                    ),
            )
            cursor.execute("DELETE FROM hive_configurations WHERE hive_id = %s", (configuration.hive_id,))
            cursor.execute(
                    """
                    INSERT INTO hive_configurations (
                        id, hive_id, workspace_id, hive_type, frame_use, frame_standard_id, notes,
                        status, effective_from, configured_by_user_id, configured_at, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        configuration.hive_configuration_id,
                        configuration.hive_id,
                        configuration.workspace_id,
                        configuration.hive_type,
                        configuration.frame_use,
                        configuration.frame_standard_id,
                        configuration.notes,
                        configuration.status,
                        configuration.effective_from,
                        configuration.configured_by_user_id,
                        configuration.configured_at,
                        configuration.updated_at,
                    ),
            )

    def _upsert_inspection_projection(self, inspection: InspectionResponse) -> None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                    INSERT INTO inspections (id, workspace_id, hive_id, inspection_date, intent)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        inspection_date = EXCLUDED.inspection_date,
                        intent = EXCLUDED.intent,
                        updated_at = now()
                    """,
                (
                    inspection.inspection_id,
                    inspection.workspace_id,
                    inspection.hive_id,
                    inspection.inspection_date,
                    inspection.intent,
                ),
            )

    def _upsert_source_image_and_photo_projection(
        self,
        photo: InspectionPhotoResponse,
        width_px: int,
        height_px: int,
        content_hash: str,
        content_hash_algorithm: str,
    ) -> None:
        source_image_id = _source_image_id_for_photo(photo.inspection_photo_id)
        human_id = self._human_readable_id(
            table="source_images",
            id_column="id",
            id_value=source_image_id,
            human_column="human_readable_id",
            sequence="source_image_human_id_seq",
            prefix="HS-SI",
        )
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                    INSERT INTO source_images (
                        id, human_readable_id, workspace_id, source_type, object_key,
                        original_filename, media_type, file_size_bytes, source_width_px,
                        source_height_px, content_hash, content_hash_algorithm,
                        permission_status, metadata_minimisation_status, metadata_checked_at,
                        lifecycle_status, created_at
                    )
                    VALUES (%s, %s, %s, 'inspection_photo', %s, %s, %s, %s, %s, %s, %s, %s,
                        'workspace_data_use_agreement_accepted', 'raw_metadata_discarded', %s,
                        'accepted', %s)
                    ON CONFLICT (id) DO UPDATE SET
                        object_key = EXCLUDED.object_key,
                        original_filename = EXCLUDED.original_filename,
                        media_type = EXCLUDED.media_type,
                        file_size_bytes = EXCLUDED.file_size_bytes
                    """,
                (
                    source_image_id,
                    human_id,
                    photo.workspace_id,
                    photo.original_object_key,
                    photo.filename,
                    photo.content_type,
                    photo.size_bytes,
                    width_px,
                    height_px,
                    content_hash,
                    content_hash_algorithm,
                    photo.uploaded_at,
                    photo.uploaded_at,
                ),
            )
            cursor.execute(
                """
                    INSERT INTO inspection_photos (
                        id, workspace_id, source_image_id, inspection_id, upload_status,
                        uploaded_at, uploaded_by_user_id
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET upload_status = EXCLUDED.upload_status
                    """,
                (
                    photo.inspection_photo_id,
                    photo.workspace_id,
                    source_image_id,
                    photo.inspection_id,
                    photo.upload_status,
                    photo.uploaded_at,
                    photo.uploaded_by_user_id,
                ),
            )

    def _upsert_training_crop_projection(self, crop: TrainingCropResponse) -> None:
        source_image_id = self._source_image_id_for_photo_id(crop.inspection_photo_id)
        human_id = self._human_readable_id(
            table="training_crops",
            id_column="id",
            id_value=crop.training_crop_id,
            human_column="human_readable_id",
            sequence="training_crop_human_id_seq",
            prefix="HS-TC",
        )
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                    """
                    INSERT INTO training_crops (
                        id, human_readable_id, workspace_id, source_image_id, inspection_photo_id,
                        crop_x, crop_y, crop_width, crop_height, source_image_width_px,
                        source_image_height_px, crop_image_width_px, crop_image_height_px,
                        curriculum_stage, review_status, visible_bee_status, exclusion_reason, notes,
                        created_by_user_id, created_at, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        review_status = EXCLUDED.review_status,
                        visible_bee_status = EXCLUDED.visible_bee_status,
                        exclusion_reason = EXCLUDED.exclusion_reason,
                        notes = EXCLUDED.notes,
                        updated_at = EXCLUDED.updated_at
                    """,
                    (
                        crop.training_crop_id,
                        human_id,
                        crop.workspace_id,
                        source_image_id,
                        crop.inspection_photo_id,
                        crop.crop_x,
                        crop.crop_y,
                        crop.crop_width,
                        crop.crop_height,
                        crop.source_image_width_px,
                        crop.source_image_height_px,
                        crop.crop_image_width_px,
                        crop.crop_image_height_px,
                        crop.curriculum_stage,
                        crop.review_status,
                        crop.visible_bee_status,
                        crop.exclusion_reason,
                        crop.notes,
                        crop.created_by_user_id,
                        crop.created_at,
                        crop.updated_at,
                    ),
            )

    def _upsert_ellipse_projection(self, ellipse: OrientedBeeEllipseResponse) -> None:
        source_image_id = self._source_image_id_for_photo_id(ellipse.inspection_photo_id)
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                    INSERT INTO oriented_bee_ellipses (
                        id, workspace_id, source_image_id, inspection_photo_id, training_crop_id,
                        annotation_type, center_x, center_y, radius_x, radius_y, rotation_degrees,
                        coordinate_space, source_image_width_px, source_image_height_px, source,
                        created_by_user_id, created_at, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        annotation_type = EXCLUDED.annotation_type,
                        center_x = EXCLUDED.center_x,
                        center_y = EXCLUDED.center_y,
                        radius_x = EXCLUDED.radius_x,
                        radius_y = EXCLUDED.radius_y,
                        rotation_degrees = EXCLUDED.rotation_degrees,
                        updated_at = EXCLUDED.updated_at
                    """,
                (
                    ellipse.annotation_id,
                    ellipse.workspace_id,
                    source_image_id,
                    ellipse.inspection_photo_id,
                    ellipse.training_crop_id,
                    ellipse.annotation_type,
                    ellipse.center_x,
                    ellipse.center_y,
                    ellipse.radius_x,
                    ellipse.radius_y,
                    ellipse.rotation_degrees,
                    ellipse.coordinate_space,
                    ellipse.source_image_width_px,
                    ellipse.source_image_height_px,
                    ellipse.source,
                    ellipse.created_by_user_id,
                    ellipse.created_at,
                    ellipse.updated_at,
                ),
            )

    def _upsert_dataset_item_projection(self, dataset_item: DatasetItemResponse) -> None:
        source_image_id = self._source_image_id_for_photo_id(dataset_item.inspection_photo_id)
        human_id = self._human_readable_id(
            table="dataset_items",
            id_column="id",
            id_value=dataset_item.dataset_item_id,
            human_column="human_readable_id",
            sequence="dataset_item_human_id_seq",
            prefix="HS-DI",
        )
        hive_configuration = (
            dataset_item.provenance.hive_configuration.model_dump(mode="json")
            if dataset_item.provenance and dataset_item.provenance.hive_configuration
            else None
        )
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                    """
                    INSERT INTO dataset_items (
                        id, human_readable_id, workspace_id, source_image_id, inspection_photo_id,
                        labelling_session_id, training_crop_id, source_evidence_type, dataset_role, status,
                        source_group_key, image_quality_status, reviewed_annotation_ids, ellipse_snapshot,
                        provenance_snapshot, permission_snapshot, hive_configuration_snapshot,
                        assigned_by_user_id, assigned_at, assignment_note, exclusion_reason, benchmark_protected
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'active', %s, %s, %s::jsonb, %s::jsonb,
                        %s::jsonb, %s::jsonb, %s::jsonb, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (
                        dataset_item.dataset_item_id,
                        human_id,
                        dataset_item.workspace_id,
                        source_image_id,
                        dataset_item.inspection_photo_id,
                        dataset_item.labelling_session_id,
                        dataset_item.training_crop_id,
                        dataset_item.source_evidence_type,
                        dataset_item.dataset_role,
                        dataset_item.source_group_key,
                        dataset_item.image_quality_status,
                        json.dumps([str(item) for item in dataset_item.reviewed_annotation_ids]),
                        json.dumps(
                            [
                                snapshot.model_dump(mode="json")
                                for snapshot in dataset_item.reviewed_ellipse_snapshots
                            ]
                        ),
                        json.dumps(
                            dataset_item.provenance.model_dump(mode="json")
                            if dataset_item.provenance
                            else {}
                        ),
                        json.dumps(
                            {"permission_status": dataset_item.permission_status}
                        ),
                        json.dumps(hive_configuration),
                        dataset_item.assigned_by_user_id,
                        dataset_item.assigned_at,
                        dataset_item.assignment_note,
                        dataset_item.exclusion_reason,
                        dataset_item.benchmark_protected,
                    ),
            )

    def _source_image_id_for_photo_id(self, inspection_photo_id: UUID) -> UUID:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT source_image_id FROM inspection_photos WHERE id = %s",
                (inspection_photo_id,),
            )
            row = cursor.fetchone()
        if row is None:
            return _source_image_id_for_photo(inspection_photo_id)
        return row[0]

    def _human_readable_id(
        self,
        *,
        table: str,
        id_column: str,
        id_value: UUID,
        human_column: str,
        sequence: str,
        prefix: str,
    ) -> str:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                f"SELECT {human_column} FROM {table} WHERE {id_column} = %s",
                (id_value,),
            )
            row = cursor.fetchone()
            if row is not None:
                return row[0]
            cursor.execute(f"SELECT nextval('{sequence}')")
            value = cursor.fetchone()[0]
        return f"{prefix}-{value:06d}"


def _source_image_id_for_photo(inspection_photo_id: UUID) -> UUID:
    return uuid5(NAMESPACE_URL, f"hivesight:source-image:{inspection_photo_id}")


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value


def _parse_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value)
