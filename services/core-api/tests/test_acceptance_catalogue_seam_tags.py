from conftest import should_skip_for_core_api_catalogue


def test_core_api_catalogue_runs_api_tagged_scenarios() -> None:
    assert should_skip_for_core_api_catalogue({"api"}, is_bdd_scenario=True) is False
    assert should_skip_for_core_api_catalogue({"api", "web"}, is_bdd_scenario=True) is False


def test_core_api_catalogue_skips_web_only_scenarios() -> None:
    assert should_skip_for_core_api_catalogue({"web"}, is_bdd_scenario=True) is True


def test_core_api_catalogue_leaves_legacy_untagged_scenarios_alone() -> None:
    assert should_skip_for_core_api_catalogue(set(), is_bdd_scenario=True) is False


def test_core_api_catalogue_leaves_non_bdd_tests_alone() -> None:
    assert should_skip_for_core_api_catalogue({"web"}, is_bdd_scenario=False) is False
