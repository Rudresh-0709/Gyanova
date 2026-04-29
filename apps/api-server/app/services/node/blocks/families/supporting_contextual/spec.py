from blocks.shared.base_spec import BlockSpec, ItemCountProfile

# Supporting & Contextual family
# Blocks: intro_paragraph, quote, annotation_paragraph, callout, caption, divider,
#         image, outro_paragraph, rich_text, definition, myth_vs_fact, summary_strip
# Merges applied:
#   - QUOTE legacy BlockType (L016) + quoteCitation -> quote (PROMOTE)
#   - CONTEXT_PARAGRAPH (L019) -> annotation_paragraph
#   - callout_box (B073) -> callout (adds type: tip|warning|info|danger)
#   - TAKEAWAY (L014) -> outro_paragraph
#   - PARAGRAPH (L009) -> rich_text
#   - DEFINITION legacy BlockType (L015) -> definition (PROMOTE)
# No splits (every block has item_range max <= 3, so Rule 1 never triggers).
# No wide blocks in this family.

SUPPORTING_CONTEXTUAL_BLOCKS: dict[str, BlockSpec] = {

    # L018 — INTRO_PARAGRAPH. Decision: Keep. Rendered as GyMLParagraph variant=intro.
    "intro_paragraph": BlockSpec(
        family="supporting_contextual",
        variant="intro_paragraph",
        display_name="Intro Paragraph",
        density_range=("ultra_sparse", "standard"),
        item_relationship_fit=("single",),
        content_structure_fit=("single",),
        requires_icons=False,
        is_primary_candidate=False,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(1, 1),
                layout_variant="intro_paragraph_default",
                height_class="compact",
                width_class="normal",
                supported_layouts=("blank", "top", "bottom", "left", "right"),
                combinable=True,
                notes=(
                    "Single intro paragraph used to open a topic. Combinable per "
                    "Rule 2 (max=1, normal width)."
                ),
            ),
        ),
    ),

    # B035 — quote. PROMOTE. Decision Notes are authoritative:
    #   density=ultra_sparse..sparse, layouts=blank/left/right, item_range=1,
    #   is_primary_candidate=True for framing slides.
    # MERGED: QUOTE legacy BlockType (L016) routes here.
    # MERGED: quoteCitation absorbed — schema gains optional citation field.
    "quote": BlockSpec(
        family="supporting_contextual",
        variant="quote",
        display_name="Quote",
        density_range=("ultra_sparse", "sparse"),
        item_relationship_fit=("single",),
        content_structure_fit=("single",),
        requires_icons=False,
        is_primary_candidate=True,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(1, 1),
                layout_variant="quote_default",
                height_class="compact",
                width_class="normal",
                supported_layouts=("blank", "left", "right"),
                combinable=True,
                notes=(
                    "PROMOTE: density/layouts/primary from Decision Notes, not row. "
                    "Schema: heading=author, description=quote text, optional "
                    "citation (from absorbed quoteCitation)."
                ),
            ),
        ),
    ),

    # L020 — ANNOTATION_PARAGRAPH. Decision: Keep.
    # MERGED: CONTEXT_PARAGRAPH (L019) absorbed — both render as GyMLParagraph;
    # context variant merges into annotation.
    "annotation_paragraph": BlockSpec(
        family="supporting_contextual",
        variant="annotation_paragraph",
        display_name="Annotation Paragraph",
        density_range=("ultra_sparse", "standard"),
        item_relationship_fit=("single",),
        content_structure_fit=("single",),
        requires_icons=False,
        is_primary_candidate=False,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(1, 1),
                layout_variant="annotation_paragraph_default",
                height_class="compact",
                width_class="normal",
                supported_layouts=("blank", "top", "bottom", "left", "right"),
                combinable=True,
                notes=(
                    "Annotation/context paragraph reinforcing the main teaching. "
                    "Combinable per Rule 2 (max=1, normal width)."
                ),
            ),
        ),
    ),

    # L011 — CALLOUT. Decision: Merge with callout_box.
    # MERGED: callout_box (B073) absorbed. Schema gains optional `type` field:
    # tip | warning | info | danger (default: info).
    "callout": BlockSpec(
        family="supporting_contextual",
        variant="callout",
        display_name="Callout",
        density_range=("ultra_sparse", "standard"),
        item_relationship_fit=("single",),
        content_structure_fit=("single",),
        requires_icons=False,
        is_primary_candidate=False,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(1, 1),
                layout_variant="callout_default",
                height_class="compact",
                width_class="normal",
                supported_layouts=("blank", "top", "bottom", "left", "right"),
                combinable=True,
                notes=(
                    "Callout annotation with type variants tip/warning/info/danger "
                    "(absorbed from callout_box). Combinable per Rule 2."
                ),
            ),
        ),
    ),

    # L022 — CAPTION. Decision: Keep. Requires icons per spreadsheet column.
    "caption": BlockSpec(
        family="supporting_contextual",
        variant="caption",
        display_name="Caption",
        density_range=("ultra_sparse", "standard"),
        item_relationship_fit=("single",),
        content_structure_fit=("single",),
        requires_icons=True,
        is_primary_candidate=False,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(1, 1),
                layout_variant="caption_default",
                height_class="compact",
                width_class="normal",
                supported_layouts=("blank", "top", "bottom", "left", "right"),
                combinable=True,
                notes=(
                    "Image/figure caption with icon. Combinable per Rule 2 "
                    "(max=1, normal width)."
                ),
            ),
        ),
    ),

    # L017 — DIVIDER. Decision: Keep. Density spans full scale (works everywhere).
    "divider": BlockSpec(
        family="supporting_contextual",
        variant="divider",
        display_name="Divider",
        density_range=("ultra_sparse", "super_dense"),
        item_relationship_fit=("single",),
        content_structure_fit=("single",),
        requires_icons=False,
        is_primary_candidate=False,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(1, 1),
                layout_variant="divider_default",
                height_class="compact",
                width_class="normal",
                supported_layouts=("blank", "top", "bottom", "left", "right"),
                combinable=True,
                notes=(
                    "Visual separator usable at any density. Combinable per Rule 2."
                ),
            ),
        ),
    ),

    # L012 — IMAGE. Decision: Keep.
    "image": BlockSpec(
        family="supporting_contextual",
        variant="image",
        display_name="Image",
        density_range=("ultra_sparse", "standard"),
        item_relationship_fit=("single",),
        content_structure_fit=("single",),
        requires_icons=False,
        is_primary_candidate=False,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(1, 1),
                layout_variant="image_default",
                height_class="compact",
                width_class="normal",
                supported_layouts=("blank", "top", "bottom", "left", "right"),
                combinable=True,
                notes=(
                    "Single visual media supplementing the main teaching. "
                    "Combinable per Rule 2."
                ),
            ),
        ),
    ),

    # L021 — OUTRO_PARAGRAPH. Decision: Keep.
    # MERGED: TAKEAWAY (L014) absorbed — both are closing/reinforcing paragraphs.
    "outro_paragraph": BlockSpec(
        family="supporting_contextual",
        variant="outro_paragraph",
        display_name="Outro Paragraph",
        density_range=("ultra_sparse", "standard"),
        item_relationship_fit=("single",),
        content_structure_fit=("single",),
        requires_icons=False,
        is_primary_candidate=False,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(1, 1),
                layout_variant="outro_paragraph_default",
                height_class="compact",
                width_class="normal",
                supported_layouts=("blank", "top", "bottom", "left", "right"),
                combinable=True,
                notes=(
                    "Closing paragraph that summarizes/reinforces the lesson "
                    "(absorbed TAKEAWAY). Combinable per Rule 2."
                ),
            ),
        ),
    ),

    # L033 — RICH_TEXT. Decision: Keep. Survivor of the paragraph merges.
    # MERGED: PARAGRAPH (L009) absorbed. RICH_TEXT is the survivor.
    "rich_text": BlockSpec(
        family="supporting_contextual",
        variant="rich_text",
        display_name="Rich Text",
        density_range=("ultra_sparse", "standard"),
        item_relationship_fit=("single",),
        content_structure_fit=("single",),
        requires_icons=False,
        is_primary_candidate=False,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(1, 1),
                layout_variant="rich_text_default",
                height_class="compact",
                width_class="normal",
                supported_layouts=("blank", "top", "bottom", "left", "right"),
                combinable=True,
                notes=(
                    "Formatted rich text adding depth/context. Survivor of the "
                    "PARAGRAPH merge. Combinable per Rule 2."
                ),
            ),
        ),
    ),

    # B032 — definition. PROMOTE. Decision Notes authoritative:
    #   density=sparse..balanced, layouts=blank/left/right, item_range=1-3,
    #   is_primary_candidate=True (can be primary when teaching vocabulary).
    # MERGED: DEFINITION legacy BlockType (L015) routes here.
    "definition": BlockSpec(
        family="supporting_contextual",
        variant="definition",
        display_name="Definition",
        density_range=("sparse", "balanced"),
        item_relationship_fit=("single",),
        content_structure_fit=("single",),
        requires_icons=False,
        is_primary_candidate=True,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(1, 3),
                layout_variant="definition_default",
                height_class="compact",
                width_class="normal",
                supported_layouts=("blank", "left", "right"),
                combinable=True,
                notes=(
                    "PROMOTE: density/layouts/range/primary from Decision Notes. "
                    "Up to 3 term/definition pairs. Combinable per Rule 2 "
                    "(max=3 <= 4, normal width). No Rule 1 split (max <= 4)."
                ),
            ),
        ),
    ),

    # B072 — myth_vs_fact. New addition. Approved as-is.
    # Opposing polarity styling (red myth + green fact) — distinct from comparison blocks.
    "myth_vs_fact": BlockSpec(
        family="supporting_contextual",
        variant="myth_vs_fact",
        display_name="Myth vs Fact",
        density_range=("ultra_sparse", "standard"),
        item_relationship_fit=("opposing",),
        content_structure_fit=("two_sided",),
        requires_icons=False,
        is_primary_candidate=False,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(1, 1),
                layout_variant="myth_vs_fact_default",
                height_class="full",
                width_class="normal",
                supported_layouts=("blank", "top", "bottom", "left", "right"),
                combinable=True,
                notes=(
                    "Two-column myth/fact pair with opposing polarity styling "
                    "(red cross / green check). Combinable per Rule 2."
                ),
            ),
        ),
    ),

    # B074 — summary_strip. New addition. Approved as-is.
    # Compact horizontal numbered strip — minimal vertical footprint differentiates
    # from bigBullets (vertical, titled).
    "summary_strip": BlockSpec(
        family="supporting_contextual",
        variant="summary_strip",
        display_name="Summary Strip",
        density_range=("ultra_sparse", "standard"),
        item_relationship_fit=("parallel",),
        content_structure_fit=("list",),
        requires_icons=False,
        is_primary_candidate=False,
        item_count_profiles=(
            ItemCountProfile(
                item_range=(1, 1),
                layout_variant="summary_strip_default",
                height_class="compact",
                width_class="normal",
                supported_layouts=("blank", "top", "bottom", "left", "right"),
                combinable=True,
                notes=(
                    "Compact horizontal strip of numbered key-takeaway points. "
                    "Block-level item_range is 1 (the strip itself); points[] "
                    "are nested inside. Combinable per Rule 2."
                ),
            ),
        ),
    ),

    # bulletCheck (B011) — NOT included here pending family resolution.
    # The spreadsheet has 'Supporting & Contextual' in one family column and
    # 'Grid & Container' in the cross-reference column. Confirm intended home.
    # If it lands here, it absorbs bulletCross (B012) via the polarity field.
}