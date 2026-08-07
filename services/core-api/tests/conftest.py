import pytest

CATALOGUE_SEAM_MARKERS = frozenset({"api", "web"})


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    skip_non_api_catalogue = pytest.mark.skip(
        reason="Acceptance-catalogue scenario is not tagged for the Core API seam."
    )
    for item in items:
        marker_names = {marker.name for marker in item.iter_markers()}
        if should_skip_for_core_api_catalogue(marker_names, is_bdd_scenario=is_bdd_scenario(item)):
            item.add_marker(skip_non_api_catalogue)


def is_bdd_scenario(item: pytest.Item) -> bool:
    return hasattr(getattr(item, "obj", None), "__scenario__")


def should_skip_for_core_api_catalogue(
    marker_names: set[str],
    *,
    is_bdd_scenario: bool,
) -> bool:
    if not is_bdd_scenario:
        return False
    seam_markers = marker_names & CATALOGUE_SEAM_MARKERS
    return bool(seam_markers) and "api" not in seam_markers
