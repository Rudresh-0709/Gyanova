from blocks.families.timeline.spec import TIMELINE_BLOCKS
from blocks.shared.base_spec import satisfies_density


def test_all_blocks_present():
    expected = [
        "timeline",
        "timelineHorizontal",
        "timelineIcon",
        "timelineMilestone",
    ]
    assert set(TIMELINE_BLOCKS.keys()) == set(expected)


def test_split_blocks_drop_side_image_at_high_count():
    # timeline: normal width, left/right layouts, max > 4 → Rule 1 split
    block = TIMELINE_BLOCKS["timeline"]
    high_profile = next(
        p for p in block.item_count_profiles if p.item_range[0] >= 5
    )
    assert "left" not in high_profile.supported_layouts
    assert "right" not in high_profile.supported_layouts

    # timelineIcon: same Rule 1 split (normal + left/right + max > 4)
    block = TIMELINE_BLOCKS["timelineIcon"]
    high_profile = next(
        p for p in block.item_count_profiles if p.item_range[0] >= 5
    )
    assert "left" not in high_profile.supported_layouts
    assert "right" not in high_profile.supported_layouts


def test_timeline_has_two_profiles():
    # Rule 1 split produces exactly 2 profiles
    block = TIMELINE_BLOCKS["timeline"]
    assert len(block.item_count_profiles) == 2
    low = next(p for p in block.item_count_profiles if p.item_range[1] <= 4)
    high = next(p for p in block.item_count_profiles if p.item_range[0] >= 5)
    assert "left" in low.supported_layouts
    assert "right" in low.supported_layouts
    assert high.supported_layouts == ("blank",)


def test_timeline_icon_has_two_profiles():
    # Rule 1 split produces exactly 2 profiles for icon variant too
    block = TIMELINE_BLOCKS["timelineIcon"]
    assert len(block.item_count_profiles) == 2
    low = next(p for p in block.item_count_profiles if p.item_range[1] <= 4)
    high = next(p for p in block.item_count_profiles if p.item_range[0] >= 5)
    assert "left" in low.supported_layouts
    assert "right" in low.supported_layouts
    assert high.supported_layouts == ("blank",)


def test_timeline_icon_requires_icons():
    block = TIMELINE_BLOCKS["timelineIcon"]
    assert block.requires_icons is True


def test_timeline_milestone_requires_icons():
    block = TIMELINE_BLOCKS["timelineMilestone"]
    assert block.requires_icons is True


def test_timeline_base_no_icons():
    block = TIMELINE_BLOCKS["timeline"]
    assert block.requires_icons is False


def test_density_gates():
    # timeline: sparse → dense
    block = TIMELINE_BLOCKS["timeline"]
    assert satisfies_density(block, "sparse") is True
    assert satisfies_density(block, "dense") is True
    assert satisfies_density(block, "super_dense") is False
    assert satisfies_density(block, "ultra_sparse") is False

    # timelineHorizontal: sparse → standard
    block = TIMELINE_BLOCKS["timelineHorizontal"]
    assert satisfies_density(block, "sparse") is True
    assert satisfies_density(block, "standard") is True
    assert satisfies_density(block, "dense") is False

    # timelineMilestone: sparse → standard (PROMOTE values)
    block = TIMELINE_BLOCKS["timelineMilestone"]
    assert satisfies_density(block, "sparse") is True
    assert satisfies_density(block, "standard") is True
    assert satisfies_density(block, "dense") is False


def test_wide_blocks_never_have_side_images():
    for variant, block in TIMELINE_BLOCKS.items():
        for profile in block.item_count_profiles:
            if profile.width_class == "wide":
                assert "left" not in profile.supported_layouts, \
                    f"{variant} is wide but has 'left' in supported_layouts"
                assert "right" not in profile.supported_layouts, \
                    f"{variant} is wide but has 'right' in supported_layouts"


def test_combinable_only_on_normal_width_low_count():
    for variant, block in TIMELINE_BLOCKS.items():
        for profile in block.item_count_profiles:
            if profile.combinable:
                assert profile.width_class == "normal", \
                    f"{variant}: combinable=True but width_class is wide"


def test_timeline_horizontal_is_wide():
    block = TIMELINE_BLOCKS["timelineHorizontal"]
    assert len(block.item_count_profiles) == 1
    profile = block.item_count_profiles[0]
    assert profile.width_class == "wide"
    assert profile.item_range == (3, 5)
    assert "left" not in profile.supported_layouts
    assert "right" not in profile.supported_layouts


def test_timeline_milestone_promoted_values():
    # timelineMilestone is a PROMOTE block — verify promoted attributes
    block = TIMELINE_BLOCKS["timelineMilestone"]
    assert block.density_range == ("sparse", "standard")
    assert block.is_primary_candidate is True
    assert block.requires_icons is True


def test_timeline_milestone_has_two_profiles():
    # timelineMilestone: item_range 2–6, normal, but layouts are top/bottom
    # (not left/right), so Rule 1 does NOT apply — but it still has 2 profiles
    # for combinable split (low count combinable, high count not)
    block = TIMELINE_BLOCKS["timelineMilestone"]
    assert len(block.item_count_profiles) == 2
    low = next(p for p in block.item_count_profiles if p.item_range[1] <= 4)
    high = next(p for p in block.item_count_profiles if p.item_range[0] >= 5)
    assert low.combinable is True
    assert high.combinable is False


def test_all_blocks_have_correct_family():
    for variant, block in TIMELINE_BLOCKS.items():
        assert block.family == "timeline", \
            f"{variant} has family='{block.family}' instead of 'timeline'"


def test_all_blocks_have_sequential_relationship():
    for variant, block in TIMELINE_BLOCKS.items():
        assert block.item_relationship_fit == ("sequential",), \
            f"{variant} should have item_relationship_fit=('sequential',)"


def test_all_blocks_have_timeline_structure():
    for variant, block in TIMELINE_BLOCKS.items():
        assert block.content_structure_fit == ("timeline",), \
            f"{variant} should have content_structure_fit=('timeline',)"


def test_all_profiles_have_required_fields():
    for variant, block in TIMELINE_BLOCKS.items():
        for i, profile in enumerate(block.item_count_profiles):
            assert isinstance(profile.item_range, tuple), \
                f"{variant} profile {i}: item_range is not a tuple"
            assert len(profile.item_range) == 2, \
                f"{variant} profile {i}: item_range must be (min, max)"
            assert profile.item_range[0] <= profile.item_range[1], \
                f"{variant} profile {i}: item_range min > max"
            assert profile.layout_variant, \
                f"{variant} profile {i}: layout_variant is empty"
            assert profile.height_class in ("full", "compact", "flexible"), \
                f"{variant} profile {i}: invalid height_class '{profile.height_class}'"
            assert profile.width_class in ("normal", "wide"), \
                f"{variant} profile {i}: invalid width_class '{profile.width_class}'"
            assert len(profile.supported_layouts) > 0, \
                f"{variant} profile {i}: supported_layouts is empty"
            assert profile.notes, \
                f"{variant} profile {i}: notes is empty"