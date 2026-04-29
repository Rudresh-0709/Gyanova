from blocks.families.supporting_contextual.spec import (
    SUPPORTING_CONTEXTUAL_BLOCKS,
)
from blocks.shared.base_spec import satisfies_density


def test_all_blocks_present():
    expected = [
        "intro_paragraph",
        "quote",
        "annotation_paragraph",
        "callout",
        "caption",
        "divider",
        "image",
        "outro_paragraph",
        "rich_text",
        "definition",
        "myth_vs_fact",
        "summary_strip",
    ]
    assert set(SUPPORTING_CONTEXTUAL_BLOCKS.keys()) == set(expected)


def test_no_rule_1_splits_in_family():
    # Every block in this family has item_range max <= 3, so Rule 1 never triggers.
    for variant, block in SUPPORTING_CONTEXTUAL_BLOCKS.items():
        assert len(block.item_count_profiles) == 1, (
            f"{variant}: expected single profile (no Rule 1 split applies)"
        )
        for profile in block.item_count_profiles:
            assert profile.item_range[1] <= 3, (
                f"{variant}: item_range max > 3 — Rule 1 split would be required"
            )


def test_density_gates():
    # quote (PROMOTE): ultra_sparse → sparse
    q = SUPPORTING_CONTEXTUAL_BLOCKS["quote"]
    assert satisfies_density(q, "ultra_sparse") is True
    assert satisfies_density(q, "sparse") is True
    assert satisfies_density(q, "balanced") is False
    assert satisfies_density(q, "super_dense") is False

    # definition (PROMOTE): sparse → balanced
    d = SUPPORTING_CONTEXTUAL_BLOCKS["definition"]
    assert satisfies_density(d, "sparse") is True
    assert satisfies_density(d, "balanced") is True
    assert satisfies_density(d, "ultra_sparse") is False
    assert satisfies_density(d, "standard") is False

    # divider: full range ultra_sparse → super_dense
    div = SUPPORTING_CONTEXTUAL_BLOCKS["divider"]
    assert satisfies_density(div, "ultra_sparse") is True
    assert satisfies_density(div, "super_dense") is True
    assert satisfies_density(div, "balanced") is True


def test_wide_blocks_never_have_side_images():
    # No wide blocks expected in this family — guard regardless.
    for variant, block in SUPPORTING_CONTEXTUAL_BLOCKS.items():
        for profile in block.item_count_profiles:
            if profile.width_class == "wide":
                assert "left" not in profile.supported_layouts, (
                    f"{variant} is wide but has 'left' in supported_layouts"
                )
                assert "right" not in profile.supported_layouts, (
                    f"{variant} is wide but has 'right' in supported_layouts"
                )


def test_no_wide_blocks_in_family():
    for variant, block in SUPPORTING_CONTEXTUAL_BLOCKS.items():
        for profile in block.item_count_profiles:
            assert profile.width_class == "normal", (
                f"{variant}: family is expected to be normal-width only"
            )


def test_combinable_only_on_normal_width_low_count():
    for variant, block in SUPPORTING_CONTEXTUAL_BLOCKS.items():
        for profile in block.item_count_profiles:
            if profile.combinable:
                assert profile.width_class == "normal", (
                    f"{variant}: combinable=True but width_class is wide"
                )
                assert profile.item_range[1] <= 4, (
                    f"{variant}: combinable=True but item_range max > 4"
                )


def test_all_blocks_combinable():
    # Every block in this family is normal-width with max <= 3, so Rule 2
    # permits combinable=True, and the spreadsheet sets Combinable=TRUE for all.
    for variant, block in SUPPORTING_CONTEXTUAL_BLOCKS.items():
        for profile in block.item_count_profiles:
            assert profile.combinable is True, (
                f"{variant}: expected combinable=True per Rule 2 + spreadsheet"
            )


def test_promote_quote_uses_decision_notes_values():
    # PROMOTE: Decision Notes override row values.
    #   density=ultra_sparse..sparse, layouts=blank/left/right,
    #   item_range=1, is_primary_candidate=True.
    block = SUPPORTING_CONTEXTUAL_BLOCKS["quote"]
    assert block.density_range == ("ultra_sparse", "sparse")
    assert block.is_primary_candidate is True
    assert len(block.item_count_profiles) == 1
    profile = block.item_count_profiles[0]
    assert profile.item_range == (1, 1)
    assert profile.supported_layouts == ("blank", "left", "right")
    assert profile.width_class == "normal"


