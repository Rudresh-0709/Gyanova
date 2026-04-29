from blocks.shared.base_spec import BlockSpec, ItemCountProfile

# Stats & Quantitative family
# Blocks: formula_block, interlockingArrows, stats, statsComparison, statsPercentage
# Merges applied: stats absorbed big_number_highlight (B057), progress_bars (B058), change_delta (B060)
#                 statsComparison absorbed weighted_comparison (B054), score_card (B059)
# Renames applied: InterlockingArrows (B006) → interlockingArrows
#                  statsGauge (B008) → statsComparison (per Canonical Names column)

STATS_QUANTITATIVE_BLOCKS: dict[str, BlockSpec] = {

    "formula_block": BlockSpec(
        # BlockType enum L030 (GyMLFormulaBlock). Snake-cased from FORMULA_BLOCK.
        family="stats_quantitative",
        variant="formula_block",
        display_name="Formula Block",
        density_range=("sparse", "standard"),
        item_relationship_fit=("single",),
        content_structure_fit=("single",),
        requires_icons=False,
        is_primary_candidate=True,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(1, 1),
                layout_variant="formula_block_default",
                height_class="full",
                width_class="normal",
                supported_layouts=("blank", "top", "bottom", "left", "right"),
                combinable=True,
                notes="Fixed single-formula block; all layouts supported, combinable as a supporting element."
            ),
        ),
    ),

    "interlockingArrows": BlockSpec(
        # RENAMED from InterlockingArrows (B006). Capital 'I' breaks camelCase normalisation in _VARIANT_LOOKUP.
        family="stats_quantitative",
        variant="interlockingArrows",
        display_name="Interlocking Arrows",
        density_range=("sparse", "standard"),
        item_relationship_fit=("parallel",),
        content_structure_fit=("matrix",),
        requires_icons=False,
        is_primary_candidate=True,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(4, 4),
                layout_variant="interlockingArrows_default",
                height_class="full",
                width_class="normal",
                supported_layouts=("blank", "top", "bottom", "left", "right"),
                combinable=True,
                notes="Fixed 4-item interlocking metric display; all layouts supported, combinable at fixed low count."
            ),
        ),
    ),

    "stats": BlockSpec(
        # Absorbed: big_number_highlight (B057, optional context field added),
        #           progress_bars (B058, bar_fill sub-schema),
        #           change_delta (B060, before/after delta pairs sub-schema).
        family="stats_quantitative",
        variant="stats",
        display_name="Stats",
        density_range=("sparse", "standard"),
        item_relationship_fit=("parallel",),
        content_structure_fit=("single",),
        requires_icons=False,
        is_primary_candidate=True,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(2, 4),
                layout_variant="stats_default",
                height_class="full",
                width_class="normal",
                supported_layouts=("blank", "top", "bottom", "left", "right"),
                combinable=True,
                notes="Large value + label display; all layouts supported, combinable at max 4 normal-width items."
            ),
        ),
    ),

    "statsComparison": BlockSpec(
        # RENAMED from statsGauge (B008) per Canonical Names column → statsComparison.
        # Absorbed: weighted_comparison (B054, scoring matrix with qualitative fallback),
        #           score_card (B059, dashboard metric tiles, max 4 items).
        family="stats_quantitative",
        variant="statsComparison",
        display_name="Stats Comparison",
        density_range=("sparse", "standard"),
        item_relationship_fit=("parallel",),
        content_structure_fit=("matrix",),
        requires_icons=False,
        is_primary_candidate=True,
        item_count_profiles=(
            # Rule 1 split: normal width + left/right + max 6 > 4
            ItemCountProfile(
                item_range=(3, 4),
                layout_variant="vertical_short",
                height_class="full",
                width_class="normal",
                supported_layouts=("blank", "top", "bottom", "left", "right"),
                combinable=True,
                notes="Low-count profile (3–4 items); all layouts supported, combinable for side-by-side metric pairs."
            ),
            ItemCountProfile(
                item_range=(5, 6),
                layout_variant="vertical_long",
                height_class="full",
                width_class="normal",
                supported_layouts=("blank",),
                combinable=False,
                notes="High-count profile (5–6 items); side images dropped and not combinable to keep dense metric grid readable."
            ),
        ),
    ),

    "statsPercentage": BlockSpec(
        # PROMOTED from renderer-only (B009). Decision Notes override original row values:
        # width=wide, layouts=blank/top/bottom, item range=2–4, density=sparse/balanced/standard.
        family="stats_quantitative",
        variant="statsPercentage",
        display_name="Stats Percentage",
        density_range=("sparse", "standard"),
        item_relationship_fit=("parallel",),
        content_structure_fit=("single",),
        requires_icons=False,
        is_primary_candidate=True,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(2, 4),
                layout_variant="statsPercentage_default",
                height_class="full",
                width_class="wide",
                supported_layouts=("blank", "top", "bottom"),
                combinable=False,
                notes="Promoted wide block; percentage values displayed at full width. No side images, not combinable per Rule 2."
            ),
        ),
    ),

}