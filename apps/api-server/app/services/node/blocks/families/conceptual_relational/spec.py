from blocks.shared.base_spec import BlockSpec, ItemCountProfile

# Conceptual & Relational family
# Blocks: feature_showcase, diamondHub, hubAndSpoke, relationshipMap,
#         cause_effect_web, dependency_chain, ecosystem_map
# Merges applied: hubAndSpoke absorbed HUB_AND_SPOKE legacy BlockType (L024)

CONCEPTUAL_RELATIONAL_BLOCKS: dict[str, BlockSpec] = {

    "feature_showcase": BlockSpec(
        # BlockType enum L028 (GyMLFeatureShowcaseBlock, standalone). Snake-cased from FEATURE_SHOWCASE_BLOCK.
        family="conceptual_relational",
        variant="feature_showcase",
        display_name="Feature Showcase",
        density_range=("dense", "super_dense"),
        item_relationship_fit=("radial",),
        content_structure_fit=("network",),
        requires_icons=True,
        is_primary_candidate=True,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(4, 6),
                layout_variant="orbital",
                height_class="full",
                width_class="wide",
                supported_layouts=("blank",),
                combinable=False,
                notes="Wide radial block with central hub image; blank-only layout, not combinable per Rule 2."
            ),
        ),
    ),

    "diamondHub": BlockSpec(
        family="conceptual_relational",
        variant="diamondHub",
        display_name="Diamond Hub",
        density_range=("balanced", "dense"),
        item_relationship_fit=("radial",),
        content_structure_fit=("network",),
        requires_icons=True,
        is_primary_candidate=True,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(4, 4),
                layout_variant="diamondHub_default",
                height_class="full",
                width_class="wide",
                supported_layouts=("blank",),
                combinable=False,
                notes="Fixed 4-item wide hub; blank-only layout, combinable overridden to False per Rule 2 (wide block)."
            ),
        ),
    ),

    "hubAndSpoke": BlockSpec(
        # Absorbed: HUB_AND_SPOKE legacy BlockType (L024). Survivor: hubAndSpoke (full CSS in renderer.py).
        family="conceptual_relational",
        variant="hubAndSpoke",
        display_name="Hub & Spoke",
        density_range=("dense", "super_dense"),
        item_relationship_fit=("radial",),
        content_structure_fit=("network",),
        requires_icons=True,
        is_primary_candidate=True,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(3, 6),
                layout_variant="orbital",
                height_class="full",
                width_class="wide",
                supported_layouts=("blank",),
                combinable=False,
                notes="Wide SVG orbital hub; switches to balanced columns at 5+ items. Blank-only, not combinable per Rule 2."
            ),
        ),
    ),

    "relationshipMap": BlockSpec(
        family="conceptual_relational",
        variant="relationshipMap",
        display_name="Relationship Map",
        density_range=("dense", "super_dense"),
        item_relationship_fit=("causal",),
        content_structure_fit=("network",),
        requires_icons=True,
        is_primary_candidate=True,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(3, 3),
                layout_variant="relationshipMap_default",
                height_class="full",
                width_class="wide",
                supported_layouts=("blank", "top", "bottom"),
                combinable=False,
                notes="Fixed 3-node wide block with connector arrows between cards; combinable overridden to False per Rule 2."
            ),
        ),
    ),

    "cause_effect_web": BlockSpec(
        family="conceptual_relational",
        variant="cause_effect_web",
        display_name="Cause Effect Web",
        density_range=("balanced", "standard"),
        item_relationship_fit=("causal",),
        content_structure_fit=("network",),
        requires_icons=True,
        is_primary_candidate=True,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(2, 4),
                layout_variant="two_column",
                height_class="full",
                width_class="wide",
                supported_layouts=("blank", "top", "bottom"),
                combinable=False,
                notes="Wide two-column block with directed arrows from causes (left) to effects (right); not combinable per Rule 2."
            ),
        ),
    ),

    "dependency_chain": BlockSpec(
        family="conceptual_relational",
        variant="dependency_chain",
        display_name="Dependency Chain",
        density_range=("standard", "super_dense"),
        item_relationship_fit=("hierarchical",),
        content_structure_fit=("network",),
        requires_icons=True,
        is_primary_candidate=True,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(4, 7),
                layout_variant="dependency_chain_default",
                height_class="full",
                width_class="wide",
                supported_layouts=("blank",),
                combinable=False,
                notes="Wide DAG block; nodes reference each other by label via depends_on[]. Blank-only, not combinable per Rule 2."
            ),
        ),
    ),

    "ecosystem_map": BlockSpec(
        family="conceptual_relational",
        variant="ecosystem_map",
        display_name="Ecosystem Map",
        density_range=("standard", "super_dense"),
        item_relationship_fit=("radial",),
        content_structure_fit=("network",),
        requires_icons=True,
        is_primary_candidate=True,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(4, 7),
                layout_variant="orbital",
                height_class="full",
                width_class="wide",
                supported_layouts=("blank",),
                combinable=False,
                notes="Wide orbital block with central entity; all connections are implicitly center-to-node via connection_label. Not combinable per Rule 2."
            ),
        ),
    ),

}