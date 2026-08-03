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


def main() -> None:
    parser = argparse.ArgumentParser(description="HiveSight Core API database commands.")
    parser.add_argument("command", choices=("migrate", "seed-dev", "reset-dev", "reset-test"))
    args = parser.parse_args()
    database_url = load_settings().database_url
    if args.command == "migrate":
        apply_migrations(database_url)
    elif args.command == "seed-dev":
        seed_dev_data(database_url)
    elif args.command in {"reset-dev", "reset-test"}:
        reset_database(database_url)


if __name__ == "__main__":
    main()
