from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from hive_sight_core_api.models import (
    ApiaryResponse,
    DevUserResponse,
    HiveResponse,
)


@dataclass(frozen=True)
class DevUserSeed:
    code: str
    user_id: UUID
    display_name: str
    description: str
    workspace_id: UUID
    workspace_display_name: str
    apiary_id: UUID
    apiary_name: str
    hive_id: UUID
    hive_name: str
    workspace_membership_role: str = "owner"
    reviewer_capability: bool = False
    dataset_curator_capability: bool = False
    contributor_access_scope: str = "none"
    is_default: bool = False


DEV_USERS: tuple[DevUserSeed, ...] = (
    DevUserSeed(
        code="DEV-OWNER-CURATOR",
        user_id=UUID("00000000-0000-0000-0000-000000000101"),
        display_name="Default Dev Owner Curator",
        description="Continuity user for current local owner, curator, and reviewer workflows.",
        workspace_id=UUID("00000000-0000-0000-0000-000000000201"),
        workspace_display_name="Dev Owner Curator Workspace",
        apiary_id=UUID("00000000-0000-0000-0000-000000000301"),
        apiary_name="Dev Owner Curator Apiary",
        hive_id=UUID("00000000-0000-0000-0000-000000000401"),
        hive_name="Dev Owner Curator Hive",
        reviewer_capability=True,
        dataset_curator_capability=True,
        is_default=True,
    ),
    DevUserSeed(
        code="OWNER-A",
        user_id=UUID("00000000-0000-0000-0000-000000000102"),
        display_name="Workspace Owner A",
        description="Ordinary beekeeper owner with no internal capability.",
        workspace_id=UUID("00000000-0000-0000-0000-000000000202"),
        workspace_display_name="Owner A Workspace",
        apiary_id=UUID("00000000-0000-0000-0000-000000000302"),
        apiary_name="Owner A Apiary",
        hive_id=UUID("00000000-0000-0000-0000-000000000402"),
        hive_name="Owner A Hive",
    ),
    DevUserSeed(
        code="OWNER-B",
        user_id=UUID("00000000-0000-0000-0000-000000000103"),
        display_name="Workspace Owner B",
        description="Second ordinary beekeeper owner for workspace separation checks.",
        workspace_id=UUID("00000000-0000-0000-0000-000000000203"),
        workspace_display_name="Owner B Workspace",
        apiary_id=UUID("00000000-0000-0000-0000-000000000303"),
        apiary_name="Owner B Apiary",
        hive_id=UUID("00000000-0000-0000-0000-000000000403"),
        hive_name="Owner B Hive",
    ),
    DevUserSeed(
        code="CURATOR-1",
        user_id=UUID("00000000-0000-0000-0000-000000000104"),
        display_name="Dataset Curator",
        description="Normal User with Dataset Curator internal capability.",
        workspace_id=UUID("00000000-0000-0000-0000-000000000204"),
        workspace_display_name="Dataset Curator Workspace",
        apiary_id=UUID("00000000-0000-0000-0000-000000000304"),
        apiary_name="Dataset Curator Apiary",
        hive_id=UUID("00000000-0000-0000-0000-000000000404"),
        hive_name="Dataset Curator Hive",
        dataset_curator_capability=True,
    ),
    DevUserSeed(
        code="REVIEWER-1",
        user_id=UUID("00000000-0000-0000-0000-000000000105"),
        display_name="Reviewer 1",
        description="Distinct reviewer identity for future blind-review paths.",
        workspace_id=UUID("00000000-0000-0000-0000-000000000205"),
        workspace_display_name="Reviewer 1 Workspace",
        apiary_id=UUID("00000000-0000-0000-0000-000000000305"),
        apiary_name="Reviewer 1 Apiary",
        hive_id=UUID("00000000-0000-0000-0000-000000000405"),
        hive_name="Reviewer 1 Hive",
        reviewer_capability=True,
    ),
    DevUserSeed(
        code="REVIEWER-2",
        user_id=UUID("00000000-0000-0000-0000-000000000106"),
        display_name="Reviewer 2",
        description="Second distinct reviewer identity for future blind-review paths.",
        workspace_id=UUID("00000000-0000-0000-0000-000000000206"),
        workspace_display_name="Reviewer 2 Workspace",
        apiary_id=UUID("00000000-0000-0000-0000-000000000306"),
        apiary_name="Reviewer 2 Apiary",
        hive_id=UUID("00000000-0000-0000-0000-000000000406"),
        hive_name="Reviewer 2 Hive",
        reviewer_capability=True,
    ),
    DevUserSeed(
        code="REVIEWER-3",
        user_id=UUID("00000000-0000-0000-0000-000000000107"),
        display_name="Reviewer 3 / Adjudicator",
        description="Third reviewer identity for future adjudication proof points.",
        workspace_id=UUID("00000000-0000-0000-0000-000000000207"),
        workspace_display_name="Reviewer 3 Workspace",
        apiary_id=UUID("00000000-0000-0000-0000-000000000307"),
        apiary_name="Reviewer 3 Apiary",
        hive_id=UUID("00000000-0000-0000-0000-000000000407"),
        hive_name="Reviewer 3 Hive",
        reviewer_capability=True,
    ),
    DevUserSeed(
        code="CONTRIBUTOR-1",
        user_id=UUID("00000000-0000-0000-0000-000000000108"),
        display_name="External Contributor",
        description="Contributor identity with its own Workspace and no broad foreign access.",
        workspace_id=UUID("00000000-0000-0000-0000-000000000208"),
        workspace_display_name="Contributor Workspace",
        apiary_id=UUID("00000000-0000-0000-0000-000000000308"),
        apiary_name="Contributor Apiary",
        hive_id=UUID("00000000-0000-0000-0000-000000000408"),
        hive_name="Contributor Hive",
    ),
    DevUserSeed(
        code="BASIC-OWNER",
        user_id=UUID("00000000-0000-0000-0000-000000000109"),
        display_name="Basic Workspace Owner",
        description="Valid owner User with no elevated internal capability.",
        workspace_id=UUID("00000000-0000-0000-0000-000000000209"),
        workspace_display_name="Basic Owner Workspace",
        apiary_id=UUID("00000000-0000-0000-0000-000000000309"),
        apiary_name="Basic Owner Apiary",
        hive_id=UUID("00000000-0000-0000-0000-000000000409"),
        hive_name="Basic Owner Hive",
    ),
)

