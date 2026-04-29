from blocks.families.grid_container.spec import GRID_CONTAINER_BLOCKS
from blocks.shared.base_spec import satisfies_density


def test_all_blocks_present():
    expected = [
        "bigBullets",
        "bulletIcon",
        "cardGridDiamond",
        "cardGridImage",
        "cardGridSimple",
        "diamondGrid",
        "diamondRibbon",
        "ribbonFold",
        "bento_grid",
        "pillar_cards",
    ]
    assert set(GRID_CONTAINER_BLOCKS.keys()) == set(expected)


def test_bullet_check_not_in_grid_family():
    # bulletCheck moved to supporting_contextual per spreadsheet New Family column.
    assert "bulletCheck" not in GRID_CONTAINER_BLOCKS


def test_split_blocks_drop_side_image_at_high_count():
    # Every normal-width block with max>4 must split (Rule 1).
    split_variants = [
        "bigBullets",
        "bulletIcon",
        "cardGridDiamond",
        "cardGridSimple",
        "diamondGrid",
        "diamondRibbon",
        "ribbonFold",
        "bento_grid",
        "pillar_cards",
    ]
    for variant in split_variants:
        block = GRID_CONTAINER_BLOCKS[variant]
        assert len(block.item_count_profiles) == 2, (
            f"{variant} should have 2 profiles after Rule 1 split"
        )
        high_profile = next(
            p for p in block.item_count_profiles if p.item_range[0] >= 5
        )
        assert "left" not in high_profile.supported_layouts, (
            f"{variant} high profile must not include 'left'"
        )
        assert "right" not in high_profile.supported_layouts, (
            f"{variant} high profile must not include 'right'"
        )
        assert high_profile.supported_layouts == ("blank",), (
            f"{variant} high profile should be ('blank',)"
        )


def test_split_blocks_low_profile_keeps_side_images():
    split_variants = [
        "bigBullets",
        "bulletIcon",
        "cardGridDiamond",
        "cardGridSimple",
        "diamondGrid",
        "diamondRibbon",
        "ribbonFold",
        "bento_grid",
        "pillar_cards",
    ]
    for variant in split_variants:
        block = GRID_CONTAINER_BLOCKS[variant]
        low_profile = next(
            p for p in block.item_count_profiles if p.item_range[1] <= 4
        )
        assert "left" in low_profile.supported_layouts, (
            f"{variant} low profile should keep 'left'"
        )
        assert "right" in low_profile.supported_layouts, (
            f"{variant} low profile should keep 'right'"
        )


def test_density_gates():
    # bigBullets: ultra_sparse → standard
    bb = GRID_CONTAINER_BLOCKS["bigBullets"]
    assert satisfies_density(bb, "ultra_sparse") is True
    assert satisfies_density(bb, "standard") is True
    assert satisfies_density(bb, "dense") is False
    assert satisfies_density(bb, "super_dense") is False

    # diamondRibbon: balanced → super_dense
    dr = GRID_CONTAINER_BLOCKS["diamondRibbon"]
    assert satisfies_density(dr, "balanced") is True
    assert satisfies_density(dr, "super_dense") is True
    assert satisfies_density(dr, "ultra_sparse") is False
    assert satisfies_density(dr, "sparse") is False

    # ribbonFold: balanced → dense
    rf = GRID_CONTAINER_BLOCKS["ribbonFold"]
    assert satisfies_density(rf, "balanced") is True
    assert satisfies_density(rf, "dense") is True
    assert satisfies_density(rf, "super_dense") is False
    assert satisfies_density(rf, "sparse") is False


def test_wide_blocks_never_have_side_images():
    for variant, block in GRID_CONTAINER_BLOCKS.items():
        for profile in block.item_count_profiles:
            if profile.width_class == "wide":
                assert "left" not in profile.supported_layouts, (
                    f"{variant} is wide but has 'left' in supported_layouts"
                )
                assert "right" not in profile.supported_layouts, (
                    f"{variant} is wide but has 'right' in supported_layouts"
                )


def test_card_grid_image_is_wide_single_profile():
    block = GRID_CONTAINER_BLOCKS["cardGridImage"]
    assert len(block.item_count_profiles) == 1
    profile = block.item_count_profiles[0]
    assert profile.width_class == "wide"
    assert profile.supported_layouts == ("blank",)
    assert profile.combinable is False


def test_combinable_only_on_normal_width_low_count():
    for variant, block in GRID_CONTAINER_BLOCKS.items():
        for profile in block.item_count_profiles:
            if profile.combinable:
                assert profile.width_class == "normal", (
                    f"{variant}: combinable=True but width_class is wide"
                )
                assert profile.item_range[1] <= 4, (
                    f"{variant}: combinable=True but item_range max > 4"
                )


def test_family_wide_relationship_and_structure_fits():
    # All grid_container blocks should be parallel/list per the family-wide rule.
    for variant, block in GRID_CONTAINER_BLOCKS.items():
        assert block.item_relationship_fit == ("parallel",), (
            f"{variant}: expected item_relationship_fit=('parallel',)"
        )
        assert block.content_structure_fit == ("list",), (
            f"{variant}: expected content_structure_fit=('list',)"
        )


def test_primary_candidate_corrections_applied():
    # Decision Notes in the spreadsheet explicitly corrected these to True.
    corrected_to_true = [
        "bigBullets",
        "bulletIcon",
        "cardGridImage",
        "cardGridSimple",
    ]
    for variant in corrected_to_true:
        assert GRID_CONTAINER_BLOCKS[variant].is_primary_candidate is True, (
            f"{variant}: Decision Notes 'FIX is_primary_candidate→True' not applied"
        )

    # pillar_cards: spreadsheet Primary Candidate=No, no correction note.
    assert GRID_CONTAINER_BLOCKS["pillar_cards"].is_primary_candidate is False


def test_bigbullets_icons_removed():
    # Decision Notes: "Remove icons".
    assert GRID_CONTAINER_BLOCKS["bigBullets"].requires_icons is False


def test_all_profiles_have_required_fields():
    for variant, block in GRID_CONTAINER_BLOCKS.items():
        for profile in block.item_count_profiles:
            assert profile.item_range[0] <= profile.item_range[1], variant
            assert profile.layout_variant, variant
            assert profile.height_class in ("full", "compact", "flexible"), variant
            assert profile.width_class in ("normal", "wide"), variant
            assert len(profile.supported_layouts) >= 1, variant
            assert isinstance(profile.combinable, bool), variant
            assert profile.notes, variant