def test_promote_definition_uses_decision_notes_values():
    # PROMOTE: Decision Notes override row values.
    #   density=sparse..balanced, layouts=blank/left/right,
    #   item_range=1-3, is_primary_candidate=True.
    block = SUPPORTING_CONTEXTUAL_BLOCKS["definition"]
    assert block.density_range == ("sparse", "balanced")
    assert block.is_primary_candidate is True
    assert len(block.item_count_profiles) == 1
    profile = block.item_count_profiles[0]
    assert profile.item_range == (1, 3)
    assert profile.supported_layouts == ("blank", "left", "right")
    assert profile.width_class == "normal"


def test_only_promoted_blocks_are_primary_candidates():
    # Per spreadsheet: only quote and definition are primary candidates.
    expected_primary = {"quote", "definition"}
    actual_primary = {
        variant
        for variant, block in SUPPORTING_CONTEXTUAL_BLOCKS.items()
        if block.is_primary_candidate
    }
    assert actual_primary == expected_primary


def test_caption_requires_icons():
    # Caption is the only block in this family with requires_icons=True
    # (per spreadsheet "Requires Icons?" column).
    assert SUPPORTING_CONTEXTUAL_BLOCKS["caption"].requires_icons is True
    for variant, block in SUPPORTING_CONTEXTUAL_BLOCKS.items():
        if variant != "caption":
            assert block.requires_icons is False, (
                f"{variant}: only 'caption' should require icons in this family"
            )


def test_single_relationship_and_structure_default():
    # Most blocks are framing/single — assert the two new-addition exceptions
    # have their own fits and everything else defaults to ('single',)/('single',).
    single_default = {
        "intro_paragraph",
        "quote",
        "annotation_paragraph",
        "callout",
        "caption",
        "divider",
        "image",
        "outro_paragraph",
        "rich_text",
        "definition",
    }
    for variant in single_default:
        block = SUPPORTING_CONTEXTUAL_BLOCKS[variant]
        assert block.item_relationship_fit == ("single",), variant
        assert block.content_structure_fit == ("single",), variant

    myth = SUPPORTING_CONTEXTUAL_BLOCKS["myth_vs_fact"]
    assert myth.item_relationship_fit == ("opposing",)
    assert myth.content_structure_fit == ("two_sided",)

    strip = SUPPORTING_CONTEXTUAL_BLOCKS["summary_strip"]
    assert strip.item_relationship_fit == ("parallel",)
    assert strip.content_structure_fit == ("list",)


def test_compact_height_class_for_text_blocks():
    # Text/paragraph blocks and inline elements are compact; only myth_vs_fact
    # uses 'full' height because it renders a two-column comparison.
    compact_variants = {
        "intro_paragraph",
        "quote",
        "annotation_paragraph",
        "callout",
        "caption",
        "divider",
        "image",
        "outro_paragraph",
        "rich_text",
        "definition",
        "summary_strip",
    }
    for variant in compact_variants:
        for profile in SUPPORTING_CONTEXTUAL_BLOCKS[variant].item_count_profiles:
            assert profile.height_class == "compact", (
                f"{variant}: expected height_class='compact'"
            )

    for profile in SUPPORTING_CONTEXTUAL_BLOCKS["myth_vs_fact"].item_count_profiles:
        assert profile.height_class == "full"


def test_all_profiles_have_required_fields():
    for variant, block in SUPPORTING_CONTEXTUAL_BLOCKS.items():
        for profile in block.item_count_profiles:
            assert profile.item_range[0] <= profile.item_range[1], variant
            assert profile.layout_variant, variant
            assert profile.height_class in ("full", "compact", "flexible"), variant
            assert profile.width_class in ("normal", "wide"), variant
            assert len(profile.supported_layouts) >= 1, variant
            assert isinstance(profile.combinable, bool), variant
            assert profile.notes, variant


def test_all_blockspec_fields_present():
    for variant, block in SUPPORTING_CONTEXTUAL_BLOCKS.items():
        assert block.family == "supporting_contextual", variant
        assert block.variant == variant, variant
        assert block.display_name, variant
        assert len(block.density_range) == 2, variant
        assert block.item_relationship_fit, variant
        assert block.content_structure_fit, variant
        assert isinstance(block.requires_icons, bool), variant
        assert isinstance(block.is_primary_candidate, bool), variant
        assert len(block.item_count_profiles) >= 1, variant