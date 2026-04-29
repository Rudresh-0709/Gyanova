from blocks.families.stats_quantitative.spec import STATS_QUANTITATIVE_BLOCKS
from blocks.shared.base_spec import satisfies_density


def test_all_blocks_present():
    expected = [
        "formula_block",
        "interlockingArrows",
        "stats",
        "statsComparison",
        "statsPercentage",
    ]
    assert set(STATS_QUANTITATIVE_BLOCKS.keys()) == set(expected)


def test_absorbed_and_renamed_blocks_not_present():
    # Renamed: InterlockingArrows → interlockingArrows
    assert "InterlockingArrows" not in STATS_QUANTITATIVE_BLOCKS
    # Renamed: statsGauge → statsComparison
    assert "statsGauge" not in STATS_QUANTITATIVE_BLOCKS
    # Absorbed into stats
    assert "big_number_highlight" not in STATS_QUANTITATIVE_BLOCKS
    assert "progress_bars" not in STATS_QUANTITATIVE_BLOCKS
    assert "change_delta" not in STATS_QUANTITATIVE_BLOCKS
    # Absorbed into statsComparison
    assert "weighted_comparison" not in STATS_QUANTITATIVE_BLOCKS
    assert "score_card" not in STATS_QUANTITATIVE_BLOCKS


def test_stats_comparison_split_drops_side_images_at_high_count():
    block = STATS_QUANTITATIVE_BLOCKS["statsComparison"]
    high_profile = next(
        p for p in block.item_count_profiles if p.item_range[0] >= 5
    )
    assert "left" not in high_profile.supported_layouts
    assert "right" not in high_profile.supported_layouts


def test_stats_comparison_split_allows_side_images_at_low_count():
    block = STATS_QUANTITATIVE_BLOCKS["statsComparison"]
    low_profile = next(
        p for p in block.item_count_profiles if p.item_range[1] <= 4
    )
    assert "left" in low_profile.supported_layouts
    assert "right" in low_profile.supported_layouts


def test_stats_comparison_has_two_profiles():
    block = STATS_QUANTITATIVE_BLOCKS["statsComparison"]
    assert len(block.item_count_profiles) == 2


def test_wide_blocks_never_have_side_images():
    for variant, block in STATS_QUANTITATIVE_BLOCKS.items():
        for profile in block.item_count_profiles:
            if profile.width_class == "wide":
                assert "left" not in profile.supported_layouts, \
                    f"{variant} is wide but has 'left' in supported_layouts"
                assert "right" not in profile.supported_layouts, \
                    f"{variant} is wide but has 'right' in supported_layouts"


def test_combinable_only_on_normal_width_low_count():
    for variant, block in STATS_QUANTITATIVE_BLOCKS.items():
        for profile in block.item_count_profiles:
            if profile.combinable:
                assert profile.width_class == "normal", \
                    f"{variant}: combinable=True but width_class is wide"
                assert profile.item_range[1] <= 4, \
                    f"{variant}: combinable=True but item_range max > 4"


def test_density_gates():
    block = STATS_QUANTITATIVE_BLOCKS["stats"]
    assert satisfies_density(block, "sparse") is True
    assert satisfies_density(block, "standard") is True
    assert satisfies_density(block, "dense") is False

    block = STATS_QUANTITATIVE_BLOCKS["statsComparison"]
    assert satisfies_density(block, "sparse") is True
    assert satisfies_density(block, "dense") is False

    block = STATS_QUANTITATIVE_BLOCKS["statsPercentage"]
    assert satisfies_density(block, "balanced") is True
    assert satisfies_density(block, "super_dense") is False


def test_fixed_item_count_blocks():
    # formula_block is always exactly 1
    block = STATS_QUANTITATIVE_BLOCKS["formula_block"]
    for profile in block.item_count_profiles:
        assert profile.item_range == (1, 1)

    # interlockingArrows is always exactly 4
    block = STATS_QUANTITATIVE_BLOCKS["interlockingArrows"]
    for profile in block.item_count_profiles:
        assert profile.item_range == (4, 4)


def test_stats_percentage_is_promoted_wide():
    block = STATS_QUANTITATIVE_BLOCKS["statsPercentage"]
    for profile in block.item_count_profiles:
        assert profile.width_class == "wide"
        assert profile.item_range == (2, 4)
        assert profile.combinable is False


def test_no_rule1_split_except_stats_comparison():
    # Only statsComparison should have 2 profiles; all others have 1
    for variant, block in STATS_QUANTITATIVE_BLOCKS.items():
        if variant == "statsComparison":
            assert len(block.item_count_profiles) == 2
        else:
            assert len(block.item_count_profiles) == 1, \
                f"{variant} unexpectedly has {len(block.item_count_profiles)} profiles"