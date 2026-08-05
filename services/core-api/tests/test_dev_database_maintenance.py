from hive_sight_core_api.db import (
    DEV_OWNER_CURATOR_KEEP_APIARIES,
    should_prune_dev_owner_curator_apiary,
)


def test_dev_owner_apiary_prune_rule_keeps_only_named_local_apiaries() -> None:
    assert DEV_OWNER_CURATOR_KEEP_APIARIES == frozenset(
        {
            "Dev Owner Curator Apiary",
            "Pudseys",
        }
    )

    assert should_prune_dev_owner_curator_apiary("Dev Owner Curator Apiary") is False
    assert should_prune_dev_owner_curator_apiary("Pudseys") is False
    assert should_prune_dev_owner_curator_apiary("Slice 17 apiary 1785925315558") is True
    assert should_prune_dev_owner_curator_apiary("Acceptance apiary 1785925185005") is True
    assert should_prune_dev_owner_curator_apiary("Repository repo-1785925271216-training") is True
