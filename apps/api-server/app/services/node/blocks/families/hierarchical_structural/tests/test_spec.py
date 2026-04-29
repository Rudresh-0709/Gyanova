from blocks.families.hierarchical_structural.spec import (
    HIERARCHICAL_STRUCTURAL_BLOCKS,
)
from blocks.shared.base_spec import satisfies_density


def test_all_blocks_present():
    expected = ["hierarchy_tree", "layer_stack"]
    assert set(HIERARCHICAL_STRUCTURAL_BLOCKS.keys()) == set(expected)


def test_split_blocks_drop_side_image_at_high_count():
    # layer_stack is the only Rule 1 split in this family.
    block = HIERARCHICAL_STRUCTURAL_BLOCKS["layer_stack"]
    high_profile = next(
        p for p in block.item_count_profiles if p.item_range[0] >= 5
    )
    assert "left" not in high_profile.supported_layouts
    assert "right" not in high_profile.supported_layouts
    assert high_profile.supported_layouts == ("blank",)


def test_split_blocks_low_profile_keeps_side_images():
    block = HIERARCHICAL_STRUCTURAL_BLOCKS["layer_stack"]
    low_profile = next(
        p for p in block.item_count_profiles if p.item_range[1] <= 4
    )
    assert "left" in low_profile.supported_layouts
    assert "right" in low_profile.supported_layouts


def test_density_gates():
    tree = HIERARCHICAL_STRUCTURAL_BLOCKS["hierarchy_tree"]
    assert satisfies_density(tree, "balanced") is True
    assert satisfies_density(tree, "super_dense") is True
    assert satisfies_density(tree, "ultra_sparse") is False
    assert satisfies_density(tree, "sparse") is False

    stack = HIERARCHICAL_STRUCTURAL_BLOCKS["layer_stack"]
    assert satisfies_density(stack, "balanced") is True
    assert satisfies_density(stack, "dense") is True
    assert satisfies_density(stack, "super_dense") is False
    assert satisfies_density(stack, "sparse") is False


def test_wide_blocks_never_have_side_images():
    for variant, block in HIERARCHICAL_STRUCTURAL_BLOCKS.items():
        for profile in block.item_count_profiles:
            if profile.width_class == "wide":
                assert "left" not in profile.supported_layouts, (
                    f"{variant} is wide but has 'left' in supported_layouts"
                )
                assert "right" not in profile.supported_layouts, (
                    f"{variant} is wide but has 'right' in supported_layouts"
                )


def test_combinable_only_on_normal_width_low_count():
    for variant, block in HIERARCHICAL_STRUCTURAL_BLOCKS.items():
        for profile in block.item_count_profiles:
            if profile.combinable:
                assert profile.width_class == "normal", (
                    f"{variant}: combinable=True but width_class is wide"
                )
                assert profile.item_range[1] <= 4, (
                    f"{variant}: combinable=True but item_range max > 4"
                )


def test_hierarchy_tree_merge_metadata():
    # Sanity: hierarchy_tree absorbed classification_tree (B065).
    # Verify it carries the expected shape (wide, hierarchical/tree).
    block = HIERARCHICAL_STRUCTURAL_BLOCKS["hierarchy_tree"]
    assert block.item_relationship_fit == ("hierarchical",)
    assert block.content_structure_fit == ("tree",)
    assert block.requires_icons is True
    assert len(block.item_count_profiles) == 1
    assert block.item_count_profiles[0].width_class == "wide"


def test_layer_stack_merge_metadata():
    # Sanity: layer_stack absorbed nested_boxes (B066) as style='concentric'.
    block = HIERARCHICAL_STRUCTURAL_BLOCKS["layer_stack"]
    assert block.item_relationship_fit == ("layered",)
    assert block.content_structure_fit == ("layers",)
    assert len(block.item_count_profiles) == 2  # Rule 1 split