from blocks.shared.base_spec import BlockSpec, ItemCountProfile

# Comparison & Analytical family
# Blocks: comparison_table, split_panel, comparisonBeforeAfter, comparisonProsCons,
#         ranking_ladder, spectrum_scale, venn_overlap
# Merges applied: comparisonProsCons absorbed comparison (B023) + wide (B048)

COMPARISON_ANALYTICAL_BLOCKS: dict[str, BlockSpec] = {

    "comparison_table": BlockSpec(
        # BlockType enum L031 (GyMLComparisonTable). Wide — Rule 7: left/right dropped.
        family="comparison_analytical",
        variant="comparison_table",
        display_name="Comparison Table",
        density_range=("balanced", "super_dense"),
        item_relationship_fit=("opposing",),
        content_structure_fit=("matrix",),
        requires_icons=False,
        is_primary_candidate=True,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(2, 4),
                layout_variant="comparison_table_default",
                height_class="full",
                width_class="wide",
                supported_layouts=("blank", "top", "bottom"),
                combinable=False,
                notes="Wide tabular block; spreadsheet listed left/right but wide blocks never support side images — corrected to blank/top/bottom."
            ),
        ),
    ),

    "split_panel": BlockSpec(
        # BlockType enum L037 (GyMLSplitPanel). Wide — Rule 7: left/right dropped.
        family="comparison_analytical",
        variant="split_panel",
        display_name="Split Panel",
        density_range=("balanced", "standard"),
        item_relationship_fit=("opposing",),
        content_structure_fit=("two_sided",),
        requires_icons=False,
        is_primary_candidate=True,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(2, 2),
                layout_variant="split_panel_default",
                height_class="full",
                width_class="wide",
                supported_layouts=("blank", "top", "bottom"),
                combinable=False,
                notes="Fixed 2-panel wide block; side images dropped per Rule 7."
            ),
        ),
    ),

    "comparisonBeforeAfter": BlockSpec(
        family="comparison_analytical",
        variant="comparisonBeforeAfter",
        display_name="Comparison Before After",
        density_range=("balanced", "standard"),
        item_relationship_fit=("opposing",),
        content_structure_fit=("two_sided",),
        requires_icons=False,
        is_primary_candidate=True,
        item_count_profiles=(
            # Rule 1 split: normal width + left/right + max 6 > 4
            ItemCountProfile(
                item_range=(1, 4),
                layout_variant="vertical_short",
                height_class="full",
                width_class="normal",
                supported_layouts=("blank", "left", "right"),
                combinable=True,
                notes="Low-count profile (1–4 items); side images permitted and block is combinable."
            ),
            ItemCountProfile(
                item_range=(5, 6),
                layout_variant="vertical_long",
                height_class="full",
                width_class="normal",
                supported_layouts=("blank",),
                combinable=False,
                notes="High-count profile (5–6 items); side images dropped to avoid crowding the longer before/after list."
            ),
        ),
    ),

    "comparisonProsCons": BlockSpec(
        # Absorbed: comparison (B023, renderer-only with .anim-slide-comparison CSS) and
        # wide (B048, comparison alias). Port .anim-slide-comparison CSS before removing B023.
        family="comparison_analytical",
        variant="comparisonProsCons",
        display_name="Comparison Pros Cons",
        density_range=("balanced", "dense"),
        item_relationship_fit=("opposing",),
        content_structure_fit=("two_sided",),
        requires_icons=True,
        is_primary_candidate=True,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(2, 2),
                layout_variant="two_column",
                height_class="full",
                width_class="normal",
                supported_layouts=("blank", "left", "right"),
                combinable=True,
                notes="Fixed 2-item pros/cons block; always two columns, side images supported."
            ),
        ),
    ),

    "ranking_ladder": BlockSpec(
        family="comparison_analytical",
        variant="ranking_ladder",
        display_name="Ranking Ladder",
        density_range=("balanced", "dense"),
        item_relationship_fit=("ranked",),
        content_structure_fit=("list",),
        requires_icons=False,
        is_primary_candidate=True,
        item_count_profiles=(
            # Rule 1 split: normal width + left/right + max 6 > 4
            ItemCountProfile(
                item_range=(3, 4),
                layout_variant="vertical_short",
                height_class="full",
                width_class="normal",
                supported_layouts=("blank", "left", "right"),
                combinable=False,
                notes="Low-count profile (3–4 items); side images permitted alongside short ranked ladder."
            ),
            ItemCountProfile(
                item_range=(5, 6),
                layout_variant="vertical_long",
                height_class="full",
                width_class="normal",
                supported_layouts=("blank",),
                combinable=False,
                notes="High-count profile (5–6 items); side images dropped to avoid crowding the taller ranked list."
            ),
        ),
    ),

    "spectrum_scale": BlockSpec(
        family="comparison_analytical",
        variant="spectrum_scale",
        display_name="Spectrum Scale",
        density_range=("balanced", "standard"),
        item_relationship_fit=("overlapping",),
        content_structure_fit=("spectrum",),
        requires_icons=False,
        is_primary_candidate=True,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(3, 6),
                layout_variant="horizontal_axis",
                height_class="full",
                width_class="wide",
                supported_layouts=("blank", "top", "bottom"),
                combinable=False,
                notes="Wide horizontal spectrum bar; no side images, not combinable per Rule 2 (wide block)."
            ),
        ),
    ),

    "venn_overlap": BlockSpec(
        family="comparison_analytical",
        variant="venn_overlap",
        display_name="Venn Overlap",
        density_range=("balanced", "standard"),
        item_relationship_fit=("overlapping",),
        content_structure_fit=("web",),
        requires_icons=False,
        is_primary_candidate=True,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(3, 3),
                layout_variant="venn_overlap_default",
                height_class="full",
                width_class="normal",
                supported_layouts=("blank",),
                combinable=True,
                notes="Fixed 3-circle Venn diagram; blank layout only — overlapping circles need full canvas."
            ),
        ),
    ),

}