from blocks.families.conceptual_relational.spec import CONCEPTUAL_RELATIONAL_BLOCKS
from blocks.shared.base_spec import satisfies_density


def test_all_blocks_present():
    expected = [
        "feature_showcase",
        "diamondHub",
        "hubAndSpoke",
        "relationshipMap",
        "cause_effect_web",
        "dependency_chain",
        "ecosystem_map",
    ]
    assert set(CONCEPTUAL_RELATIONAL_BLOCKS.keys()) == set(expected)


def test_absorbed_blocks_not_present():
    # HUB_AND_SPOKE (L024) was absorbed into hubAndSpoke
    assert "HUB_AND_SPOKE" not in CONCEPTUAL_RELATIONAL_BLOCKS
    assert "FEATURE_SHOWCASE_BLOCK" not in CONCEPTUAL_RELATIONAL_BLOCKS


def test_all_blocks_are_wide():
    # Every block in this family is wide
    for variant, block in CONCEPTUAL_RELATIONAL_BLOCKS.items():
        for profile in block.item_count_profiles:
            assert profile.width_class == "wide", \
                f"{variant} expected wide but got {profile.width_class}"


def test_wide_blocks_never_have_side_images():
    for variant, block in CONCEPTUAL_RELATIONAL_BLOCKS.items():
        for profile in block.item_count_profiles:
            assert "left" not in profile.supported_layouts, \
                f"{variant} is wide but has 'left' in supported_layouts"
            assert "right" not in profile.supported_layouts, \
                f"{variant} is wide but has 'right' in supported_layouts"


def test_no_block_is_combinable():
    # All wide blocks — Rule 2 forces combinable=False for all
    for variant, block in CONCEPTUAL_RELATIONAL_BLOCKS.items():
        for profile in block.item_count_profiles:
            assert profile.combinable is False, \
                f"{variant}: combinable should be False for wide blocks"


def test_density_gates():
    block = CONCEPTUAL_RELATIONAL_BLOCKS["feature_showcase"]
    assert satisfies_density(block, "dense") is True
    assert satisfies_density(block, "balanced") is False

    block = CONCEPTUAL_RELATIONAL_BLOCKS["cause_effect_web"]
    assert satisfies_density(block, "balanced") is True
    assert satisfies_density(block, "super_dense") is False

    block = CONCEPTUAL_RELATIONAL_BLOCKS["dependency_chain"]
    assert satisfies_density(block, "standard") is True
    assert satisfies_density(block, "sparse") is False


def test_fixed_item_count_blocks():
    # diamondHub is always exactly 4
    block = CONCEPTUAL_RELATIONAL_BLOCKS["diamondHub"]
    for profile in block.item_count_profiles:
        assert profile.item_range == (4, 4)

    # relationshipMap is always exactly 3
    block = CONCEPTUAL_RELATIONAL_BLOCKS["relationshipMap"]
    for profile in block.item_count_profiles:
        assert profile.item_range == (3, 3)


def test_blank_only_blocks():
    for variant_name in ("feature_showcase", "hubAndSpoke", "dependency_chain", "ecosystem_map", "diamondHub"):
        block = CONCEPTUAL_RELATIONAL_BLOCKS[variant_name]
        for profile in block.item_count_profiles:
            assert profile.supported_layouts == ("blank",), \
                f"{variant_name} expected blank-only layouts"


def test_no_rule1_splits():
    # All blocks are wide — Rule 1 never applies; each block has exactly one profile
    for variant, block in CONCEPTUAL_RELATIONAL_BLOCKS.items():
        assert len(block.item_count_profiles) == 1, \
            f"{variant} should have exactly one ItemCountProfile (wide block, no split)"


def test_hub_and_spoke_orbital_layout():
    block = CONCEPTUAL_RELATIONAL_BLOCKS["hubAndSpoke"]
    for profile in block.item_count_profiles:
        assert profile.layout_variant == "orbital"


def test_ecosystem_map_orbital_layout():
    block = CONCEPTUAL_RELATIONAL_BLOCKS["ecosystem_map"]
    for profile in block.item_count_profiles:
        assert profile.layout_variant == "orbital"