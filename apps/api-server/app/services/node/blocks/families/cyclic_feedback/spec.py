from blocks.shared.base_spec import BlockSpec, ItemCountProfile

# Cyclic & Feedback family
# Blocks: cyclic_process_block
# Merges applied: cyclic_process_block absorbed cyclicBlock smart_layout variant (B039)

CYCLIC_FEEDBACK_BLOCKS: dict[str, BlockSpec] = {

    "cyclic_process_block": BlockSpec(
        # BlockType enum L027 (GyMLCyclicProcessBlock, standalone). Snake-cased from CYCLIC_PROCESS_BLOCK.
        # Absorbed: cyclicBlock smart_layout variant (B039). Survivor: cyclic_process_block (has full CSS).
        family="cyclic_feedback",
        variant="cyclic_process_block",
        display_name="Cyclic Process",
        density_range=("balanced", "dense"),
        item_relationship_fit=("cyclical",),
        content_structure_fit=("network",),
        requires_icons=False,
        is_primary_candidate=True,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(3, 4),
                layout_variant="cyclic_process_block_default",
                height_class="full",
                width_class="wide",
                supported_layouts=("blank",),
                combinable=False,
                notes="Wide standalone cyclic block with per-item images; blank-only layout, not combinable per Rule 2."
            ),
        ),
    ),

}