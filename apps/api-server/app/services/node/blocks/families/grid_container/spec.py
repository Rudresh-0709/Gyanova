from blocks.shared.base_spec import BlockSpec, ItemCountProfile

# Grid & Container family
# Blocks: bigBullets, bulletIcon, cardGridDiamond, cardGridImage, cardGridSimple,
#         diamondGrid, diamondRibbon, ribbonFold, bento_grid, pillar_cards
# Merges applied: none within this family.
# Moved out: bulletCheck (B011) → supporting_contextual (absorbed bulletCross B012
#            via polarity field; tracked there, not here).
# Family-wide: item_relationship_fit=("parallel",), content_structure_fit=("list",)

GRID_CONTAINER_BLOCKS: dict[str, BlockSpec] = {

    # B010 — bigBullets. Decision Notes: FIX is_primary_candidate→True; Remove icons.
    "bigBullets": BlockSpec(
        family="grid_container",
        variant="bigBullets",
        display_name="Big Bullets",
        density_range=("ultra_sparse", "standard"),
        item_relationship_fit=("parallel",),
        content_structure_fit=("list",),
        requires_icons=False,
        is_primary_candidate=True,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(2, 4),
                layout_variant="vertical_short",
                height_class="full",
                width_class="normal",
                supported_layouts=("blank", "top", "bottom", "left", "right"),
                combinable=True,
                notes="Low profile (2–4): keeps side images; combinable per Rule 2.",
            ),
            ItemCountProfile(
                item_range=(5, 6),
                layout_variant="vertical_long",
                height_class="full",
                width_class="normal",
                supported_layouts=("blank",),
                combinable=False,
                notes="High profile (5–6): side images dropped per Rule 1; combinable forced False (max>4).",
            ),
        ),
    ),

    # B013 — bulletIcon. Decision Notes: FIX is_primary_candidate→True.
    "bulletIcon": BlockSpec(
        family="grid_container",
        variant="bulletIcon",
        display_name="Bullet Icon",
        density_range=("sparse", "standard"),
        item_relationship_fit=("parallel",),
        content_structure_fit=("list",),
        requires_icons=True,
        is_primary_candidate=True,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(2, 4),
                layout_variant="vertical_icon_short",
                height_class="full",
                width_class="normal",
                supported_layouts=("blank", "top", "bottom", "left", "right"),
                combinable=True,
                notes="Low profile (2–4) with icons; combinable per Rule 2.",
            ),
            ItemCountProfile(
                item_range=(5, 6),
                layout_variant="vertical_icon_long",
                height_class="full",
                width_class="normal",
                supported_layouts=("blank",),
                combinable=False,
                notes="High profile (5–6): side images dropped per Rule 1; combinable forced False (max>4).",
            ),
        ),
    ),

    # B015 — cardGridDiamond. Keep.
    "cardGridDiamond": BlockSpec(
        family="grid_container",
        variant="cardGridDiamond",
        display_name="Card Grid Diamond",
        density_range=("sparse", "standard"),
        item_relationship_fit=("parallel",),
        content_structure_fit=("list",),
        requires_icons=True,
        is_primary_candidate=True,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(3, 4),
                layout_variant="grid_2x2",
                height_class="full",
                width_class="normal",
                supported_layouts=("blank", "top", "bottom", "left", "right"),
                combinable=True,
                notes="Low profile (3–4) diamond cards; combinable per Rule 2.",
            ),
            ItemCountProfile(
                item_range=(5, 6),
                layout_variant="grid_3x2",
                height_class="full",
                width_class="normal",
                supported_layouts=("blank",),
                combinable=False,
                notes="High profile (5–6): side images dropped per Rule 1; combinable forced False.",
            ),
        ),
    ),

    # B017 — cardGridImage. Wide; Decision Notes: FIX is_primary_candidate→True.
    "cardGridImage": BlockSpec(
        family="grid_container",
        variant="cardGridImage",
        display_name="Card Grid Image",
        density_range=("ultra_sparse", "balanced"),
        item_relationship_fit=("parallel",),
        content_structure_fit=("list",),
        requires_icons=False,
        is_primary_candidate=True,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(2, 4),
                layout_variant="cardGridImage_default",
                height_class="full",
                width_class="wide",
                supported_layouts=("blank",),
                combinable=False,
                notes=(
                    "Wide image-card grid; single profile (no Rule 1 split — wide). "
                    "Combinable forced False by Rule 2 (wide width)."
                ),
            ),
        ),
    ),

    # B018 — cardGridSimple. Decision Notes: FIX is_primary_candidate→True.
    "cardGridSimple": BlockSpec(
        family="grid_container",
        variant="cardGridSimple",
        display_name="Card Grid Simple",
        density_range=("ultra_sparse", "balanced"),
        item_relationship_fit=("parallel",),
        content_structure_fit=("list",),
        requires_icons=False,
        is_primary_candidate=True,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(2, 4),
                layout_variant="grid_2x2",
                height_class="full",
                width_class="normal",
                supported_layouts=("blank", "top", "bottom", "left", "right"),
                combinable=True,
                notes="Low profile (2–4) minimal cards; combinable per Rule 2.",
            ),
            ItemCountProfile(
                item_range=(5, 6),
                layout_variant="grid_3x2",
                height_class="full",
                width_class="normal",
                supported_layouts=("blank",),
                combinable=False,
                notes="High profile (5–6): side images dropped per Rule 1; combinable forced False.",
            ),
        ),
    ),

    # B027 — diamondGrid. Keep.
    "diamondGrid": BlockSpec(
        family="grid_container",
        variant="diamondGrid",
        display_name="Diamond Grid",
        density_range=("ultra_sparse", "standard"),
        item_relationship_fit=("parallel",),
        content_structure_fit=("list",),
        requires_icons=True,
        is_primary_candidate=True,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(1, 4),
                layout_variant="grid_2x2",
                height_class="full",
                width_class="normal",
                supported_layouts=("blank", "top", "bottom", "left", "right"),
                combinable=True,
                notes="Low profile (1–4) diamond cells; combinable per Rule 2.",
            ),
            ItemCountProfile(
                item_range=(5, 6),
                layout_variant="grid_3x2",
                height_class="full",
                width_class="normal",
                supported_layouts=("blank",),
                combinable=False,
                notes="High profile (5–6): side images dropped per Rule 1; combinable forced False.",
            ),
        ),
    ),

    # B029 — diamondRibbon. Keep. (Spreadsheet density 'balance' read as 'balanced'.)
    "diamondRibbon": BlockSpec(
        family="grid_container",
        variant="diamondRibbon",
        display_name="Diamond Ribbon",
        density_range=("balanced", "super_dense"),
        item_relationship_fit=("parallel",),
        content_structure_fit=("list",),
        requires_icons=True,
        is_primary_candidate=True,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(1, 4),
                layout_variant="grid_2x2",
                height_class="full",
                width_class="normal",
                supported_layouts=("blank", "top", "bottom", "left", "right"),
                combinable=True,
                notes="Low profile (1–4) ribbon-diamond cards; combinable per Rule 2.",
            ),
            ItemCountProfile(
                item_range=(5, 6),
                layout_variant="grid_3x2",
                height_class="full",
                width_class="normal",
                supported_layouts=("blank",),
                combinable=False,
                notes="High profile (5–6): side images dropped per Rule 1; combinable forced False.",
            ),
        ),
    ),

    # B031 — ribbonFold. Keep.
    "ribbonFold": BlockSpec(
        family="grid_container",
        variant="ribbonFold",
        display_name="Ribbon Fold",
        density_range=("balanced", "dense"),
        item_relationship_fit=("parallel",),
        content_structure_fit=("list",),
        requires_icons=True,
        is_primary_candidate=True,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(3, 4),
                layout_variant="vertical_icon_short",
                height_class="full",
                width_class="normal",
                supported_layouts=("blank", "top", "bottom", "left", "right"),
                combinable=True,
                notes="Low profile (3–4) ribbon-fold cards; combinable per Rule 2.",
            ),
            ItemCountProfile(
                item_range=(5, 5),
                layout_variant="vertical_icon_long",
                height_class="full",
                width_class="normal",
                supported_layouts=("blank",),
                combinable=False,
                notes="High profile (5): side images dropped per Rule 1; combinable forced False (max>4).",
            ),
        ),
    ),

    # B068 — bento_grid. New addition. Approved as-is.
        # B068 — bento_grid. New addition. Approved as-is.
    "bento_grid": BlockSpec(
        family="grid_container",
        variant="bento_grid",
        display_name="Bento Grid",
        density_range=("balanced", "standard"),
        item_relationship_fit=("parallel",),
        content_structure_fit=("list",),
        requires_icons=True,
        is_primary_candidate=True,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(3, 4),
                layout_variant="bento_grid_default",
                height_class="full",
                width_class="normal",
                supported_layouts=("blank", "top", "bottom", "left", "right"),
                combinable=True,
                notes=(
                    "Low profile (3–4): asymmetric featured cell + smaller cells; "
                    "combinable per Rule 2."
                ),
            ),
            ItemCountProfile(
                item_range=(5, 5),
                layout_variant="bento_grid_long",
                height_class="full",
                width_class="normal",
                supported_layouts=("blank",),
                combinable=False,
                notes="High profile (5): side images dropped per Rule 1; combinable forced False (max>4).",
            ),
        ),
    ),

    # B069 — pillar_cards. New addition. Approved as-is.
    # Primary Candidate column = No (kept; no Decision-Notes correction).
    "pillar_cards": BlockSpec(
        family="grid_container",
        variant="pillar_cards",
        display_name="Pillar Cards",
        density_range=("sparse", "standard"),
        item_relationship_fit=("parallel",),
        content_structure_fit=("list",),
        requires_icons=True,
        is_primary_candidate=False,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(3, 4),
                layout_variant="pillar_cards_default",
                height_class="full",
                width_class="normal",
                supported_layouts=("blank", "top", "bottom", "left", "right"),
                combinable=True,
                notes=(
                    "Low profile (3–4): tall narrow cards with top icon; "
                    "combinable per Rule 2."
                ),
            ),
            ItemCountProfile(
                item_range=(5, 5),
                layout_variant="pillar_cards_long",
                height_class="full",
                width_class="normal",
                supported_layouts=("blank",),
                combinable=False,
                notes="High profile (5): side images dropped per Rule 1; combinable forced False (max>4).",
            ),
        ),
    ),

    # bulletCheck (B011) — MOVED to supporting_contextual family (spreadsheet
    #   New Family = 'Supporting & Contextual'). Absorbed bulletCross (B012)
    #   via polarity field. Tracked in supporting_contextual/spec.py, not here.

    # BorderedCards (B014) — DELETED. Reason: redundant with cardGridSimple.
    # cardGrid (B044) — DELETED. Reason: superseded by cardGridSimple / cardGridDiamond.
    # knowledgeWeb (B042) — DELETED. Reason: belongs in conceptual_relational; rendering deprecated.
    # striped — DELETED. Reason: stylistic variant, not a distinct block.
    # highlight — DELETED. Reason: stylistic variant, not a distinct block.
}