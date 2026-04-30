from blocks.shared.base_spec import BlockSpec, ItemCountProfile

# Sequential Process family
# Blocks: processAccordion, processArrow, processSteps, sequentialOutput, sequentialSteps, branching_path, input_process_output, image_process
# Merges applied: processArrow absorbed transformation_strip (B052)
# Renames applied: imageProcess (L026, BlockType enum) → image_process

SEQUENTIAL_PROCESS_BLOCKS: dict[str, BlockSpec] = {

    "processAccordion": BlockSpec(
        family="sequential_process",
        variant="processAccordion",
        display_name="Process Accordion",
        density_range=("standard", "super_dense"),
        item_relationship_fit=("sequential",),
        content_structure_fit=("steps",),
        requires_icons=True,
        is_primary_candidate=True,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(3, 5),
                layout_variant="processAccordion_default",
                height_class="full",
                width_class="normal",
                supported_layouts=("left", "right"),
                combinable=False,
                notes="No blank layout; accordion expands vertically so side-image context is always present."
            ),
        ),
    ),

    "processArrow": BlockSpec(
        # Absorbed: transformation_strip (B052). processArrow now handles single before→after strips via `transformation` sub-variant.
        family="sequential_process",
        variant="processArrow",
        display_name="Process Arrow",
        density_range=("balanced", "super_dense"),
        item_relationship_fit=("sequential",),
        content_structure_fit=("steps", "funnel"),
        requires_icons=True,
        is_primary_candidate=True,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(2, 5),
                layout_variant="horizontal_axis",
                height_class="full",
                width_class="wide",
                supported_layouts=("blank", "top", "bottom"),
                combinable=True,
                notes="Wide block; horizontal arrow flow fills full width, no side images."
            ),
        ),
    ),

    "processSteps": BlockSpec(
        family="sequential_process",
        variant="processSteps",
        display_name="Process Steps",
        density_range=("sparse", "dense"),
        item_relationship_fit=("sequential",),
        content_structure_fit=("steps",),
        requires_icons=False,
        is_primary_candidate=True,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(3, 5),
                layout_variant="processSteps_default",
                height_class="full",
                width_class="normal",
                supported_layouts=("blank", "left", "right"),
                combinable=False,
                notes="Allows side images up to 5 items."
            ),
        ),
    ),

    "sequentialOutput": BlockSpec(
        family="sequential_process",
        variant="sequentialOutput",
        display_name="Sequential Output",
        density_range=("balanced", "dense"),
        item_relationship_fit=("sequential",),
        content_structure_fit=("steps",),
        requires_icons=True,
        is_primary_candidate=True,
        item_count_profiles=(
            # Low profile: normal width, 2–4 items
            ItemCountProfile(
                item_range=(2, 4),
                layout_variant="vertical_short",
                height_class="full",
                width_class="normal",
                supported_layouts=("left", "right"),
                combinable=True,
                notes="Normal-width low-count profile; supports side images and combinable pairing."
            ),
            # High profile: wide, 4–6 items
            ItemCountProfile(
                item_range=(5, 6),
                layout_variant="vertical_long",
                height_class="full",
                width_class="wide",
                supported_layouts=("blank", "top", "bottom"),
                combinable=True,
                notes="Wide high-count profile; expands to full width, side images dropped, supports combinable pairing."
            ),
        ),
    ),

    "sequentialSteps": BlockSpec(
        # PROMOTED: width wide, layouts blank/top/bottom (from Decision Notes, not original audit row)
        family="sequential_process",
        variant="sequentialSteps",
        display_name="Sequential Steps",
        density_range=("balanced", "dense"),
        item_relationship_fit=("sequential",),
        content_structure_fit=("steps",),
        requires_icons=False,
        is_primary_candidate=True,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(2, 4),
                layout_variant="sequentialSteps_default",
                height_class="full",
                width_class="normal",
                supported_layouts=("blank", "left", "right"),
                combinable=False,
                notes="Promoted wide block; no side images, single profile spans full item range."
            ),
        ),
    ),

    "branching_path": BlockSpec(
        family="sequential_process",
        variant="branching_path",
        display_name="Branching Path",
        density_range=("balanced", "standard"),
        item_relationship_fit=("sequential", "hierarchical"),
        content_structure_fit=("steps",),
        requires_icons=False,
        is_primary_candidate=True,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(2, 4),
                layout_variant="branching_path_default",
                height_class="full",
                width_class="wide",
                supported_layouts=("blank", "top", "bottom"),
                combinable=False,
                notes="Wide block; audit listed left/right but wide blocks never support side images — corrected to blank/top/bottom only."
            ),
        ),
    ),

    "image_process": BlockSpec(
        # RENAMED from imageProcess (L026, BlockType enum). Arrow-connected process steps with per-item images.
        family="sequential_process",
        variant="image_process",
        display_name="Image Process",
        density_range=("dense", "super_dense"),
        item_relationship_fit=("sequential",),
        content_structure_fit=("steps",),
        requires_icons=False,
        is_primary_candidate=True,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(3, 5),
                layout_variant="image_process_default",
                height_class="full",
                width_class="wide",
                supported_layouts=("blank",),
                combinable=False,
                notes="Wide block with per-item images; blank layout only, no side images."
            ),
        ),
    ),

    "input_process_output": BlockSpec(
        family="sequential_process",
        variant="input_process_output",
        display_name="Input → Process → Output",
        density_range=("balanced", "dense"),
        item_relationship_fit=("sequential",),
        content_structure_fit=("steps",),
        requires_icons=True,
        is_primary_candidate=True,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(3, 3),
                layout_variant="input_process_output_default",
                height_class="full",
                width_class="normal",
                supported_layouts=("blank", "top", "bottom"),
                combinable=True,
                notes="Fixed 3-item block representing exactly input, process, and output stages."
            ),
        ),
    ),

}