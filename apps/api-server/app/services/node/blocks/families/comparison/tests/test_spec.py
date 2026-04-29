from blocks.families.comparison.spec import COMPARISON_ANALYTICAL_BLOCKS
from blocks.shared.base_spec import satisfies_density


def test_all_blocks_present():
    expected = [
        "comparison_table",
        "split_panel",
        "comparisonBeforeAfter",
        "comparisonProsCons",
        "ranking_ladder",
        "spectrum_scale",
        "venn_overlap",
    ]
    assert set(COMPARISON_ANALYTICAL_BLOCKS.keys()) == set(expected)


def test_absorbed_blocks_not_present():
    # comparison (B023) and wide (B048) were absorbed into comparisonProsCons
    assert "comparison" not in COMPARISON_ANALYTICAL_BLOCKS
    assert "wide" not in COMPARISON_ANALYTICAL_BLOCKS
    assert "comparisonCards" not in COMPARISON_ANALYTICAL_BLOCKS


def test_split_blocks_drop_side_images_at_high_count():
    for variant_name in ("comparisonBeforeAfter", "ranking_ladder"):
        block = COMPARISON_ANALYTICAL_BLOCKS[variant_name]
        high_profile = next(
            p for p in block.item_count_profiles if p.item_range[0] >= 5
        )
        assert "left" not in high_profile.supported_layouts, \
            f"{variant_name} high profile still has 'left'"
        assert "right" not in high_profile.supported_layouts, \
            f"{variant_name} high profile still has 'right'"


def test_split_blocks_allow_side_images_at_low_count():
    for variant_name in ("comparisonBeforeAfter", "ranking_ladder"):
        block = COMPARISON_ANALYTICAL_BLOCKS[variant_name]
        low_profile = next(
            p for p in block.item_count_profiles if p.item_range[1] <= 4
        )
        assert "left" in low_profile.supported_layouts, \
            f"{variant_name} low profile missing 'left'"
        assert "right" in low_profile.supported_layouts, \
            f"{variant_name} low profile missing 'right'"


def test_density_gates():
    block = COMPARISON_ANALYTICAL_BLOCKS["comparisonProsCons"]
    assert satisfies_density(block, "balanced") is True
    assert satisfies_density(block, "super_dense") is False

    block = COMPARISON_ANALYTICAL_BLOCKS["comparison_table"]
    assert satisfies_density(block, "balanced") is True
    assert satisfies_density(block, "super_dense") is True
    assert satisfies_density(block, "sparse") is False


def test_wide_blocks_never_have_side_images():
    for variant, block in COMPARISON_ANALYTICAL_BLOCKS.items():
        for profile in block.item_count_profiles:
            if profile.width_class == "wide":
                assert "left" not in profile.supported_layouts, \
                    f"{variant} is wide but has 'left' in supported_layouts"
                assert "right" not in profile.supported_layouts, \
                    f"{variant} is wide but has 'right' in supported_layouts"


def test_combinable_only_on_normal_width_low_count():
    for variant, block in COMPARISON_ANALYTICAL_BLOCKS.items():
        for profile in block.item_count_profiles:
            if profile.combinable:
                assert profile.width_class == "normal", \
                    f"{variant}: combinable=True but width_class is wide"


def test_fixed_item_count_blocks():
    # comparisonProsCons is always exactly 2
    pros_cons = COMPARISON_ANALYTICAL_BLOCKS["comparisonProsCons"]
    for profile in pros_cons.item_count_profiles:
        assert profile.item_range == (2, 2)

    # split_panel is always exactly 2
    split = COMPARISON_ANALYTICAL_BLOCKS["split_panel"]
    for profile in split.item_count_profiles:
        assert profile.item_range == (2, 2)

    # venn_overlap is always exactly 3
    venn = COMPARISON_ANALYTICAL_BLOCKS["venn_overlap"]
    for profile in venn.item_count_profiles:
        assert profile.item_range == (3, 3)


def test_venn_overlap_blank_only():
    block = COMPARISON_ANALYTICAL_BLOCKS["venn_overlap"]
    for profile in block.item_count_profiles:
        assert profile.supported_layouts == ("blank",)


def test_spectrum_scale_is_wide_and_not_combinable():
    block = COMPARISON_ANALYTICAL_BLOCKS["spectrum_scale"]
    for profile in block.item_count_profiles:
        assert profile.width_class == "wide"
        assert profile.combinable is False


def test_comparison_before_after_has_two_profiles():
    block = COMPARISON_ANALYTICAL_BLOCKS["comparisonBeforeAfter"]
    assert len(block.item_count_profiles) == 2


def test_ranking_ladder_has_two_profiles():
    block = COMPARISON_ANALYTICAL_BLOCKS["ranking_ladder"]
    assert len(block.item_count_profiles) == 2