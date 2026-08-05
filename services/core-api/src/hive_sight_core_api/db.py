from __future__ import annotations

import argparse
import json
from uuid import NAMESPACE_URL, uuid5
from urllib.parse import urlparse, urlunparse
from pathlib import Path

from hive_sight_core_api.dev_store import FRAME_STANDARDS
from hive_sight_core_api.dev_users import DEV_USERS, accepted_at
from hive_sight_core_api.settings import load_settings

MIGRATIONS_DIR = Path(__file__).with_name("migrations")
DEV_OWNER_CURATOR_KEEP_APIARIES = frozenset(("Dev Owner Curator Apiary", "Pudseys"))


class PostgresDependencyError(RuntimeError):
    pass


def _connect(database_url: str):
    try:
        import psycopg
    except ImportError as exc:  # pragma: no cover - exercised only before dependencies install.
        raise PostgresDependencyError(
            "Install Core API dependencies before running Postgres commands."
        ) from exc
    return psycopg.connect(database_url)


def _database_name(database_url: str) -> str:
    parsed = urlparse(database_url)
    return parsed.path.lstrip("/")


def _maintenance_database_url(database_url: str) -> str:
    parsed = urlparse(database_url)
    return urlunparse(parsed._replace(path="/postgres"))


def ensure_database_exists(database_url: str) -> None:
    database_name = _database_name(database_url)
    if not database_name:
        return
    try:
        import psycopg
        from psycopg import sql
    except ImportError as exc:  # pragma: no cover - exercised only before dependencies install.
        raise PostgresDependencyError(
            "Install Core API dependencies before running Postgres commands."
        ) from exc
    with psycopg.connect(_maintenance_database_url(database_url), autocommit=True) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (database_name,))
            if cursor.fetchone() is None:
                cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_name)))


