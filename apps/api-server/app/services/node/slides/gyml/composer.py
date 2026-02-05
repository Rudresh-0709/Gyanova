"""
GyML Composer

Compose slides from content following slide_engine.md rules.
Outputs GyML-agnostic IR (ComposedSlide) - knows nothing about GyML syntax.
"""

from typing import List, Dict, Any, Optional, Tuple
import uuid
import re

from .definitions import (
    ComposedSlide,
    ComposedSection,
    ComposedBlock,
    Emphasis,
)
from .constants import (
    Intent,
    BlockType,
    SectionPurpose,
    Limits,
    INTENT_KEYWORDS,
    Relationship,
    CodeRole,
    SmartLayoutVariant,
)
from .rules import (
    BLOCK_ORDER_GRAMMAR,
    get_block_grammar_position,
    validate_block_order,
    VarietyRules,
    SlidePattern,
    get_preferred_blocks_for_intent,
    suggest_block_type_from_content,
)
from .hierarchy import VisualHierarchy
from .fitness import SlideFitnessGate, FitnessException
from .image_manager import ImageManager


class SlideComposer:
    """
    Compose slides from content following slide_engine.md rules.

    Output: ComposedSlide (format-agnostic IR)
    Does NOT know about GyML syntax.

    Responsibilities:
    - Intent detection
    - Concept grouping (≤1 idea per slide)
    - Block ordering grammar
    - Emphasis assignment
    - Limit enforcement (auto-split)
    - Variety checks (deck-level)
    """

    def __init__(self, theme: Optional["Theme"] = None):
        from .theme import THEMES

        self.theme = theme or THEMES["gamma_light"]
        self.previous_patterns: List[SlidePattern] = []

    def compose(self, content: Dict[str, Any]) -> List[ComposedSlide]:
        """
        Full composition pipeline.

        Args:
            content: Raw content with title, points, blocks, etc.

        Returns:
            List of ComposedSlide (may split into multiple slides)
        """
        # 1. Detect intent
        intent = self._detect_intent(content)

        # 2. Extract and group concepts
        concepts = self._extract_concepts(content, intent)
        grouped = self._group_concepts(concepts)

        # 3. Create slides from grouped concepts
        slides = []
        for i, group in enumerate(grouped):
            slide = self._create_slide(group, intent, i)

            # 4. Enforce limits (auto-split if needed)
            split_slides = self._enforce_limits(slide)

            # 5. Apply ordering grammar to each slide
            for s in split_slides:
                s = self._apply_ordering(s)

                # 6. Assign emphasis
                s = self._assign_emphasis(s)

                # 6b. Distribute Content (Layout Optimization)
                s = self._distribute_content(s)

                # 7. Assign Visual Hierarchy
                s = self._assign_hierarchy(s)

                # 8. Visual Balance Check (New)
                s = self._ensure_visual_balance(s)

                slides.append(s)

        # 7. Deck-level variety enforcement
        slides = self._enforce_variety(slides)

        return slides

    def compose_single(self, content: Dict[str, Any]) -> ComposedSlide:
        """Compose a single slide (no splitting)."""
        slides = self.compose(content)
        return slides[0] if slides else self._create_fallback_slide(content)

    # =========================================================================
    # INTENT DETECTION
    # =========================================================================

    def _detect_intent(self, content: Dict[str, Any]) -> Intent:
        """
        Detect slide intent from content.
        From slide_engine.md §4.
        """
        # Check explicit intent
        if "intent" in content:
            try:
                return Intent(content["intent"])
            except ValueError:
                pass

        # Infer from heading/title
        title = content.get("title", "") or content.get("heading", "")
        title_lower = title.lower()

        for intent, keywords in INTENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in title_lower:
                    return intent

        # Infer from content structure
        if "timeline" in content or "events" in content:
            return Intent.NARRATE
        if "comparison" in content or "vs" in title_lower:
            return Intent.COMPARE
        if "summary" in content:
            return Intent.SUMMARIZE
        if "prove" in content or "stats" in content:
            return Intent.PROVE
        if "teach" in content or "code" in content or "definition" in content:
            return Intent.TEACH
        if "demo" in content or "steps" in content:
            return Intent.DEMO

        # Default to EXPLAIN
        return Intent.EXPLAIN

    # =========================================================================
    # CONCEPT EXTRACTION & GROUPING
    # =========================================================================

    def _extract_concepts(
        self, content: Dict[str, Any], intent: Intent = Intent.EXPLAIN
    ) -> List[Dict[str, Any]]:
        """
        Extract distinct concepts from content.
        Each concept becomes a potential slide.
        """
        concepts = []

        # Main content as a concept
        main_concept = {
            "title": content.get("title", ""),
            "blocks": [],
        }

        if "summary" in content:
            main_concept["blocks"].append(
                {
                    "type": BlockType.PARAGRAPH.value,
                    "content": {"text": content["summary"]},
                }
            )

        if "image" in content:
            main_concept["image"] = content["image"]

        # Extract blocks from various content structures
        if "points" in content:
            points = content["points"]
            # Smart Layout Decision
            layout_variant = self._select_smart_layout(intent.value, points)

            if layout_variant == SmartLayoutVariant.BULLET_ICON.value:
                # Default behavior
                main_concept["blocks"].append(
                    {
                        "type": BlockType.BULLET_LIST.value,
                        "content": {"items": points},
                    }
                )
            else:
                # Upgrade to Smart Layout
                items = []
                for p in points:
                    item_data = {}
                    if isinstance(p, str):
                        # Attempt to parse specific formats based on layout
                        if layout_variant == "timeline":
                            # Try "1990: Event" or "1990 - Event"
                            import re

                            # Regex supports: "2010", "2010s", "2010-2014", "2010–2014" (en-dash)
                            match = re.match(
                                r"^(\d{4}(?:s)?(?:[\u2013-]\d{4})?)\s*[:\u2013-]\s*(.*)",
                                p,
                            )
                            if match:
                                item_data = {
                                    "year": match.group(1),
                                    "description": match.group(2),
                                }
                            else:
                                item_data = {"heading": p}  # Fallback
                        else:
                            item_data = {"heading": p}
                    else:
                        item_data = p

                    items.append(item_data)

                main_concept["blocks"].append(
                    {
                        "type": BlockType.SMART_LAYOUT.value,
                        "content": {"variant": layout_variant, "items": items},
                    }
                )

        # Support both 'contentBlocks' (legacy) and 'blocks' (playground/new)
        raw_blocks = content.get("contentBlocks", content.get("blocks", []))
        if raw_blocks:
            for block in raw_blocks:
                # Pass through the block structure directly
                # The serializer will handle the specific fields (code, table, etc.)
                main_concept["blocks"].append(
                    {
                        "type": block.get("type", BlockType.PARAGRAPH.value),
                        "content": block,
                    }
                )

        if "paragraph" in content or "text" in content:
            main_concept["blocks"].append(
                {
                    "type": BlockType.PARAGRAPH.value,
                    "content": {
                        "text": content.get("paragraph") or content.get("text", "")
                    },
                }
            )

        if "sections" in content:
            for section in content["sections"]:
                for block in section.get("blocks", []):
                    main_concept["blocks"].append(block)

        concepts.append(main_concept)

        return concepts

    def _group_concepts(
        self, concepts: List[Dict[str, Any]]
    ) -> List[List[Dict[str, Any]]]:
        """
        Group concepts into slide-sized chunks.
        From slide_engine.md §5.

        MERGE if:
        - Elements explain the same idea
        - Elements are mutually dependent
        - Cognitive load remains manageable

        SPLIT if:
        - Elements answer different questions
        - Visual structures differ significantly
        - Cognitive load exceeds limits
        """
        groups = []
        current_group = []
        current_block_count = 0

        for concept in concepts:
            block_count = len(concept.get("blocks", []))

            # Check if adding this concept exceeds limits
            if current_block_count + block_count > Limits.MAX_MAIN_CONTENT_BLOCKS + 2:
                # Start new group
                if current_group:
                    groups.append(current_group)
                current_group = [concept]
                current_block_count = block_count
            else:
                current_group.append(concept)
                current_block_count += block_count

        if current_group:
            groups.append(current_group)

        return groups if groups else [[]]

    # =========================================================================
    # SLIDE CREATION
    # =========================================================================

    def _create_slide(
        self, concept_group: List[Dict[str, Any]], intent: Intent, index: int
    ) -> ComposedSlide:
        """Create a ComposedSlide from a concept group."""
        slide_id = f"slide_{uuid.uuid4().hex[:8]}"

        sections = []

        for concept in concept_group:
            title = concept.get("title", "")
            blocks = concept.get("blocks", [])

            # Create title section if we have a title
            if title and index == 0:
                title_section = ComposedSection(
                    purpose=SectionPurpose.INTRODUCTION.value,
                    relationship=Relationship.FLOW.value,
                    primary_block=None,
                    secondary_blocks=[
                        ComposedBlock(
                            type=BlockType.HEADING.value,
                            content={"text": title, "level": 1},
                            emphasis=Emphasis.PRIMARY,
                        )
                    ],
                )
                sections.append(title_section)

            # Create content section
            if blocks:
                content_blocks = []
                for block in blocks:
                    composed_block = ComposedBlock(
                        type=block.get("type", BlockType.PARAGRAPH.value),
                        content=block.get("content", block),
                        emphasis=Emphasis.SECONDARY,
                    )
                    content_blocks.append(composed_block)

                content_section = ComposedSection(
                    purpose=SectionPurpose.CONTENT.value,
                    relationship=Relationship.FLOW.value,
                    primary_block=None,
                    secondary_blocks=content_blocks,
                )
                sections.append(content_section)

        # Determine image layout
        image_layout = "blank"
        accent_image = None
        if "image" in concept_group[0] if concept_group else {}:
            image = concept_group[0].get("image", {})
            accent_image = image.get("url")
            image_layout = image.get("layout", "right")

        return ComposedSlide(
            id=slide_id,
            intent=intent.value,
            sections=sections,
            accent_image_url=accent_image,
            image_layout=image_layout,
        )

    def _create_fallback_slide(self, content: Dict[str, Any]) -> ComposedSlide:
        """
        Create minimal fallback slide.
        From slide_engine.md §15.
        """
        return ComposedSlide(
            id=f"slide_{uuid.uuid4().hex[:8]}",
            intent=Intent.EXPLAIN.value,
            sections=[
                ComposedSection(
                    purpose=SectionPurpose.CONTENT.value,
                    relationship=Relationship.FLOW.value,
                    primary_block=None,
                    secondary_blocks=[
                        ComposedBlock(
                            type=BlockType.HEADING.value,
                            content={"text": content.get("title", "Slide"), "level": 1},
                            emphasis=Emphasis.PRIMARY,
                        ),
                        ComposedBlock(
                            type=BlockType.PARAGRAPH.value,
                            content={"text": content.get("text", "")},
                            emphasis=Emphasis.SECONDARY,
                        ),
                    ],
                )
            ],
        )

    # =========================================================================
    # LIMIT ENFORCEMENT
    # =========================================================================

    def _enforce_limits(self, slide: ComposedSlide) -> List[ComposedSlide]:
        """
        Enforce implicit limits, auto-split if exceeded.
        From slide_engine.md §6, §13.
        """
        # Rule: Smart Layout > 4 items -> Split Content
        for section in slide.sections:
            for block in section.blocks:

                # Check for Smart Layout / Card Grid / Timeline
                items = []
                layout_type = block.type
                variant = None

                if block.type == BlockType.SMART_LAYOUT.value:
                    items = block.content.get("items", [])
                    variant = block.content.get("variant")
                elif block.type in [
                    BlockType.TIMELINE.value,
                    BlockType.CARD_GRID.value,
                    BlockType.STEP_LIST.value,
                ]:
                    # Legacy or specific types
                    # Normalized access to items list
                    if "events" in block.content:
                        items = block.content["events"]
                    elif "cards" in block.content:
                        items = block.content["cards"]
                    elif "items" in block.content:
                        items = block.content["items"]

                # Check Limit (MAX 4 for complex layouts, 5 for simple)
                limit = 4
                if len(items) > limit:
                    # Attempt to reflow into columns first (Dense Mode)
                    reflowed_slide = self._try_reflow_dense_content(slide, block)
                    if reflowed_slide:
                        return [reflowed_slide]

                    # Fallback to splitting
                    return self._split_smart_layout_content(slide, block, items, limit)

        word_count = slide.total_word_count()
        block_count = slide.block_count()

        # Count visual elements and containers
        visual_count = 0
        container_count = 0
        for section in slide.sections:
            for block in section.blocks:
                if block.type in [BlockType.IMAGE.value, BlockType.CARD_GRID.value]:
                    visual_count += 1
                if block.type in [
                    BlockType.COLUMNS.value,
                    BlockType.SMART_LAYOUT.value,
                ]:
                    container_count += 1

        # Check if splitting is needed (Standard block splitting)
        should_split = Limits.should_split_slide(
            word_count=word_count,
            concept_count=block_count,  # Approximate
            visual_count=visual_count,
            container_count=container_count,
            main_block_count=block_count,
        )

        if should_split:
            return self._split_slide(slide)

        return [slide]

    def _try_reflow_dense_content(
        self, slide: ComposedSlide, content_block: ComposedBlock
    ) -> Optional[ComposedSlide]:
        """
        Attempt to reflow a dense slide into a 2-column layout.
        Strategy:
        - Col 1 (40%): Accent Image (converted to inline) + Summary/Intro Paragraphs
        - Col 2 (60%): The oversized Smart Layout (Timeline, Grid, etc.)
        """
        # 1. Identify components to move
        image_url = slide.accent_image_url
        intro_blocks = []

        # Find intro paragraphs (usually before the smart layout)
        # We assume the content_block is in the main content section
        target_section = None
        for section in slide.sections:
            if content_block in section.secondary_blocks:
                target_section = section
                break

        if not target_section:
            return None

        # Gather intro blocks (everything before the main content block)
        for b in target_section.secondary_blocks:
            if b == content_block:
                break
            if b.type == BlockType.PARAGRAPH.value:
                intro_blocks.append(b)

        # 2. Check if we have enough material to justify columns
        # We need at least (Image OR Intro) AND Content Block
        if not (image_url or intro_blocks):
            return None  # Nothing to put in the side column

        # 3. Construct Columns
        col1_blocks = []

        # Add Image
        if image_url:
            col1_blocks.append(
                ComposedBlock(
                    type=BlockType.IMAGE.value,
                    content={
                        "src": image_url,
                        "alt": "Slide Image",
                        "is_accent": False,
                    },
                    emphasis=Emphasis.SECONDARY,
                )
            )

        # Add Intro Text
        col1_blocks.extend(intro_blocks)

        # Col 2 is just the content block
        col2_blocks = [content_block]

        # Create Column Container
        columns_block = ComposedBlock(
            type=BlockType.COLUMNS.value,
            content={
                "colwidths": [40, 60],
                "columns": [
                    {"blocks": col1_blocks},  # Column 1
                    {"blocks": col2_blocks},  # Column 2
                ],
            },
            emphasis=Emphasis.PRIMARY,
        )

        # 4. Rebuild Slide
        # We keep the Title Section (index 0 usually)
        # We replace the Content Section body with the new Columns block

        new_sections = []
        for section in slide.sections:
            if section == target_section:
                # Replace this section's content
                new_section = ComposedSection(
                    purpose=section.purpose,
                    relationship=section.relationship,
                    primary_block=section.primary_block,
                    secondary_blocks=[columns_block],  # Replaced!
                )
                new_sections.append(new_section)
            else:
                new_sections.append(section)

        # Create hierarchy profile
        from .hierarchy import VisualHierarchy

        dense_profile = VisualHierarchy.get_profile("super_dense")

        # Return new slide with "blank" image layout (since we moved image inside)
        return ComposedSlide(
            id=slide.id,
            intent=slide.intent,
            sections=new_sections,
            image_layout="blank",
            accent_image_url=None,  # Removed
            hierarchy=dense_profile,  # Applied explicit hierarchy
        )

    def _split_smart_layout_content(
        self,
        slide: ComposedSlide,
        block: ComposedBlock,
        items: List[Any],
        chunk_size: int,
    ) -> List[ComposedSlide]:
        """
        Split a single oversized Smart Layout block into multiple slides.
        """
        slides = []
        chunks = [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]

        total_parts = len(chunks)

        for i, chunk in enumerate(chunks):
            # Create a Deep Copy of the base slide structure
            # (Simplest way is to re-instantiate, or use copy module if available)
            # We'll re-instantiate key parts to be safe.

            # Title suffix: "Title (1/2)"
            base_title_block = None
            if slide.sections and slide.sections[0].secondary_blocks:
                for b in slide.sections[0].secondary_blocks:
                    if b.type == BlockType.HEADING.value:
                        base_title_block = b
                        break

            title_text = (
                base_title_block.content.get("text", "Slide")
                if base_title_block
                else "Slide"
            )
            if total_parts > 1:
                title_text = f"{title_text} ({i+1}/{total_parts})"

            # Reconstruct content block with sliced items
            new_content = block.content.copy()
            if block.type == BlockType.SMART_LAYOUT.value:
                new_content["items"] = chunk
            elif "events" in new_content:
                new_content["events"] = chunk
            elif "cards" in new_content:
                new_content["cards"] = chunk
            elif "items" in new_content:
                new_content["items"] = chunk

            new_block = ComposedBlock(
                type=block.type, content=new_content, emphasis=Emphasis.PRIMARY
            )

            # Create Slide
            new_slide = ComposedSlide(
                id=f"{slide.id}_part_{i}",
                intent=slide.intent,
                sections=[
                    # Title Section
                    ComposedSection(
                        purpose=SectionPurpose.INTRODUCTION.value,
                        relationship=Relationship.FLOW.value,
                        primary_block=None,
                        secondary_blocks=[
                            ComposedBlock(
                                type=BlockType.HEADING.value,
                                content={"text": title_text, "level": 1},
                                emphasis=Emphasis.PRIMARY,
                            )
                        ],
                    ),
                    # Content Section
                    ComposedSection(
                        purpose=SectionPurpose.CONTENT.value,
                        relationship=Relationship.FLOW.value,
                        primary_block=None,
                        secondary_blocks=[new_block],
                    ),
                ],
                image_layout=(
                    slide.image_layout if i == 0 else "blank"
                ),  # Only first slide gets the big image
                accent_image_url=slide.accent_image_url if i == 0 else None,
            )
            slides.append(new_slide)

        return slides

    def _split_slide(self, slide: ComposedSlide) -> List[ComposedSlide]:
        """Split an oversized slide (multiple blocks) into multiple slides."""
        slides = []

        # Gather all blocks
        all_blocks = []
        for section in slide.sections:
            if section.purpose == SectionPurpose.CONTENT.value:
                all_blocks.extend(section.secondary_blocks)

        if not all_blocks:
            return [slide]  # Nothing to split

        # Split blocks into chunks
        chunk_size = Limits.MAX_MAIN_CONTENT_BLOCKS
        chunks = [
            all_blocks[i : i + chunk_size]
            for i in range(0, len(all_blocks), chunk_size)
        ]

        for i, chunk in enumerate(chunks):
            new_slide = ComposedSlide(
                id=f"{slide.id}_{i}",
                intent=slide.intent,
                sections=[
                    # Title (Reused)
                    slide.sections[0] if slide.sections else None,
                    # Content
                    ComposedSection(
                        purpose=SectionPurpose.CONTENT.value,
                        relationship=Relationship.FLOW.value,
                        primary_block=None,
                        secondary_blocks=chunk,
                    ),
                ],
                image_layout=slide.image_layout if i == 0 else "blank",
                accent_image_url=slide.accent_image_url if i == 0 else None,
            )
            # Fix Title Reuse issue (should clone or just accept it)
            # For now, simplistic reuse
            if new_slide.sections[0] is None:
                # Fallback title
                new_slide.sections.insert(
                    0,
                    ComposedSection(
                        purpose=SectionPurpose.INTRODUCTION.value,
                        relationship=Relationship.FLOW.value,
                        primary_block=None,
                        secondary_blocks=[
                            ComposedBlock(
                                BlockType.HEADING.value,
                                {"text": "Continued", "level": 1},
                                Emphasis.PRIMARY,
                            )
                        ],
                    ),
                )

            slides.append(new_slide)

        return slides if slides else [slide]

    # =========================================================================
    # ORDERING
    # =========================================================================

    # =========================================================================
    # OPTIMIZATION (AUTO-LAYOUT)
    # =========================================================================

    def _resolve_relationships(self, slide: ComposedSlide) -> ComposedSlide:
        """
        Decide content relationships (FLOW vs PARALLEL vs ANCHORED).

        Replaces _optimize_layout.
        Does NOT decide columns or grids - just relationships.
        """
        for section in slide.sections:
            # Start with FLOW (Primary=None, all in Secondary)
            blocks = section.secondary_blocks

            # Identify candidates
            text_blocks = []
            visual_block = None

            # 1. Scan for Visuals
            for block in blocks:
                if block.type in [
                    BlockType.TIMELINE.value,
                    BlockType.CARD_GRID.value,
                    BlockType.SMART_LAYOUT.value,
                    BlockType.CODE.value,
                    BlockType.TABLE.value,
                    BlockType.STATS.value,
                    BlockType.COMPARISON.value,
                    BlockType.IMAGE.value,
                ]:
                    if visual_block is None:
                        visual_block = block

                if block.type in [
                    BlockType.PARAGRAPH.value,
                    BlockType.CALLOUT.value,
                    BlockType.TAKEAWAY.value,
                    BlockType.QUOTE.value,
                    BlockType.BULLET_LIST.value,
                    BlockType.STEP_LIST.value,
                ]:
                    text_blocks.append(block)

            # 2. Decision Logic

            # CASE A: Parallel (Text + Heavy Visual)
            if text_blocks and visual_block:
                section.relationship = Relationship.PARALLEL.value
                section.primary_block = visual_block

                # Remove visual from secondary pool
                new_secondary = []
                for b in blocks:
                    if b == visual_block:
                        continue
                    new_secondary.append(b)
                section.secondary_blocks = new_secondary

            # CASE B: Anchored (Text + Image)
            elif (
                visual_block
                and visual_block.type == BlockType.IMAGE.value
                and text_blocks
            ):
                section.relationship = Relationship.ANCHORED.value
                section.primary_block = visual_block

                new_secondary = []
                for b in blocks:
                    if b == visual_block:
                        continue
                    new_secondary.append(b)
                section.secondary_blocks = new_secondary

        return slide

    def _apply_ordering(self, slide: ComposedSlide) -> ComposedSlide:
        """
        Apply block ordering grammar.
        From slide_engine.md §8.
        """
        for section in slide.sections:
            # Sort secondary_blocks by grammar position
            # (primary_block is usually None at this stage as we init as FLOW)
            if section.secondary_blocks:
                section.secondary_blocks.sort(
                    key=lambda b: (
                        BLOCK_ORDER_GRAMMAR.index(get_block_grammar_position(b.type))
                        if get_block_grammar_position(b.type) in BLOCK_ORDER_GRAMMAR
                        else 2
                    )
                )

        # Relationship pass: Decide FLOW vs PARALLEL vs ANCHORED
        slide = self._resolve_relationships(slide)

        return slide

    # =========================================================================
    # EMPHASIS
    # =========================================================================

    def _assign_emphasis(self, slide: ComposedSlide) -> ComposedSlide:
        """
        Assign emphasis and roles.
        Enforces Rule: Exactly ONE dominant block per slide.
        """
        for section in slide.sections:
            blocks = section.blocks  # Access all blocks via property

            # Reset all to secondary initially
            for b in blocks:
                b.emphasis = Emphasis.SECONDARY

            # 1. Identify Candidate for Dominance
            dominant_candidate = None

            # Check for explicitly assigned roles (e.g. Code Primary)
            for b in blocks:
                if b.role == CodeRole.PRIMARY.value:
                    dominant_candidate = b
                    break

            # If no explicit role, find heaviest visual
            if not dominant_candidate:
                for b in blocks:
                    if b.type in [
                        BlockType.TIMELINE.value,
                        BlockType.CARD_GRID.value,
                        BlockType.SMART_LAYOUT.value,
                        BlockType.STATS.value,
                        BlockType.COMPARISON.value,
                        BlockType.TABLE.value,
                        BlockType.DIAGRAM.value,
                    ]:
                        dominant_candidate = b
                        break

            # If still none, check for Code (default to primary if it's the only complex thing)
            if not dominant_candidate:
                for b in blocks:
                    if b.type == BlockType.CODE.value:
                        # Default role if not set
                        if not b.role:
                            b.role = CodeRole.PRIMARY.value
                        dominant_candidate = b
                        break

            # If still none, Heading is dominant
            if not dominant_candidate:
                for b in blocks:
                    if b.type == BlockType.HEADING.value:
                        dominant_candidate = b
                        break

            # 2. Apply Dominance - STRICT HIERARCHY
            # Rule: Heading is ALWAYS Primary if present.
            # Smart Layouts are Secondary (unless they ARE the only content).

            heading_block = next(
                (b for b in blocks if b.type == BlockType.HEADING.value), None
            )

            if heading_block:
                heading_block.emphasis = Emphasis.PRIMARY
                # All others degrade to Secondary/Tertiary
                for b in blocks:
                    if b == heading_block:
                        continue

                    if b.type in [BlockType.CALLOUT.value, BlockType.IMAGE.value]:
                        b.emphasis = Emphasis.TERTIARY
                    else:
                        b.emphasis = Emphasis.SECONDARY

            elif dominant_candidate:
                # No heading, so dominant block takes lead
                dominant_candidate.emphasis = Emphasis.PRIMARY
                for b in blocks:
                    if b == dominant_candidate:
                        continue
                    b.emphasis = Emphasis.SECONDARY

            else:
                # Fallback
                for b in blocks:
                    b.emphasis = Emphasis.SECONDARY

        return slide

    # =========================================================================
    # VARIETY
    # =========================================================================

    def _enforce_variety(self, slides: List[ComposedSlide]) -> List[ComposedSlide]:
        """
        Enforce deck-level variety.
        From slide_engine.md §12.
        """
        if len(slides) < 2:
            return slides

        patterns = [self._extract_pattern(s) for s in slides]

        for i in range(1, len(slides)):
            violations = VarietyRules.check_consecutive_pattern(
                patterns[i - 1], patterns[i]
            )

            if violations:
                # Try to recompose
                suggestions = VarietyRules.suggest_recomposition(
                    patterns[i], patterns[i - 1]
                )

                if "alternative_block" in suggestions:
                    slides[i] = self._recompose_with_alternative(
                        slides[i], suggestions["alternative_block"]
                    )
                    patterns[i] = self._extract_pattern(slides[i])

        # Store patterns for future slides
        self.previous_patterns = patterns

        return slides

    # =========================================================================
    # VISUAL HIERARCHY
    # =========================================================================

    def _optimize_sidebar_layout(self, slide: ComposedSlide) -> bool:
        """
        Reflow dense slides with secondary content into a 70/30 (or 60/40) sidebar layout.
        Moves Callouts/Notes under the user image (or injected placeholder).
        Returns True if optimization was applied.
        """
        # 1. Check triggers: Must have Code OR Dense Text
        has_dense_block = any(
            b.type in [BlockType.CODE.value, BlockType.TABLE.value]
            for s in slide.sections
            for b in s.blocks
        )
        is_dense = self._calculate_visual_density(slide) > 0.7

        if not (has_dense_block or is_dense):
            return False

        # 2. Check for Secondary Content to move (Callouts, small paragraphs)
        secondary_blocks = []
        primary_blocks = []

        main_section = slide.sections[0]  # Assuming single section for now
        print(
            f"DEBUG: Optimizer Blocks: {[b.type for b in main_section.blocks]}"
        )  # DEBUG

        for b in main_section.blocks:
            # Headings and Code always stay primary
            if b.type in [
                BlockType.HEADING.value,
                BlockType.CODE.value,
                BlockType.TABLE.value,
            ]:
                primary_blocks.append(b)
                continue

            # Callouts always go to sidebar
            if b.type == BlockType.CALLOUT.value:
                print("DEBUG: Found Callout")  # DEBUG
                secondary_blocks.append(b)
                continue

            # Paragraphs: Heuristic - if short/last, maybe sidebar?
            if b.type == BlockType.PARAGRAPH.value and b == main_section.blocks[-1]:
                text = b.content.get("text", "")
                # Simple check: starts with "Note:" or short
                if len(text) < 100 or text.startswith("Note:"):
                    secondary_blocks.append(b)
                    continue

            primary_blocks.append(b)

        if not secondary_blocks:
            return False

        # 3. Apply Transformation
        # Create Right Column Content: Image + Secondary Blocks
        right_col_blocks = []

        # Image First
        if slide.accent_image_url:
            right_col_blocks.append(
                ComposedBlock(
                    type=BlockType.IMAGE.value,
                    content={
                        "src": slide.accent_image_url,
                        "alt": slide.accent_image_alt or "",
                    },
                )
            )
        else:
            # Force placeholder if no image (user wants visual balance)
            right_col_blocks.append(
                ComposedBlock(
                    type=BlockType.IMAGE.value,
                    content={"src": "placeholder", "alt": "Decorative reference"},
                )
            )

        # Then Secondary Blocks
        right_col_blocks.extend(secondary_blocks)

        # Create Left Column Content: Primary Blocks
        left_col_blocks = primary_blocks

        # Create 2-Column Layout Block (IR)
        columns_block = ComposedBlock(
            type=BlockType.COLUMNS.value,
            content={
                "colwidths": [60, 40],
                "columns": [{"blocks": left_col_blocks}, {"blocks": right_col_blocks}],
            },
        )

        # Replace section content - using property setter hack?
        # No, blocks is a property returning list. We need to modify underlying storage.
        # ComposedSection has 'primary_block' and 'secondary_blocks'.
        # We'll set primary to None and secondary to [columns_block].
        main_section.primary_block = None
        main_section.secondary_blocks = [columns_block]

        # Disable default image layout since we moved the image manually
        slide.image_layout = "blank"

        # Force hierarchy to 'super_dense' for tighter spacing
        slide.hierarchy = VisualHierarchy.get_profile("super_dense")

        return True

    def _assign_hierarchy(self, slide: ComposedSlide) -> ComposedSlide:
        """
        Assign visual hierarchy constraints based on density and intent.
        """
        # Respect manually assigned hierarchy (e.g. from dense reflow)
        if slide.hierarchy:
            return slide

        word_count = slide.total_word_count()
        block_count = slide.block_count()

        # Calculate approximate density score
        # Arbitrary units: words + (blocks * 20)
        density_score = word_count + (block_count * 20)

        # Decision Logic
        profile_name = "default"

        if density_score > 150:
            profile_name = "dense"
        elif slide.intent in [Intent.PROVE.value, Intent.INTRODUCE.value]:
            # High impact slides
            profile_name = "impact"

        slide.hierarchy = VisualHierarchy.get_profile(profile_name)
        return slide

    def _distribute_content(self, slide: ComposedSlide) -> ComposedSlide:
        """
        Distribute content into appropriate sections/layouts.
        """
        # 0. Try Sidebar Optimization first (Code/Callout combo)
        if self._optimize_sidebar_layout(slide):
            return slide

        # 1. Try Smart Layouts (if not already optimized)
        if slide.hierarchy:
            return slide

        word_count = slide.total_word_count()
        block_count = slide.block_count()

        # Calculate approximate density score
        # Arbitrary units: words + (blocks * 20)
        density_score = word_count + (block_count * 20)

        # Decision Logic
        profile_name = "default"

        if density_score > 150:
            profile_name = "dense"
        elif slide.intent in [Intent.PROVE.value, Intent.INTRODUCE.value]:
            # High impact slides
            profile_name = "impact"

        slide.hierarchy = VisualHierarchy.get_profile(profile_name)
        return slide

    def _calculate_visual_density(self, slide: ComposedSlide) -> float:
        """
        Calculate visual density (0.0 to 1.0).
        Based on word count, block count, and presence of media.
        """
        MAX_WORDS = 150
        MAX_BLOCKS = 6

        word_score = min(slide.total_word_count() / MAX_WORDS, 1.0)
        block_score = min(slide.block_count() / MAX_BLOCKS, 1.0)

        # Images boost density significantly
        has_media = slide.accent_image_url or any(
            b.type == BlockType.IMAGE.value for s in slide.sections for b in s.blocks
        )
        media_bonus = 0.4 if has_media else 0.0

        return (word_score * 0.4) + (block_score * 0.2) + media_bonus

    def _ensure_visual_balance(self, slide: ComposedSlide) -> ComposedSlide:
        """
        Ensure slide meets visual density standards using FitnessGate.
        Delegates image placement to ImageManager.
        """
        # 1. Calculate Density
        # Skip if slide has explicit COLUMNS layout (Dense Mode)
        has_columns = any(
            block.type == BlockType.COLUMNS.value
            for section in slide.sections
            for block in (section.blocks + section.secondary_blocks)
        )
        if has_columns:
            return slide

        print(f"DEBUG: Block Count = {slide.block_count()}")  # DEBUG
        density = SlideFitnessGate._calculate_estimated_height(slide)
        print(f"DEBUG: Slide Density = {density}")  # DEBUG
        has_image = bool(slide.accent_image_url)

        # 2. Determine Image Strategy
        placement = ImageManager.determine_placement(density, has_image, slide.intent)
        print(f"DEBUG: Image Placement Decision = {placement}")  # DEBUG

        # 3. Apply Strategy
        if placement != "blank":
            slide.image_layout = placement

            # Inject placeholder if required but missing
            should_inject = ImageManager.should_inject_placeholder(density, has_image)
            print(f"DEBUG: Should Inject Placeholder? = {should_inject}")  # DEBUG
            if not has_image and should_inject:
                placeholder = ImageManager.get_placeholder_image()
                slide.accent_image_url = placeholder.src
                slide.accent_image_alt = placeholder.alt
        else:
            slide.image_layout = "blank"

        # 4. Final Hard Validation
        # If density is still critical < 0.25, we should technically fail.
        # Ideally, we would raise FitnessException here and catch it in compose()
        # to try a fallback strategy.
        is_valid, reason = SlideFitnessGate.validate_density(slide)
        if not is_valid:
            # TODO: Log this failure or handle specific fallback
            pass

        return slide

    def _select_smart_layout(self, intent: str, items: List[Any]) -> str:
        """
        Decision tree for selecting the best Smart Layout variant.
        Respects ThemeConstraints.
        """
        count = len(items)
        has_dates = any("year" in str(i) or "date" in str(i) for i in items[:3])
        has_numbers = any("value" in str(i) or "%" in str(i) for i in items[:3])

        # Check constraints if available
        constraints = (
            self.theme.constraints if hasattr(self, "theme") and self.theme else None
        )
        allowed = constraints.allowed_layouts if constraints else []

        # Helper to check if variant is allowed (if list is empty, all are allowed)
        def is_allowed(v):
            return not allowed or v in allowed

        # Helper to try a variant
        def try_variant(v, items):
            if not is_allowed(v):
                return False
            try:
                SlideFitnessGate.validate_constraints(None, v, items)
                return True
            except FitnessException:
                return False

        # 1. TIMELINE Logic
        if (intent == Intent.NARRATE.value or has_dates) and try_variant(
            "timeline", items
        ):
            return SmartLayoutVariant.TIMELINE.value

        # 2. COMPARISON Logic
        if intent == Intent.COMPARE.value:
            if count == 2 and try_variant("comparison", items):
                return SmartLayoutVariant.COMPARISON.value
            elif count == 3 and try_variant("solidBoxesWithIconsInside", items):
                return SmartLayoutVariant.SOLID_BOXES_WITH_ICONS.value
            elif try_variant("cardGrid", items):
                return SmartLayoutVariant.CARD_GRID.value

        # 3. PROVE / STATS Logic
        if (intent == Intent.PROVE.value or has_numbers) and try_variant(
            "stats", items
        ):
            return SmartLayoutVariant.STATS.value

        # 4. PROCESS / DEMO Logic
        if (intent == Intent.DEMO.value) and try_variant("processSteps", items):
            return SmartLayoutVariant.PROCESS_STEPS.value

        # 5. EXPLANATION / DEFAULT Logic
        if count <= 4 and try_variant("bigBullets", items):
            return SmartLayoutVariant.BIG_BULLETS.value
        elif try_variant("cardGrid", items):
            return SmartLayoutVariant.CARD_GRID.value

        return SmartLayoutVariant.BULLET_ICON.value

    def _extract_pattern(self, slide: ComposedSlide) -> SlidePattern:
        """Extract pattern from slide for variety checking."""
        dominant_type = BlockType.PARAGRAPH.value
        has_columns = False
        has_smart_layout = False

        for section in slide.sections:
            for block in section.blocks:
                if block.emphasis == Emphasis.PRIMARY:
                    dominant_type = block.type
                if block.type == BlockType.COLUMNS.value:
                    has_columns = True
                if block.type == BlockType.SMART_LAYOUT.value:
                    has_smart_layout = True

        density = VarietyRules.calculate_density(slide.total_word_count())

        return SlidePattern(
            dominant_block_type=dominant_type,
            block_count=slide.block_count(),
            has_columns=has_columns,
            has_smart_layout=has_smart_layout,
            density=density,
        )

    def _recompose_with_alternative(
        self, slide: ComposedSlide, alternative_type: str
    ) -> ComposedSlide:
        """Attempt to recompose slide with an alternative block type."""
        # This is a simplified implementation
        # In practice, would need more sophisticated content transformation
        for section in slide.sections:
            for block in section.blocks:
                if block.emphasis == Emphasis.PRIMARY:
                    # Keep the content, just change the type
                    if (
                        block.type == BlockType.BULLET_LIST.value
                        and alternative_type == BlockType.CARD_GRID.value
                    ):
                        # Transform bullet list to card grid
                        items = block.content.get("items", [])
                        block.type = BlockType.CARD_GRID.value
                        block.content = {
                            "cards": [
                                {"heading": item[:50], "text": item}
                                for item in items[:4]
                            ]
                        }

        return slide
