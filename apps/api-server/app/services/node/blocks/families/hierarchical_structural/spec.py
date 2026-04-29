from blocks.shared.base_spec import BlockSpec, ItemCountProfile

# Hierarchical & Structural family
# Blocks: hierarchy_tree, layer_stack
# Merges applied:
#   - classification_tree (B065) -> hierarchy_tree (rendered as 'taxonomy' style variant)
#   - nested_boxes (B066) -> layer_stack (rendered as style='concentric')

HIERARCHICAL_STRUCTURAL_BLOCKS: dict[str, BlockSpec] = {

    # MERGED: classification_tree (B065) absorbed. GyMLHierarchyTree extended with
    # taxonomy-specific rendering as a 'taxonomy' style variant.
    # Source row: L036 (HIERARCHY_TREE) — Decision: Improve.
    "hierarchy_tree": BlockSpec(
        family="hierarchical_structural",
        variant="hierarchy_tree",
        display_name="Hierarchy Tree",
        density_range=("balanced", "super_dense"),
        item_relationship_fit=("hierarchical",),
        content_structure_fit=("tree",),
        requires_icons=True,
        is_primary_candidate=True,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(2, 4),
                layout_variant="hierarchy_tree_default",
                height_class="full",
                width_class="wide",
                supported_layouts=("blank", "top", "bottom"),
                combinable=False,
                notes=(
                    "Wide tree layout for parent-child hierarchies and taxonomies; "
                    "combinable forced False by Rule 2 (wide width). No split needed "
                    "(item_range max=4 and wide width)."
                ),
            ),
        ),
    ),

    # MERGED: nested_boxes (B066) absorbed as style='concentric'.
    # layer_stack style field: 'stacked' (default) | 'concentric' (nested rectangles).
    # Source row: B064 (layer_stack) — Decision: Approved.
    "layer_stack": BlockSpec(
        family="hierarchical_structural",
        variant="layer_stack",
        display_name="Layer Stack",
        density_range=("balanced", "dense"),
        item_relationship_fit=("layered",),
        content_structure_fit=("layers",),
        requires_icons=False,
        is_primary_candidate=True,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(3, 4),
                layout_variant="vertical_short",
                height_class="full",
                width_class="normal",
                supported_layouts=("blank", "left", "right"),
                combinable=True,
                notes=(
                    "Low profile (3–4 layers): supports side images and is "
                    "combinable (spreadsheet TRUE, max <= 4, normal width)."
                ),
            ),
            ItemCountProfile(
                item_range=(5, 6),
                layout_variant="vertical_long",
                height_class="full",
                width_class="normal",
                supported_layouts=("blank",),
                combinable=False,
                notes=(
                    "High profile (5–6 layers): side images dropped per Rule 1; "
                    "combinable forced False because item_range max > 4."
                ),
            ),
        ),
    ),
}