def apply_migrations(database_url: str) -> None:
    ensure_database_exists(database_url)
    with _connect(database_url) as connection, connection.cursor() as cursor:
        cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version text PRIMARY KEY,
                    applied_at timestamptz NOT NULL DEFAULT now()
                )
                """
        )
        for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
            version = path.name
            cursor.execute("SELECT 1 FROM schema_migrations WHERE version = %s", (version,))
            if cursor.fetchone() is not None:
                continue
            cursor.execute(path.read_text(encoding="utf-8"))
            cursor.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (version,))


def reset_database(database_url: str) -> None:
    with _connect(database_url) as connection, connection.cursor() as cursor:
        cursor.execute("DROP SCHEMA public CASCADE")
        cursor.execute("CREATE SCHEMA public")
    apply_migrations(database_url)
    seed_dev_data(database_url)


def seed_dev_data(database_url: str) -> None:
    apply_migrations(database_url)
    with _connect(database_url) as connection, connection.cursor() as cursor:
        seed_time = accepted_at()
        for seed in DEV_USERS:
            user_id = str(seed.user_id)
            workspace_id = str(seed.workspace_id)
            cursor.execute(
                """
                    INSERT INTO users (id, display_name, contact_identifier)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        display_name = EXCLUDED.display_name,
                        contact_identifier = EXCLUDED.contact_identifier
                    """,
                (user_id, seed.display_name, seed.code),
            )
            cursor.execute(
                """
                    INSERT INTO repository_records (record_type, record_id, payload)
                    VALUES ('user', %s, %s::jsonb)
                    ON CONFLICT (record_type, record_id) DO UPDATE SET payload = EXCLUDED.payload
                    """,
                (user_id, json.dumps({"user_id": user_id})),
            )
            cursor.execute(
                """
                    INSERT INTO workspaces (
                        id,
                        display_name,
                        data_use_agreement_status,
                        data_use_agreement_terms_version,
                        data_use_agreement_accepted_at
                    )
                    VALUES (%s, %s, 'accepted', 'dev-seed', %s)
                    ON CONFLICT (id) DO UPDATE SET
                        display_name = EXCLUDED.display_name,
                        data_use_agreement_status = EXCLUDED.data_use_agreement_status,
                        data_use_agreement_terms_version = EXCLUDED.data_use_agreement_terms_version,
                        data_use_agreement_accepted_at = EXCLUDED.data_use_agreement_accepted_at
                    """,
                (workspace_id, seed.workspace_display_name, seed_time),
            )
            cursor.execute(
                """
                    INSERT INTO repository_records (record_type, record_id, payload)
                    VALUES ('workspace', %s, %s::jsonb)
                    ON CONFLICT (record_type, record_id) DO UPDATE SET payload = EXCLUDED.payload
                    """,
                (
                    workspace_id,
                    json.dumps(
                        {
                            "workspace_id": workspace_id,
                            "data_use_agreement_status": "accepted",
                            "data_use_agreement_terms_version": "dev-seed",
                            "data_use_agreement_accepted_at": seed_time.isoformat(),
                        }
                    ),
                ),
            )
            cursor.execute(
                """
                    INSERT INTO workspace_memberships (id, user_id, workspace_id, role, status)
                    VALUES (%s, %s, %s, %s, 'active')
                    ON CONFLICT (user_id, workspace_id, role) DO UPDATE SET status = 'active'
                    """,
                (
                    str(
                        uuid5(
                            NAMESPACE_URL,
                            f"hivesight:membership:{user_id}:{workspace_id}:{seed.workspace_membership_role}",
                        )
                    ),
                    user_id,
                    workspace_id,
                    seed.workspace_membership_role,
                ),
            )
            cursor.execute(
                """
                    INSERT INTO repository_records (record_type, record_id, payload)
                    VALUES ('workspace_membership', %s, %s::jsonb)
                    ON CONFLICT (record_type, record_id) DO UPDATE SET payload = EXCLUDED.payload
                    """,
                (
                    f"{user_id}:{workspace_id}:{seed.workspace_membership_role}",
                    json.dumps(
                        {
                            "user_id": user_id,
                            "workspace_id": workspace_id,
                            "role": seed.workspace_membership_role,
                            "status": "active",
                        }
                    ),
                ),
            )
            cursor.execute(
                """
                    INSERT INTO apiaries (id, workspace_id, name)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name
                    """,
                (str(seed.apiary_id), workspace_id, seed.apiary_name),
            )
            cursor.execute(
                """
                    INSERT INTO repository_records (record_type, record_id, payload)
                    VALUES ('apiary', %s, %s::jsonb)
                    ON CONFLICT (record_type, record_id) DO UPDATE SET payload = EXCLUDED.payload
                    """,
                (
                    str(seed.apiary_id),
                    json.dumps(
                        {
                            "apiary_id": str(seed.apiary_id),
                            "workspace_id": workspace_id,
                            "name": seed.apiary_name,
                        }
                    ),
                ),
            )
            cursor.execute(
                """
                    INSERT INTO hives (id, workspace_id, apiary_id, name)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name
                    """,
                (str(seed.hive_id), workspace_id, str(seed.apiary_id), seed.hive_name),
            )
            cursor.execute(
                """
                    INSERT INTO repository_records (record_type, record_id, payload)
                    VALUES ('hive', %s, %s::jsonb)
                    ON CONFLICT (record_type, record_id) DO UPDATE SET payload = EXCLUDED.payload
                    """,
                (
                    str(seed.hive_id),
                    json.dumps(
                        {
                            "hive_id": str(seed.hive_id),
                            "apiary_id": str(seed.apiary_id),
                            "workspace_id": workspace_id,
                            "name": seed.hive_name,
                        }
                    ),
                ),
            )
            cursor.execute("DELETE FROM internal_capabilities WHERE user_id = %s", (user_id,))
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
                            str(
                                uuid5(
                                    NAMESPACE_URL,
                                    f"hivesight:capability:{user_id}:{capability}",
                                )
                            ),
                            user_id,
                            capability,
                        ),
                    )
        for frame_standard in FRAME_STANDARDS:
            cursor.execute(
                """
                    INSERT INTO frame_standards (
                        id,
                        display_name,
                        hive_type,
                        frame_use,
                        top_bar_length_mm,
                        bottom_bar_length_mm,
                        side_bar_height_mm,
                        measurement_unit,
                        source_note,
                        status
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        display_name = EXCLUDED.display_name,
                        hive_type = EXCLUDED.hive_type,
                        frame_use = EXCLUDED.frame_use,
                        top_bar_length_mm = EXCLUDED.top_bar_length_mm,
                        bottom_bar_length_mm = EXCLUDED.bottom_bar_length_mm,
                        side_bar_height_mm = EXCLUDED.side_bar_height_mm,
                        measurement_unit = EXCLUDED.measurement_unit,
                        source_note = EXCLUDED.source_note,
                        status = EXCLUDED.status
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


def should_prune_dev_owner_curator_apiary(name: str) -> bool:
    return name not in DEV_OWNER_CURATOR_KEEP_APIARIES


def prune_dev_owner_curator_apiaries(database_url: str) -> dict[str, int]:
    apply_migrations(database_url)
    workspace_id = str(DEV_USERS[0].workspace_id)
    with _connect(database_url) as connection, connection.cursor() as cursor:
        cursor.execute(
            "SELECT id FROM apiaries WHERE workspace_id = %s AND name <> ALL(%s)",
            (workspace_id, list(DEV_OWNER_CURATOR_KEEP_APIARIES)),
        )
        apiary_ids = [str(row[0]) for row in cursor.fetchall()]
        if not apiary_ids:
            return _empty_prune_counts()

        ids = _dev_owner_curator_descendant_ids(cursor, apiary_ids)
        counts: dict[str, int] = {}
        counts["varroa_reviews_removed"] = _delete_uuid_values(
            cursor,
            "varroa_review_outcomes",
            "id",
            ids["varroa_review_outcomes"],
        )
        counts["dataset_items_removed"] = _delete_uuid_values(
            cursor,
            "dataset_items",
            "id",
            ids["dataset_items"],
        )
        counts["bee_ellipses_removed"] = _delete_uuid_values(
            cursor,
            "oriented_bee_ellipses",
            "id",
            ids["oriented_bee_ellipses"],
        )
        counts["training_crops_removed"] = _delete_uuid_values(
            cursor,
            "training_crops",
            "id",
            ids["training_crops"],
        )
        counts["inspection_photos_removed"] = _delete_uuid_values(
            cursor,
            "inspection_photos",
            "id",
            ids["inspection_photos"],
        )
        counts["source_images_removed"] = _delete_uuid_values(
            cursor,
            "source_images",
            "id",
            ids["source_images"],
        )
        counts["inspections_removed"] = _delete_uuid_values(
            cursor,
            "inspections",
            "id",
            ids["inspections"],
        )
        _delete_uuid_values(cursor, "hive_configurations", "hive_id", ids["hives"])
        counts["hives_removed"] = _delete_uuid_values(cursor, "hives", "id", ids["hives"])
        counts["apiaries_removed"] = _delete_uuid_values(cursor, "apiaries", "id", ids["apiaries"])
        counts["repository_records_removed"] = _delete_dev_owner_curator_repository_records(
            cursor,
            ids,
        )
        return counts


def _empty_prune_counts() -> dict[str, int]:
    return {
        "apiaries_removed": 0,
        "hives_removed": 0,
        "inspections_removed": 0,
        "inspection_photos_removed": 0,
        "source_images_removed": 0,
        "training_crops_removed": 0,
        "bee_ellipses_removed": 0,
        "dataset_items_removed": 0,
        "varroa_reviews_removed": 0,
        "repository_records_removed": 0,
    }


def _dev_owner_curator_descendant_ids(cursor, apiary_ids: list[str]) -> dict[str, list[str]]:
    ids: dict[str, list[str]] = {"apiaries": apiary_ids}
    ids["hives"] = _select_uuid_values(cursor, "hives", "apiary_id", apiary_ids)
    ids["inspections"] = _select_uuid_values(cursor, "inspections", "hive_id", ids["hives"])
    ids["inspection_photos"] = _select_uuid_values(
        cursor,
        "inspection_photos",
        "inspection_id",
        ids["inspections"],
    )
    ids["source_images"] = _select_uuid_values(
        cursor,
        "inspection_photos",
        "id",
        ids["inspection_photos"],
        selected_column="source_image_id",
    )
    ids["training_crops"] = sorted(
        set(_select_uuid_values(cursor, "training_crops", "inspection_photo_id", ids["inspection_photos"]))
        | set(_select_uuid_values(cursor, "training_crops", "source_image_id", ids["source_images"]))
    )
    ids["oriented_bee_ellipses"] = sorted(
        set(
            _select_uuid_values(
                cursor,
                "oriented_bee_ellipses",
                "training_crop_id",
                ids["training_crops"],
            )
        )
        | set(
            _select_uuid_values(
                cursor,
                "oriented_bee_ellipses",
                "inspection_photo_id",
                ids["inspection_photos"],
            )
        )
    )
    ids["dataset_items"] = sorted(
        set(_select_uuid_values(cursor, "dataset_items", "training_crop_id", ids["training_crops"]))
        | set(_select_uuid_values(cursor, "dataset_items", "inspection_photo_id", ids["inspection_photos"]))
        | set(_select_uuid_values(cursor, "dataset_items", "source_image_id", ids["source_images"]))
    )
    ids["varroa_review_outcomes"] = sorted(
        set(
            _select_uuid_values(
                cursor,
                "varroa_review_outcomes",
                "training_crop_id",
                ids["training_crops"],
            )
        )
        | set(
            _select_uuid_values(
                cursor,
                "varroa_review_outcomes",
                "inspection_photo_id",
                ids["inspection_photos"],
            )
        )
        | set(
            _select_uuid_values(
                cursor,
                "varroa_review_outcomes",
                "bee_annotation_id",
                ids["oriented_bee_ellipses"],
            )
        )
    )
    return ids


def _select_uuid_values(
    cursor,
    table: str,
    column: str,
    values: list[str],
    *,
    selected_column: str = "id",
) -> list[str]:
    if not values:
        return []
    cursor.execute(
        f"SELECT {selected_column} FROM {table} WHERE {column} = ANY(%s::uuid[])",
        (values,),
    )
    return [str(row[0]) for row in cursor.fetchall()]


def _delete_uuid_values(cursor, table: str, column: str, values: list[str]) -> int:
    if not values:
        return 0
    cursor.execute(
        f"DELETE FROM {table} WHERE {column} = ANY(%s::uuid[])",
        (values,),
    )
    return cursor.rowcount


def _delete_dev_owner_curator_repository_records(cursor, ids: dict[str, list[str]]) -> int:
    record_type_by_key = {
        "apiaries": "apiary",
        "hives": "hive",
        "inspections": "inspection",
        "inspection_photos": "inspection_photo",
        "source_images": "source_image",
        "training_crops": "training_crop",
        "oriented_bee_ellipses": "training_crop_ellipse",
        "dataset_items": "dataset_item",
        "varroa_review_outcomes": "varroa_review_outcome",
    }
    removed = 0
    for key, record_type in record_type_by_key.items():
        for record_id in ids[key]:
            cursor.execute(
                "DELETE FROM repository_records WHERE record_type = %s AND record_id = %s",
                (record_type, record_id),
            )
            removed += cursor.rowcount
    return removed


def main() -> None:
    parser = argparse.ArgumentParser(description="HiveSight Core API database commands.")
    parser.add_argument(
        "command",
        choices=("migrate", "seed-dev", "reset-dev", "reset-test", "prune-dev-owner-apiaries"),
    )
    args = parser.parse_args()
    settings = load_settings()
    database_url = settings.database_url
    if args.command == "migrate":
        apply_migrations(database_url)
    elif args.command == "seed-dev":
        seed_dev_data(database_url)
    elif args.command in {"reset-dev", "reset-test"}:
        reset_database(database_url)
    elif args.command == "prune-dev-owner-apiaries":
        if settings.database_purpose != "dev":
            raise SystemExit("Dev Owner apiary cleanup is only allowed against the dev database.")
        print(json.dumps(prune_dev_owner_curator_apiaries(database_url), sort_keys=True))


if __name__ == "__main__":
    main()
