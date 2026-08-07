from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
ACCEPTANCE_FEATURE_ROOT = REPO_ROOT / "acceptance" / "features"
INVENTORY_PATH = REPO_ROOT / "architecture" / "acceptance-catalogue-inventory.md"
SUPPORTED_SEAM_TAGS = frozenset({"@api", "@web"})


def test_canonical_acceptance_features_declare_supported_seams() -> None:
    feature_paths = sorted(ACCEPTANCE_FEATURE_ROOT.glob("*/*.feature"))

    assert feature_paths, "Expected at least one canonical acceptance catalogue feature."

    for feature_path in feature_paths:
        tags = _feature_level_tags(feature_path)
        assert tags, f"{feature_path.relative_to(REPO_ROOT)} is missing a seam tag."
        assert tags <= SUPPORTED_SEAM_TAGS, (
            f"{feature_path.relative_to(REPO_ROOT)} declares unsupported seam tags: "
            f"{', '.join(sorted(tags - SUPPORTED_SEAM_TAGS))}"
        )


def test_acceptance_inventory_lists_canonical_catalogue_features() -> None:
    inventory = INVENTORY_PATH.read_text(encoding="utf8")

    for feature_path in sorted(ACCEPTANCE_FEATURE_ROOT.glob("*/*.feature")):
        assert str(feature_path.relative_to(REPO_ROOT)) in inventory


def test_acceptance_inventory_lists_legacy_api_features_and_browser_specs() -> None:
    inventory = INVENTORY_PATH.read_text(encoding="utf8")
    expected_paths = [
        REPO_ROOT / "services" / "core-api" / "tests" / "features",
        REPO_ROOT / "apps" / "web" / "tests" / "acceptance",
        REPO_ROOT / "apps" / "web" / "tests" / "bdd" / "steps",
    ]

    for path_root in expected_paths:
        for test_path in sorted(path_root.glob("*")):
            if test_path.suffix not in {".feature", ".ts"}:
                continue
            assert str(test_path.relative_to(REPO_ROOT)) in inventory


def test_acceptance_inventory_names_next_migration_candidate() -> None:
    inventory = INVENTORY_PATH.read_text(encoding="utf8")

    assert "Next Recommended Migration Candidate" in inventory
    assert "Varroa detector adapter seam" in inventory


def _feature_level_tags(feature_path: Path) -> set[str]:
    pending_tags: list[str] = []
    for raw_line in feature_path.read_text(encoding="utf8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("@"):
            pending_tags.extend(line.split())
            continue
        if line.startswith("Feature:"):
            return set(pending_tags)
        return set()
    return set()
