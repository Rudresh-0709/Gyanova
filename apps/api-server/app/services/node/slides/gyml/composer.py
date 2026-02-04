"""
GyML Composer

Compose slides from content following slide_engine.md rules.
Outputs GyML-agnostic IR (ComposedSlide) - knows nothing about GyML syntax.
"""

from typing import List, Dict, Any, Optional, Tuple
import uuid
import re

from .types import (
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

    def __init__(self):
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
        concepts = self._extract_concepts(content)
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

    def _extract_concepts(self, content: Dict[str, Any]) -> List[Dict[str, Any]]:
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

        # Extract blocks from various content structures
        if "points" in content:
            main_concept["blocks"].append(
                {
                    "type": BlockType.BULLET_LIST.value,
                    "content": {"items": content["points"]},
                }
            )

        if "contentBlocks" in content:
            for block in content["contentBlocks"]:
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

        # Check if splitting is needed
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

    def _split_slide(self, slide: ComposedSlide) -> List[ComposedSlide]:
        """Split an oversized slide into multiple slides."""
        slides = []

        # Gather all blocks
        all_blocks = []
        for section in slide.sections:
            all_blocks.extend(section.blocks)

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
                    ComposedSection(
                        purpose=SectionPurpose.CONTENT.value,
                        relationship=Relationship.FLOW.value,
                        primary_block=None,
                        secondary_blocks=chunk,
                    )
                ],
                image_layout=slide.image_layout if i == 0 else "blank",
                accent_image_url=slide.accent_image_url if i == 0 else None,
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
            elif visual_block and visual_block.type == BlockType.IMAGE.value and text_blocks:
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
        Assign emphasis levels.
        From slide_engine.md §9.

        Primary: Heading OR dominant visual (only one allowed)
        Secondary: Supporting blocks
        Tertiary: Details, examples, callouts
        """
        has_primary = False

        for section in slide.sections:
            for block in section.blocks:
                # Heading gets primary if no primary yet
                if block.type == BlockType.HEADING.value and not has_primary:
                    block.emphasis = Emphasis.PRIMARY
                    has_primary = True

                # Dominant visual structures get primary
                elif (
                    block.type
                    in [
                        BlockType.CARD_GRID.value,
                        BlockType.TIMELINE.value,
                        BlockType.SMART_LAYOUT.value,
                    ]
                    and not has_primary
                ):
                    block.emphasis = Emphasis.PRIMARY
                    has_primary = True

                # Callouts and images are tertiary
                elif block.type in [
                    BlockType.CALLOUT.value,
                    BlockType.IMAGE.value,
                    BlockType.TAKEAWAY.value,
                ]:
                    block.emphasis = Emphasis.TERTIARY

                # Everything else is secondary
                else:
                    if block.emphasis != Emphasis.PRIMARY:
                        block.emphasis = Emphasis.SECONDARY

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
