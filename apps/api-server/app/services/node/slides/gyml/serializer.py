"""
GyML Serializer

Serialize ComposedSlide IR into GyML document structure.
Converts format-agnostic IR to spec-compliant GyML nodes.
"""

from typing import List, Optional

from .definitions import (
    # IR types
    ComposedSlide,
    ComposedSection,
    ComposedBlock,
    # GyML types
    GyMLSection,
    GyMLBody,
    GyMLHeading,
    GyMLParagraph,
    GyMLColumns,
    GyMLColumnDiv,
    GyMLSmartLayout,
    GyMLSmartLayoutItem,
    GyMLImage,
    GyMLIcon,
    GyMLDivider,
    GyMLTable,
    GyMLCode,
    GyMLNode,
)
from .constants import (
    BlockType,
    ImageLayout,
    SmartLayoutVariant,
    Relationship,
)


class GyMLSerializer:
    """
    Serialize ComposedSlide IR into GyML document structure.

    Input: ComposedSlide (format-agnostic)
    Output: GyMLSection (spec-compliant)

    This class only knows about mapping IR → GyML.
    It does NOT make semantic decisions.
    """

    def serialize(self, slide: ComposedSlide) -> GyMLSection:
        """
        Convert composed slide to GyML structure.

        Args:
            slide: ComposedSlide from the composer

        Returns:
            GyMLSection ready for validation and rendering
        """
        # Determine image layout (base preference)
        image_layout = self._parse_image_layout(slide.image_layout)

        # Base accent image (from metadata)
        accent_image = None
        if slide.accent_image_url:
            accent_image = GyMLImage(
                src=slide.accent_image_url,
                alt=slide.accent_image_alt or "",
                is_accent=True,
            )

        # Build body nodes and check for override relationships
        body_children: List[GyMLNode] = []

        for section in slide.sections:
            rel = section.relationship

            # CASE: PARALLEL -> Columns
            if rel == Relationship.PARALLEL.value:
                # Left Column: Secondary Blocks (Text)
                col1_nodes = []
                for b in section.secondary_blocks:
                    n = self._serialize_block(b)
                    if n:
                        col1_nodes.append(n)

                # Right Column: Primary Block (Visual)
                col2_nodes = []
                if section.primary_block:
                    n = self._serialize_block(section.primary_block)
                    if n:
                        col2_nodes.append(n)

                # Create Columns Node (40/60 split implicit for Text/Visual)
                if col1_nodes or col2_nodes:
                    columns_node = GyMLColumns(
                        colwidths=[40, 60],
                        columns=[
                            GyMLColumnDiv(children=col1_nodes),
                            GyMLColumnDiv(children=col2_nodes),
                        ],
                    )
                    body_children.append(columns_node)

            # CASE: ANCHORED -> Accent Image
            elif rel == Relationship.ANCHORED.value and section.primary_block:
                # Override accent image
                img_node = self._serialize_block(section.primary_block)
                if isinstance(img_node, GyMLImage):
                    img_node.is_accent = True
                    accent_image = img_node
                    # Ensure layout is not blank if we have an image
                    if image_layout == "blank":
                        image_layout = "right"

                # Add secondary blocks to body
                for b in section.secondary_blocks:
                    n = self._serialize_block(b)
                    if n:
                        body_children.append(n)

            # CASE: FLOW (Default)
            else:
                if section.primary_block:
                    n = self._serialize_block(section.primary_block)
                    if n:
                        body_children.append(n)

                for b in section.secondary_blocks:
                    n = self._serialize_block(b)
                    if n:
                        body_children.append(n)

        return GyMLSection(
            id=slide.id,
            image_layout=image_layout,
            accent_image=accent_image,
            body=GyMLBody(children=body_children),
            hierarchy=slide.hierarchy,
        )

    def serialize_many(self, slides: List[ComposedSlide]) -> List[GyMLSection]:
        """Serialize multiple slides."""
        return [self.serialize(slide) for slide in slides]

    def _parse_image_layout(self, layout: str) -> str:
        """Parse image layout string to valid GyML value."""
        valid_layouts = ["right", "left", "top", "behind", "blank"]
        layout_lower = layout.lower() if layout else "blank"

        if layout_lower in valid_layouts:
            return layout_lower

        # Try to match ImageLayout enum
        try:
            return ImageLayout(layout_lower).value
        except ValueError:
            return "blank"

    def _serialize_block(self, block: ComposedBlock) -> Optional[GyMLNode]:
        """
        Map composer block types to GyML nodes.

        This is a pure mapping - no semantic decisions.
        """
        block_type = block.type
        content = block.content

        # Heading → h1-h4
        if block_type == BlockType.HEADING.value:
            level = content.get("level", 2)
            text = content.get("text", "")
            return GyMLHeading(level=level, text=text)

        # Paragraph → p
        elif block_type == BlockType.PARAGRAPH.value:
            text = content.get("text", "")
            return GyMLParagraph(text=text)

        # Divider
        elif block_type == BlockType.DIVIDER.value:
            return GyMLDivider()

        # Image → img
        elif block_type == BlockType.IMAGE.value:
            return GyMLImage(
                src=content.get("url", content.get("src", "")),
                alt=content.get("alt", content.get("caption", "")),
                is_accent=False,
            )

        # Bullet list → smart-layout with bigBullets variant
        elif block_type == BlockType.BULLET_LIST.value:
            items = content.get("items", [])
            return self._serialize_as_smart_layout(
                items,
                SmartLayoutVariant.BIG_BULLETS.value,
            )

        # Step list → smart-layout with processSteps variant
        elif block_type == BlockType.STEP_LIST.value:
            steps = content.get("steps", content.get("items", []))
            return self._serialize_as_smart_layout(
                steps,
                SmartLayoutVariant.PROCESS_STEPS.value,
            )

        # Timeline → smart-layout with timeline variant
        elif block_type == BlockType.TIMELINE.value:
            events = content.get("events", content.get("items", []))
            items = []
            for event in events:
                items.append(
                    GyMLSmartLayoutItem(
                        year=event.get("year", event.get("title", "")),
                        description=event.get("description", event.get("text", "")),
                    )
                )
            return GyMLSmartLayout(
                variant=SmartLayoutVariant.TIMELINE.value,
                items=items,
            )

        # Card grid → smart-layout with cardGrid variant
        elif block_type == BlockType.CARD_GRID.value:
            cards = content.get("cards", [])
            items = []
            for card in cards:
                icon_alt = card.get("icon", "")
                items.append(
                    GyMLSmartLayoutItem(
                        icon=GyMLIcon(alt=icon_alt) if icon_alt else None,
                        heading=card.get("heading", card.get("title", "")),
                        description=card.get("text", card.get("description", "")),
                    )
                )
            return GyMLSmartLayout(
                variant=SmartLayoutVariant.CARD_GRID.value,
                items=items,
            )

        # Stats grid → smart-layout with stats variant
        elif block_type == BlockType.STATS.value:
            stats = content.get("stats", [])
            items = []
            for stat in stats:
                items.append(
                    GyMLSmartLayoutItem(
                        value=stat.get("value", ""),
                        label=stat.get("label", ""),
                    )
                )
            return GyMLSmartLayout(
                variant=SmartLayoutVariant.STATS.value,
                items=items,
            )

        # Smart layout (generic)
        elif block_type == BlockType.SMART_LAYOUT.value:
            items_data = content.get("items", [])
            variant = content.get("variant", SmartLayoutVariant.BIG_BULLETS.value)
            items = []
            for item in items_data:
                if isinstance(item, dict):
                    icon_alt = item.get("icon", "")
                    items.append(
                        GyMLSmartLayoutItem(
                            icon=GyMLIcon(alt=icon_alt) if icon_alt else None,
                            heading=item.get("heading", ""),
                            description=item.get("text", item.get("description", "")),
                            year=item.get("year", ""),
                            value=item.get("value", ""),
                            label=item.get("label", ""),
                        )
                    )
                else:
                    items.append(GyMLSmartLayoutItem(description=str(item)))
            return GyMLSmartLayout(variant=variant, items=items)

        # Columns → columns
        elif block_type == BlockType.COLUMNS.value:
            return self._serialize_columns(content)

        # Takeaway/Callout → p with emphasis (simplified)
        elif block_type in [BlockType.TAKEAWAY.value, BlockType.CALLOUT.value]:
            text = content.get("text", "")
            label = content.get("label", "")
            full_text = f"{label}: {text}" if label else text
            return GyMLParagraph(text=full_text)

        # Code block
        elif block_type == BlockType.CODE.value:
            code = content.get("code", "")
            language = content.get("language", "text")
            variant = content.get("variant", "snippet")
            return GyMLCode(code=code, language=language, variant=variant)

        # Table block
        elif block_type == BlockType.TABLE.value:
            headers = content.get("headers", [])
            rows = content.get("rows", [])
            variant = content.get("variant", "simple")
            return GyMLTable(headers=headers, rows=rows, variant=variant)

        # Quote block -> SmartLayout
        elif block_type == BlockType.QUOTE.value:
            text = content.get("text", "")
            author = content.get("author", "")
            source = content.get("source", "")
            variant = content.get("variant", SmartLayoutVariant.QUOTE.value)

            # Combine author and source for heading
            heading = author
            if source:
                heading = f"{author} ({source})" if author else source

            return GyMLSmartLayout(
                variant=variant,
                items=[GyMLSmartLayoutItem(heading=heading, description=text)],
            )

        # Definition block -> SmartLayout
        elif block_type == BlockType.DEFINITION.value:
            term = content.get("term", "")
            definition = content.get("definition", "")
            variant = content.get("variant", SmartLayoutVariant.DEFINITION.value)

            return GyMLSmartLayout(
                variant=variant,
                items=[GyMLSmartLayoutItem(heading=term, description=definition)],
            )

        # Comparison block -> SmartLayout
        elif block_type == BlockType.COMPARISON.value:
            left = content.get("left", {})
            right = content.get("right", {})
            variant = content.get("variant", SmartLayoutVariant.COMPARISON.value)

            items = []
            # Left item
            items.append(
                GyMLSmartLayoutItem(
                    heading=left.get("label", "Option A"),
                    description=(
                        "\n".join(left.get("points", []))
                        if isinstance(left.get("points"), list)
                        else left.get("text", "")
                    ),
                )
            )
            # Right item
            items.append(
                GyMLSmartLayoutItem(
                    heading=right.get("label", "Option B"),
                    description=(
                        "\n".join(right.get("points", []))
                        if isinstance(right.get("points"), list)
                        else right.get("text", "")
                    ),
                )
            )

            return GyMLSmartLayout(variant=variant, items=items)

        # Diagram block -> SmartLayout
        elif block_type == BlockType.DIAGRAM.value:
            nodes = content.get("nodes", content.get("items", []))
            connections = content.get("connections", [])
            variant = content.get("variant", SmartLayoutVariant.DIAGRAM_FLOWCHART.value)

            items = []
            for node in nodes:
                if isinstance(node, dict):
                    items.append(
                        GyMLSmartLayoutItem(
                            heading=node.get("label", node.get("title", "")),
                            description=node.get("text", node.get("description", "")),
                        )
                    )
                else:
                    items.append(GyMLSmartLayoutItem(description=str(node)))

            return GyMLSmartLayout(variant=variant, items=items)

        # Unknown block type - try to extract text
        else:
            text = content.get("text", str(content))
            if text:
                return GyMLParagraph(text=text)

        return None

    def _serialize_as_smart_layout(self, items: List, variant: str) -> GyMLSmartLayout:
        """Convert list items to smart-layout."""
        gyml_items = []

        for item in items:
            if isinstance(item, dict):
                icon_alt = item.get("icon", "")
                gyml_items.append(
                    GyMLSmartLayoutItem(
                        icon=GyMLIcon(alt=icon_alt) if icon_alt else None,
                        heading=item.get("heading", ""),
                        description=item.get(
                            "text", item.get("description", str(item))
                        ),
                    )
                )
            else:
                gyml_items.append(GyMLSmartLayoutItem(description=str(item)))

        return GyMLSmartLayout(variant=variant, items=gyml_items)

    def _serialize_columns(self, content: dict) -> GyMLColumns:
        """
        Serialize columns layout.

        From gyanova_markup_language.md §7:
        - colwidths is a hard constraint
        - Children must be div
        """
        colwidths = content.get("widths", content.get("colwidths", [50, 50]))
        columns_data = content.get("columns", [])

        columns = []
        for col_data in columns_data:
            col_children = []

            # col_data can be {"blocks": [...]} (from optimizer) or [block1, block2] (raw)
            blocks_list = (
                col_data.get("blocks", col_data)
                if isinstance(col_data, dict)
                else col_data
            )

            for block in blocks_list:
                # If block is already ComposedBlock (from optimizer), use it directly
                if isinstance(block, ComposedBlock):
                    node = self._serialize_block(block)
                # If block is raw dict (from LLM), wrap it
                else:
                    composed = ComposedBlock(
                        type=block.get("type", BlockType.PARAGRAPH.value),
                        content=block.get("content", block),
                    )
                    node = self._serialize_block(composed)

                if node:
                    col_children.append(node)

            columns.append(GyMLColumnDiv(children=col_children))

        return GyMLColumns(colwidths=colwidths, columns=columns)