DEFAULT_DEV_USER_ID = DEV_USERS[0].user_id
DEV_USER_IDS = frozenset(seed.user_id for seed in DEV_USERS)


def dev_user_response(seed: DevUserSeed) -> DevUserResponse:
    return DevUserResponse(
        user_id=seed.user_id,
        display_name=seed.display_name,
        dev_user_code=seed.code,
        description=seed.description,
        workspace_id=seed.workspace_id,
        workspace_display_name=seed.workspace_display_name,
        workspace_membership_role=seed.workspace_membership_role,
        reviewer_capability=seed.reviewer_capability,
        dataset_curator_capability=seed.dataset_curator_capability,
        contributor_access_scope=seed.contributor_access_scope,
        is_default=seed.is_default,
    )


def seeded_apiary(seed: DevUserSeed) -> ApiaryResponse:
    return ApiaryResponse(
        apiary_id=seed.apiary_id,
        workspace_id=seed.workspace_id,
        name=seed.apiary_name,
    )


def seeded_hive(seed: DevUserSeed) -> HiveResponse:
    return HiveResponse(
        hive_id=seed.hive_id,
        apiary_id=seed.apiary_id,
        workspace_id=seed.workspace_id,
        name=seed.hive_name,
    )


def accepted_at() -> datetime:
    return datetime(2026, 8, 3, tzinfo=UTC)
