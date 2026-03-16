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
    GyMLComparisonTable,
    GyMLKeyValueList,
    GyMLKeyValueItem,
    GyMLRichText,
    GyMLNumberedList,
    GyMLNumberedListItem,
    GyMLLabeledDiagram,
    GyMLDiagramLabel,
    GyMLHierarchyTree,
    GyMLTreeNode,
    GyMLSplitPanel,
    GyMLPanel,
    GyMLFormulaBlock,
    GyMLFormulaVariable,
    GyMLHubAndSpoke,
    GyMLHubAndSpokeItem,
    GyMLProcessArrowBlock,
    GyMLProcessArrowItem,
    GyMLCyclicBlock,
    GyMLCyclicItem,
    GyMLCyclicProcessBlock,
    GyMLCyclicProcessItem,
    GyMLFeatureShowcaseBlock,
    GyMLFeatureShowcaseItem,
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
                print(f"DEBUG: Processing FLOW section ({section.purpose})")
                if section.primary_block:
                    n = self._serialize_block(section.primary_block)
                    print(
                        f"DEBUG: Primary block {section.primary_block.type} serialized to {type(n)}"
                    )
                    if n:
                        body_children.append(n)

                for b in section.secondary_blocks:
                    n = self._serialize_block(b)
                    print(f"DEBUG: Secondary block {b.type} serialized to {type(n)}")
                    if n:
                        body_children.append(n)

        print(f"DEBUG: Finished assembling body_children, length: {len(body_children)}")

        return GyMLSection(
            id=slide.id,
            image_layout=image_layout,
            accent_image=accent_image,
            image_style=slide.image_style,
            slide_density=slide.slide_density,
            body=GyMLBody(children=body_children),
            hierarchy=slide.hierarchy,
            image_caption=None,
        )

    def serialize_many(self, slides: List[ComposedSlide]) -> List[GyMLSection]:
        """Serialize multiple slides."""
        return [self.serialize(slide) for slide in slides]

    def _parse_image_layout(self, layout: str) -> str:
        """Parse image layout string to valid GyML value."""
        valid_layouts = [
            "right",
            "left",
            "top",
            "bottom",
            "behind",
            "blank",
            "right-wide",
        ]
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

        # Paragraphs → p (with variants)
        elif block_type == BlockType.PARAGRAPH.value:
            text = content.get("text", "")
            return GyMLParagraph(text=text)

        elif block_type == BlockType.INTRO_PARAGRAPH.value:
            text = content.get("text", "")
            return GyMLParagraph(text=text, variant="intro")

        elif block_type == BlockType.CONTEXT_PARAGRAPH.value:
            text = content.get("text", "")
            return GyMLParagraph(text=text, variant="context")

        elif block_type == BlockType.ANNOTATION_PARAGRAPH.value:
            text = content.get("text", "")
            return GyMLParagraph(text=text, variant="annotation")

        elif block_type == BlockType.OUTRO_PARAGRAPH.value:
            text = content.get("text", "")
            return GyMLParagraph(text=text, variant="outro")

        elif block_type == BlockType.CAPTION.value:
            text = content.get("text", "")
            return GyMLParagraph(text=text, variant="caption")

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
        # Smart layout (generic)
        elif block_type == BlockType.SMART_LAYOUT.value:
            items_data = content.get("items", [])
            variant = content.get("variant", SmartLayoutVariant.BIG_BULLETS.value)

            # Auto-convert large comparison grids (>3 items) into cleanly formatted tables
            if len(items_data) > 3 and variant in [
                SmartLayoutVariant.COMPARISON.value,
                "comparisonProsCons",
                "comparisonBeforeAfter",
            ]:
                variant = "comparison_table"

            # 1. Handle STRUCTURED Comparison Schema (New)
            if "criteria" in content and "subjects" in content:
                criteria = content["criteria"]
                subjects = content["subjects"]
                conclusion = content.get("conclusion")

                # Determine if we should use Table or Cards based on count
                # (The composer usually sets this, but we reinforce here)
                num_subjects = len(subjects)
                if num_subjects > 3 or variant == "comparison_table":
                    # Map to GyMLComparisonTable
                    headers = ["Dimension"] + [s["label"] for s in subjects]
                    rows = []
                    for crit in criteria:
                        row = [crit["label"]]
                        for subject in subjects:
                            # Find matching value
                            val = "-"
                            for v in subject.get("values", []):
                                if v.get("criterion_id") == crit["id"]:
                                    val = v.get("value", "-")
                                    break
                            row.append(val)
                        rows.append(row)
                    return GyMLComparisonTable(headers=headers, rows=rows, caption=conclusion)
                else:
                    # Map to GyMLSmartLayout (Cards)
                    items = []
                    for subject in subjects:
                        points = []
                        for crit in criteria:
                            val = "-"
                            for v in subject.get("values", []):
                                if v.get("criterion_id") == crit["id"]:
                                    val = v.get("value", "-")
                                    break
                            points.append(f"{crit['label']}: {val}")
                        
                        items.append(
                            GyMLSmartLayoutItem(
                                heading=subject["label"],
                                points=points
                            )
                        )
                    # Force comparisonCards variant for structured comparison schemas
                    variant = "comparisonCards"
                    return GyMLSmartLayout(variant=variant, items=items)

            # 2. Handle LEGACY Heuristic Pivoting
            # Special case: comparison_table variant inside smart_layout
            if variant == "comparison_table":
                headers = content.get("headers", [])
                rows = content.get("rows", [])
                caption = content.get(
                    "caption", content.get("title", content.get("heading", ""))
                )

                # Fallback: Convert items to table if headers/rows are missing
                if not headers and not rows and items_data:
                    # HEURISTIC: Check if items are dimension-centric (each item is a criterion)
                    # We look for "Subject: Value" pairs or "Subject ...; Subject ..." segments
                    first_item = items_data[0]
                    first_item_points = first_item.get("points", [])
                    first_item_desc = first_item.get("description", "")
                    
                    has_sub_val_pairs = False
                    if first_item_points:
                        has_sub_val_pairs = all(":" in str(p) for p in first_item_points)
                    elif first_item_desc:
                        # Check for colon OR multiple semicolon-separated segments
                        if ":" in first_item_desc:
                            has_sub_val_pairs = True
                        elif ";" in first_item_desc and len(first_item_desc.split(";")) >= 2:
                            # Higher confidence if at least 2 segments start with Capitalized word
                            segs = [s.strip() for s in first_item_desc.split(";")]
                            if all(s and s[0].isupper() for s in segs[:2]):
                                has_sub_val_pairs = True

                    if has_sub_val_pairs:
                        # DIMENSION-CENTRIC (Pivot)
                        # Identify all subjects from all items to ensure uniform columns
                        all_subjects = []
                        for item in items_data:
                            pts = item.get("points", [])
                            desc = item.get("description", "")
                            
                            raw_segments = []
                            if pts:
                                raw_segments = [str(p) for p in pts]
                            elif desc:
                                raw_segments = [s.strip() for s in desc.split(";") if s.strip()]
                                
                            for s in raw_segments:
                                if ":" in s:
                                    subject = s.split(":", 1)[0].strip()
                                else:
                                    # Fallback: Assume first 1-2 words are the subject if they look like it
                                    words = s.split()
                                    if words:
                                        # Take first word if capitalized
                                        if words[0][0].isupper():
                                            subject = words[0].strip(",.:;")
                                            if subject not in all_subjects:
                                                all_subjects.append(subject)
                                        continue

                                if subject not in all_subjects:
                                    all_subjects.append(subject)

                        headers = ["Dimension"] + all_subjects
                        for item in items_data:
                            row = [item.get("heading", item.get("title", "Criterion"))]
                            
                            # Extract pairs/segments from this item
                            item_pairs = {}
                            pts = item.get("points", [])
                            desc = item.get("description", "")
                            
                            raw_segments = []
                            if pts:
                                raw_segments = [str(p) for p in pts]
                            elif desc:
                                raw_segments = [s.strip() for s in desc.split(";") if s.strip()]
                                
                            for s in raw_segments:
                                if ":" in s:
                                    sub, val = s.split(":", 1)
                                    item_pairs[sub.strip()] = val.strip()
                                else:
                                    # Fallback split
                                    words = s.split()
                                    if words and words[0][0].isupper():
                                        sub = words[0].strip(",.:;")
                                        val = " ".join(words[1:])
                                        item_pairs[sub] = val
                            
                            # Fill row according to all_subjects
                            for sub in all_subjects:
                                row.append(item_pairs.get(sub, "-"))
                            rows.append(row)
                    else:
                        # SUBJECT-CENTRIC (Legacy/Flat)
                        # Each item is a column (Subject)
                        headers = [
                            item.get("heading", item.get("title", item.get("label", "")))
                            for item in items_data
                        ]

                        # Group points into rows
                        max_points = 0
                        all_points = []
                        for item in items_data:
                            pts = item.get("points", [])
                            if not pts:
                                desc = item.get(
                                    "text", item.get("description", item.get("content", ""))
                                )
                                if desc:
                                    pts = [desc]
                            all_points.append(pts)
                            max_points = max(max_points, len(pts))

                        for i in range(max_points):
                            row = []
                            for pts in all_points:
                                val = pts[i] if i < len(pts) else ""
                                # Format dict if needed
                                if isinstance(val, dict):
                                    label = val.get("label", "")
                                    desc = val.get("description", val.get("text", ""))
                                    val = f"**{label}**: {desc}" if label else desc
                                row.append(val)
                            rows.append(row)

                return GyMLComparisonTable(headers=headers, rows=rows, caption=caption)

            return self._serialize_as_smart_layout(items_data, variant)

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
            items_data = content.get("items", [])
            variant = content.get("variant", SmartLayoutVariant.COMPARISON.value)

            # NEW: structured schema handling
            if "criteria" in content and "subjects" in content:
                return self._serialize_block(
                    ComposedBlock(type=BlockType.SMART_LAYOUT.value, content=content)
                )

            # Auto-convert large comparison grids (>3 items) into cleanly formatted tables
            if len(items_data) > 3 and variant in [
                SmartLayoutVariant.COMPARISON.value,
                SmartLayoutVariant.COMPARISON_CARDS.value,
                "comparisonProsCons",
                "comparisonBeforeAfter",
            ]:
                content["variant"] = "comparison_table"
                return self._serialize_block(
                    ComposedBlock(type=BlockType.SMART_LAYOUT.value, content=content)
                )

            items = []
            for item in items_data:
                if isinstance(item, dict):
                    # Points support - keep as list for premium rendering
                    points = item.get("points")
                    desc = item.get(
                        "text", item.get("description", item.get("content", ""))
                    )

                    # If it's a list, we don't squash it anymore
                    if isinstance(points, list):
                        pass
                    else:
                        points = None

                    items.append(
                        GyMLSmartLayoutItem(
                            heading=item.get(
                                "title",
                                item.get("label", item.get("heading", "Option")),
                            ),
                            description=desc,
                            points=points,
                            icon=(
                                GyMLIcon(alt=item.get("icon"))
                                if item.get("icon")
                                else None
                            ),
                        )
                    )

            # Legacy support for left/right fields if items missing
            if not items:
                left = content.get("left", {})
                right = content.get("right", {})
                if left or right:
                    for side in [left, right]:
                        points = side.get("points")
                        desc = side.get(
                            "text", side.get("description", side.get("content", ""))
                        )
                        if not isinstance(points, list):
                            points = None

                        items.append(
                            GyMLSmartLayoutItem(
                                heading=side.get("title", side.get("label", "Option")),
                                description=desc,
                                points=points,
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
                            description=node.get(
                                "text", node.get("description", node.get("content", ""))
                            ),
                        )
                    )
                else:
                    items.append(GyMLSmartLayoutItem(description=str(node)))

            return GyMLSmartLayout(variant=variant, items=items)

        # Comparison Table
        elif block_type == BlockType.COMPARISON_TABLE.value:
            if "criteria" in content and "subjects" in content:
                content["variant"] = "comparison_table"
                return self._serialize_block(
                    ComposedBlock(type=BlockType.SMART_LAYOUT.value, content=content)
                )

            headers = content.get("headers", [])
            rows = content.get("rows", [])
            caption = content.get("caption", "")
            return GyMLComparisonTable(headers=headers, rows=rows, caption=caption)

        # Key-Value List
        elif block_type == BlockType.KEY_VALUE_LIST.value:
            items_data = content.get("items", [])
            items = [
                GyMLKeyValueItem(key=i.get("key", ""), value=i.get("value", ""))
                for i in items_data
                if isinstance(i, dict)
            ]
            return GyMLKeyValueList(items=items)

        # Rich Text
        elif block_type == BlockType.RICH_TEXT.value:
            paragraphs = content.get("paragraphs", [])
            return GyMLRichText(paragraphs=paragraphs)

        # Numbered List
        elif block_type == BlockType.NUMBERED_LIST.value:
            items_data = content.get("items", [])
            items = [
                GyMLNumberedListItem(
                    title=i.get("title", ""), description=i.get("description", "")
                )
                for i in items_data
                if isinstance(i, dict)
            ]
            return GyMLNumberedList(items=items)

        # Labeled Diagram
        elif block_type == BlockType.LABELED_DIAGRAM.value:
            image_url = content.get("image_url", content.get("imageUrl", ""))
            labels_data = content.get("labels", [])
            labels = [
                GyMLDiagramLabel(
                    text=l.get("text", ""),
                    x=float(l.get("x", 0)),
                    y=float(l.get("y", 0)),
                )
                for l in labels_data
                if isinstance(l, dict)
            ]
            return GyMLLabeledDiagram(image_url=image_url, labels=labels)

        # Hierarchy Tree
        elif block_type == BlockType.HIERARCHY_TREE.value:
            root_data = content.get("root", {})

            def parse_node(node_data: dict) -> "GyMLTreeNode":
                return GyMLTreeNode(
                    label=node_data.get("label", ""),
                    children=[parse_node(c) for c in node_data.get("children", [])],
                )

            return GyMLHierarchyTree(root=parse_node(root_data))

        # Split Panel
        elif block_type == BlockType.SPLIT_PANEL.value:
            left_data = content.get("leftPanel", content.get("left", {}))
            right_data = content.get("rightPanel", content.get("right", {}))

            left_panel = GyMLPanel(
                title=left_data.get("title", ""), content=left_data.get("content", "")
            )
            right_panel = GyMLPanel(
                title=right_data.get("title", ""), content=right_data.get("content", "")
            )
            return GyMLSplitPanel(left_panel=left_panel, right_panel=right_panel)

        # Formula Block
        elif block_type == BlockType.FORMULA_BLOCK.value:
            expression = content.get("expression", content.get("formula", ""))
            example = content.get("example", content.get("description", ""))
            variables_data = content.get("variables", [])

            variables = []
            if isinstance(variables_data, list):
                for var in variables_data:
                    variables.append(
                        GyMLFormulaVariable(
                            name=var.get("name", ""),
                            definition=var.get("definition", ""),
                        )
                    )

            return GyMLFormulaBlock(
                expression=expression, variables=variables, example=example
            )

        # Hub and Spoke block
        elif block_type == BlockType.HUB_AND_SPOKE.value:
            hub_label = content.get("hub_label", content.get("title", "Core"))
            items_data = content.get("items", [])
            items = []
            for item in items_data:
                if isinstance(item, dict):
                    items.append(
                        GyMLHubAndSpokeItem(
                            label=item.get("label", ""),
                            description=item.get("description", item.get("text", "")),
                            color=item.get("color"),
                            icon=item.get("icon"),
                        )
                    )
                else:
                    items.append(GyMLHubAndSpokeItem(label=str(item)))

            return GyMLHubAndSpoke(
                hub_label=hub_label,
                items=items,
                variant=content.get("variant", "hexagon"),
            )

        # Cyclic block
        elif block_type == BlockType.CYCLIC_BLOCK.value:
            hub_label = content.get("hub_label", content.get("title"))
            items_data = content.get("items", [])
            items = []
            for item in items_data:
                if isinstance(item, dict):
                    items.append(
                        GyMLCyclicItem(
                            label=item.get("label", ""),
                            description=item.get(
                                "description", item.get("text", "")
                            ),
                            image_url=item.get(
                                "image_url",
                                item.get("imageUrl", item.get("imagePrompt")),
                            ),
                            icon=item.get("icon"),
                            color=item.get("color"),
                        )
                    )
                else:
                    items.append(GyMLCyclicItem(label=str(item)))

            return GyMLCyclicBlock(
                hub_label=hub_label,
                items=items,
                variant=content.get("variant", "chevron"),
            )

        # Sequential Output Block
        elif block_type == BlockType.SEQUENTIAL_OUTPUT.value:
             return GyMLSequentialOutput(items=content.get("items", []))

        # Process Arrow block
        elif block_type == BlockType.PROCESS_ARROW_BLOCK.value:
            items_data = content.get("items", [])

            items_data = content.get("items", [])
            items = []
            for item in items_data:
                if isinstance(item, dict):
                    items.append(
                        GyMLProcessArrowItem(
                            label=item.get("label", ""),
                            description=item.get(
                                "description", item.get("content", "")
                            ),
                            image_url=item.get(
                                "image_url",
                                item.get("imageUrl", item.get("imagePrompt")),
                            ),
                            color=item.get("color"),
                        )
                    )
            return GyMLProcessArrowBlock(items=items)

        # Cyclic Process block
        elif block_type == BlockType.CYCLIC_PROCESS_BLOCK.value:
            items_data = content.get("items", [])

            items_data = content.get("items", [])
            items = []
            for item in items_data:
                if isinstance(item, dict):
                    items.append(
                        GyMLCyclicProcessItem(
                            label=item.get("label", ""),
                            description=item.get(
                                "description", item.get("content", "")
                            ),
                            # Store imagePrompt in image_url for the generator to pick it up
                            image_url=item.get(
                                "image_url",
                                item.get("imageUrl", item.get("imagePrompt")),
                            ),
                        )
                    )
            return GyMLCyclicProcessBlock(items=items)

        # Feature Showcase block
        elif block_type == BlockType.FEATURE_SHOWCASE_BLOCK.value:
            title = content.get("title", content.get("hub_label", "Features"))
            image_url = content.get("image_url", content.get("imageUrl"))
            image_prompt = content.get("image_prompt", content.get("imagePrompt"))
            items_data = content.get("items", [])
            items = []
            for item in items_data:
                if isinstance(item, dict):
                    items.append(
                        GyMLFeatureShowcaseItem(
                            label=item.get("label", ""),
                            description=item.get("description", item.get("text", "")),
                            icon=item.get("icon"),
                            color=item.get("color"),
                        )
                    )
                else:
                    items.append(GyMLFeatureShowcaseItem(label=str(item)))
            return GyMLFeatureShowcaseBlock(
                title=title,
                items=items,
                image_url=image_url,
                image_prompt=image_prompt,
            )

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
                heading = item.get("heading", item.get("label", item.get("title", "")))

                # Points support - keep as list for premium rendering
                points = item.get("points")
                desc = item.get(
                    "text", item.get("description", item.get("content", ""))
                )

                # Support variant specific LLM output (e.g. comparisonBeforeAfter, comparison)
                if not desc:
                    before_val = item.get("before")
                    after_val = item.get("after")
                    if before_val and after_val:
                        desc = f"Before: {before_val}\nAfter: {after_val}"
                    else:
                        pros_val = item.get("pros", item.get("pro"))
                        cons_val = item.get("cons", item.get("con"))
                        if pros_val and cons_val:
                            desc = f"Pros: {pros_val}\nCons: {cons_val}"

                if isinstance(points, list):
                    pass
                else:
                    points = None

                gyml_items.append(
                    GyMLSmartLayoutItem(
                        icon=GyMLIcon(alt=icon_alt) if icon_alt else None,
                        heading=heading,
                        description=desc,
                        points=points,
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
