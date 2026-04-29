from blocks.shared.base_spec import BlockSpec, ItemCountProfile

TIMELINE_BLOCKS: dict[str, BlockSpec] = {

    "timeline": BlockSpec(
        family="timeline",
        variant="timeline",
        display_name="Timeline",
        density_range=("sparse", "dense"),
        item_relationship_fit=("sequential",),
        content_structure_fit=("timeline",),
        requires_icons=False,
        is_primary_candidate=True,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(4, 4),
                layout_variant="vertical_short",
                height_class="full",
                width_class="normal",
                supported_layouts=("blank", "left", "right"),
                combinable=False,
                notes="4 items — side image fits alongside vertical axis"
            ),
            ItemCountProfile(
                item_range=(5, 6),
                layout_variant="vertical_long",
                height_class="full",
                width_class="normal",
                supported_layouts=("blank",),
                combinable=False,
                notes="5–6 items — axis needs full width, side image cut"
            ),
        ),
    ),

    "timelineHorizontal": BlockSpec(
        family="timeline",
        variant="timelineHorizontal",
        display_name="Timeline Horizontal",
        density_range=("sparse", "standard"),
        item_relationship_fit=("sequential",),
        content_structure_fit=("timeline",),
        requires_icons=False,
        is_primary_candidate=True,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(3, 5),
                layout_variant="horizontal_axis",
                height_class="full",
                width_class="wide",
                supported_layouts=("blank", "top", "bottom"),
                combinable=False,
                notes="Horizontal axis always needs full width — no side image"
            ),
        ),
    ),

    "timelineIcon": BlockSpec(
        family="timeline",
        variant="timelineIcon",
        display_name="Timeline Icon",
        density_range=("sparse", "dense"),
        item_relationship_fit=("sequential",),
        content_structure_fit=("timeline",),
        requires_icons=True,
        is_primary_candidate=True,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(4, 4),
                layout_variant="vertical_icon_short",
                height_class="full",
                width_class="normal",
                supported_layouts=("blank", "left", "right"),
                combinable=False,
                notes="4 items with icon badges — side image still fits"
            ),
            ItemCountProfile(
                item_range=(5, 6),
                layout_variant="vertical_icon_long",
                height_class="full",
                width_class="normal",
                supported_layouts=("blank",),
                combinable=False,
                notes="5–6 items — icon badges + axis need full width"
            ),
        ),
    ),

    "timelineMilestone": BlockSpec(
        family="timeline",
        variant="timelineMilestone",
        display_name="Timeline Milestone",
        density_range=("sparse", "standard"),
        item_relationship_fit=("sequential",),
        content_structure_fit=("timeline",),
        requires_icons=True,
        is_primary_candidate=True,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(2, 4),
                layout_variant="milestone_normal",
                height_class="full",
                width_class="normal",
                supported_layouts=("blank", "top", "bottom"),
                combinable=True,
                notes="Few milestones — compact enough to allow secondary block"
            ),
            ItemCountProfile(
                item_range=(5, 6),
                layout_variant="milestone_extended",
                height_class="full",
                width_class="normal",
                supported_layouts=("blank",),
                combinable=False,
                notes="5–6 milestones — needs full height, no secondary block"
            ),
        ),
    ),
}