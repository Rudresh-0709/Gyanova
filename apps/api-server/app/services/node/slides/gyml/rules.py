"""
GyML Rules

Dynamic rules, grammars, and validation logic.
See: slide_engine.md, gyanova_markup_language.md
"""

from typing import List, Dict, Set, Optional
from dataclasses import dataclass

from .constants import BlockType, Intent


# =============================================================================
# BLOCK ORDERING GRAMMAR
# =============================================================================

# From slide_engine.md §8
# Blocks must follow this grammar:
# [Heading] → [Context/Framing] → [Main Content 1-3] → [Supplementary] → [Takeaway]

BLOCK_ORDER_GRAMMAR = [
    "heading",  # Always first
    "context",  # Optional framing (paragraph, callout)
    "main_content",  # 1-3 main blocks (lists, grids, timelines)
    "supplementary",  # Optional (callouts, blockquotes, images)
    "takeaway",  # Always last (if present)
]

# Which block types belong to which grammar position
BLOCK_GRAMMAR_MAPPING: Dict[str, List[str]] = {
    "heading": [BlockType.HEADING.value],
    "context": [BlockType.PARAGRAPH.value, BlockType.CALLOUT.value],
    "main_content": [
        BlockType.BULLET_LIST.value,
        BlockType.STEP_LIST.value,
        BlockType.CARD_GRID.value,
        BlockType.TIMELINE.value,
        BlockType.SMART_LAYOUT.value,
        BlockType.COLUMNS.value,
        BlockType.STATS.value,
    ],
    "supplementary": [
        BlockType.CALLOUT.value,
        BlockType.IMAGE.value,
        BlockType.DIVIDER.value,
    ],
    "takeaway": [BlockType.TAKEAWAY.value],
}


def get_block_grammar_position(block_type: str) -> str:
    """Get the grammar position for a block type."""
    for position, types in BLOCK_GRAMMAR_MAPPING.items():
        if block_type in types:
            return position
    return "main_content"  # Default to main content


def validate_block_order(block_types: List[str]) -> List[str]:
    """
    Validate that blocks follow the ordering grammar.
    Returns list of violations.
    """
    violations = []

    # Track grammar positions we've seen
    seen_positions = []
    position_order = {pos: i for i, pos in enumerate(BLOCK_ORDER_GRAMMAR)}

    for block_type in block_types:
        position = get_block_grammar_position(block_type)

        # Check if this position comes after all previous positions
        if seen_positions:
            last_position = seen_positions[-1]
            if position_order.get(position, 0) < position_order.get(last_position, 0):
                # Heading must always be first
                if position == "heading" and last_position != "heading":
                    violations.append(
                        f"Heading must be first, found after {last_position}"
                    )
                # Takeaway must always be last
                elif last_position == "takeaway":
                    violations.append(
                        f"Takeaway must be last, found {block_type} after it"
                    )

        seen_positions.append(position)

    return violations


# =============================================================================
# NESTING RULES
# =============================================================================

# From gyanova_markup_language.md §11
NESTING_RULES: Dict[str, List[str]] = {
    "section": ["img", "body"],
    "body": ["h1", "h2", "h3", "h4", "p", "columns", "smart-layout", "img", "divider"],
    "columns": ["div"],
    "div": ["h1", "h2", "h3", "h4", "p", "smart-layout", "img"],
    "smart-layout": ["smart-layout-item"],
    "smart-layout-item": ["icon", "div", "h4", "p"],
}

# Forbidden nesting combinations
NESTING_FORBIDDEN: Dict[str, Set[str]] = {
    "smart-layout": {"smart-layout"},  # No smart-layout inside smart-layout
    "columns": {"columns"},  # Columns inside columns discouraged
}

# Maximum recommended nesting depth
MAX_RECOMMENDED_DEPTH = 5


def is_nesting_allowed(parent: str, child: str) -> bool:
    """Check if a child element can be nested inside a parent."""
    allowed_children = NESTING_RULES.get(parent, [])
    return child in allowed_children


def is_nesting_forbidden(parent: str, child: str) -> bool:
    """Check if a nesting combination is explicitly forbidden."""
    forbidden = NESTING_FORBIDDEN.get(parent, set())
    return child in forbidden


# =============================================================================
# CONTENT COMPATIBILITY MATRIX
# =============================================================================

# Primary blocks - only ONE per slide
PRIMARY_BLOCKS: Set[str] = {
    BlockType.TIMELINE.value,
    BlockType.CARD_GRID.value,
    BlockType.STATS.value,
    BlockType.BULLET_LIST.value,
    BlockType.STEP_LIST.value,
    BlockType.COMPARISON.value,
    BlockType.QUOTE.value,
    BlockType.DEFINITION.value,
    BlockType.CODE.value,
    BlockType.DIAGRAM.value,
    BlockType.TABLE.value,
}

# Supporting blocks - can be added alongside primary
SUPPORTING_BLOCKS: Set[str] = {
    BlockType.CALLOUT.value,
    BlockType.TAKEAWAY.value,
    BlockType.DIVIDER.value,
    BlockType.IMAGE.value,
}

# Text blocks - always allowed
TEXT_BLOCKS: Set[str] = {
    BlockType.HEADING.value,
    BlockType.PARAGRAPH.value,
}

INTENT_PREFERRED_BLOCKS: Dict[str, List[str]] = {
    Intent.INTRODUCE.value: [BlockType.HEADING.value, BlockType.IMAGE.value],
    Intent.EXPLAIN.value: [BlockType.CARD_GRID.value, BlockType.SMART_LAYOUT.value],
    Intent.NARRATE.value: [BlockType.TIMELINE.value, BlockType.STEP_LIST.value],
    Intent.COMPARE.value: [
        BlockType.COMPARISON.value,
        BlockType.TABLE.value,
        BlockType.COLUMNS.value,
    ],
    Intent.LIST.value: [BlockType.BULLET_LIST.value, BlockType.STEP_LIST.value],
    Intent.PROVE.value: [BlockType.STATS.value, BlockType.QUOTE.value],
    Intent.SUMMARIZE.value: [BlockType.TAKEAWAY.value, BlockType.BULLET_LIST.value],
    Intent.TEACH.value: [
        BlockType.CODE.value,
        BlockType.DEFINITION.value,
        BlockType.DIAGRAM.value,
    ],
    Intent.DEMO.value: [BlockType.STEP_LIST.value, BlockType.CODE.value],
}
# Forbidden combinations - these blocks cannot appear together on same slide
FORBIDDEN_COMBINATIONS: Set[tuple] = {
    # Sequential conflicts
    (BlockType.TIMELINE.value, BlockType.STEP_LIST.value),
    (BlockType.STEP_LIST.value, BlockType.TIMELINE.value),
    # Visual overload
    (BlockType.TIMELINE.value, BlockType.STATS.value),
    (BlockType.STATS.value, BlockType.TIMELINE.value),
    (BlockType.TIMELINE.value, BlockType.CARD_GRID.value),
    (BlockType.CARD_GRID.value, BlockType.TIMELINE.value),
    # Information overload
    (BlockType.CARD_GRID.value, BlockType.STATS.value),
    (BlockType.STATS.value, BlockType.CARD_GRID.value),
    (BlockType.CARD_GRID.value, BlockType.BULLET_LIST.value),
    (BlockType.BULLET_LIST.value, BlockType.CARD_GRID.value),
    (BlockType.STATS.value, BlockType.BULLET_LIST.value),
    (BlockType.BULLET_LIST.value, BlockType.STATS.value),
    # Hierarchy confusion
    (BlockType.STEP_LIST.value, BlockType.BULLET_LIST.value),
    (BlockType.BULLET_LIST.value, BlockType.STEP_LIST.value),
    # Layout conflicts
    (BlockType.COMPARISON.value, BlockType.CARD_GRID.value),
    (BlockType.CARD_GRID.value, BlockType.COMPARISON.value),
    (BlockType.COMPARISON.value, BlockType.TABLE.value),
    (BlockType.TABLE.value, BlockType.COMPARISON.value),
    # Visual conflicts
    (BlockType.DIAGRAM.value, BlockType.TIMELINE.value),
    (BlockType.TIMELINE.value, BlockType.DIAGRAM.value),
    (BlockType.DIAGRAM.value, BlockType.CARD_GRID.value),
    (BlockType.CARD_GRID.value, BlockType.DIAGRAM.value),
    (BlockType.TABLE.value, BlockType.CARD_GRID.value),
    (BlockType.CARD_GRID.value, BlockType.TABLE.value),
    # Code conflicts
    (BlockType.CODE.value, BlockType.DIAGRAM.value),
    (BlockType.DIAGRAM.value, BlockType.CODE.value),
}

# Allowed combinations - primary block + what it works well with
COMPATIBLE_COMBINATIONS: Dict[str, List[str]] = {
    BlockType.TIMELINE.value: [
        BlockType.IMAGE.value,
        BlockType.CALLOUT.value,
        BlockType.TAKEAWAY.value,
    ],
    BlockType.CARD_GRID.value: [
        BlockType.IMAGE.value,
        BlockType.CALLOUT.value,
        BlockType.TAKEAWAY.value,
    ],
    BlockType.STATS.value: [
        BlockType.CALLOUT.value,
        BlockType.TAKEAWAY.value,
        BlockType.QUOTE.value,
    ],
    BlockType.BULLET_LIST.value: [
        BlockType.IMAGE.value,
        BlockType.CALLOUT.value,
        BlockType.TAKEAWAY.value,
    ],
    BlockType.STEP_LIST.value: [
        BlockType.IMAGE.value,
        BlockType.CALLOUT.value,
        BlockType.TAKEAWAY.value,
    ],
    BlockType.COMPARISON.value: [
        BlockType.CALLOUT.value,
        BlockType.TAKEAWAY.value,
    ],
    BlockType.QUOTE.value: [
        BlockType.IMAGE.value,
        BlockType.CALLOUT.value,
    ],
    BlockType.DEFINITION.value: [
        BlockType.IMAGE.value,
        BlockType.CALLOUT.value,
        BlockType.BULLET_LIST.value,  # Exception: can list related terms
    ],
    BlockType.CODE.value: [
        BlockType.CALLOUT.value,
        BlockType.TAKEAWAY.value,
    ],
    BlockType.DIAGRAM.value: [
        BlockType.CALLOUT.value,
        BlockType.TAKEAWAY.value,
    ],
    BlockType.TABLE.value: [
        BlockType.CALLOUT.value,
        BlockType.TAKEAWAY.value,
    ],
}


def is_combination_forbidden(block_a: str, block_b: str) -> bool:
    """Check if two blocks cannot appear on the same slide."""
    return (block_a, block_b) in FORBIDDEN_COMBINATIONS


def get_compatible_blocks(primary_block: str) -> List[str]:
    """Get list of blocks that work well with a primary block."""
    return COMPATIBLE_COMBINATIONS.get(primary_block, [])


def validate_block_combination(block_types: List[str]) -> List[str]:
    """
    Validate that blocks on a slide are compatible.
    Returns list of violations.
    """
    violations = []

    # Find primary blocks
    primary_on_slide = [b for b in block_types if b in PRIMARY_BLOCKS]

    # Only one primary block allowed
    if len(primary_on_slide) > 1:
        violations.append(
            f"Multiple primary blocks not allowed: {primary_on_slide}. Max 1 per slide."
        )

    # Check forbidden combinations
    for i, block_a in enumerate(block_types):
        for block_b in block_types[i + 1 :]:
            if is_combination_forbidden(block_a, block_b):
                violations.append(f"Forbidden combination: {block_a} + {block_b}")

    return violations


# =============================================================================
# VARIETY RULES
# =============================================================================


@dataclass
class SlidePattern:
    """Captures the pattern of a slide for variety checking."""

    dominant_block_type: str
    block_count: int
    has_columns: bool
    has_smart_layout: bool
    density: str  # "dense", "medium", "light"


class VarietyRules:
    """
    Deck-level variety enforcement.
    From slide_engine.md §12.
    """

    @staticmethod
    def calculate_density(word_count: int) -> str:
        """Calculate slide density based on word count."""
        if word_count > 250:
            return "dense"
        elif word_count > 100:
            return "medium"
        else:
            return "light"

    @staticmethod
    def check_consecutive_pattern(
        prev_pattern: SlidePattern, curr_pattern: SlidePattern
    ) -> List[str]:
        """
        Check if two consecutive slides violate variety rules.
        Returns list of violations.

        From slide_engine.md §12: No two consecutive slides share the same
        dominant block pattern.
        """
        violations = []

        # Check same dominant block type
        if prev_pattern.dominant_block_type == curr_pattern.dominant_block_type:
            violations.append(
                f"Consecutive slides have same dominant block: {curr_pattern.dominant_block_type}"
            )

        # Check same block count
        if prev_pattern.block_count == curr_pattern.block_count:
            violations.append(
                f"Consecutive slides have same block count: {curr_pattern.block_count}"
            )

        # Check same orientation (columns/smart-layout)
        if (
            prev_pattern.has_columns == curr_pattern.has_columns
            and prev_pattern.has_smart_layout == curr_pattern.has_smart_layout
        ):
            if prev_pattern.has_columns or prev_pattern.has_smart_layout:
                violations.append("Consecutive slides have same layout orientation")

        return violations

    @staticmethod
    def check_density_alternation(patterns: List[SlidePattern]) -> List[str]:
        """
        Check density alternation pattern.
        Ideal: Dense → Light → Medium → Dense
        """
        violations = []

        # Count consecutive same-density slides
        for i in range(1, len(patterns)):
            if patterns[i].density == patterns[i - 1].density:
                if patterns[i].density == "dense":
                    violations.append(
                        f"Consecutive dense slides at positions {i-1} and {i}"
                    )

        return violations

    @staticmethod
    def suggest_recomposition(
        pattern: SlidePattern, prev_pattern: SlidePattern
    ) -> Dict:
        """
        Suggest changes to avoid variety violations.
        Returns suggested modifications.
        """
        suggestions = {}

        # If same dominant block, suggest alternative
        if pattern.dominant_block_type == prev_pattern.dominant_block_type:
            alternatives = {
                BlockType.BULLET_LIST.value: [
                    BlockType.CARD_GRID.value,
                    BlockType.STEP_LIST.value,
                ],
                BlockType.CARD_GRID.value: [
                    BlockType.BULLET_LIST.value,
                    BlockType.SMART_LAYOUT.value,
                ],
                BlockType.TIMELINE.value: [
                    BlockType.STEP_LIST.value,
                    BlockType.CARD_GRID.value,
                ],
            }
            if pattern.dominant_block_type in alternatives:
                suggestions["alternative_block"] = alternatives[
                    pattern.dominant_block_type
                ][0]

        # If same density, suggest adjustment
        if pattern.density == prev_pattern.density == "dense":
            suggestions["reduce_content"] = True

        return suggestions


# =============================================================================
# TEXT TO STRUCTURE PROMOTION
# =============================================================================

# From slide_engine.md §11
TEXT_PROMOTION_RULES = {
    "parallel_items_3_4": BlockType.BULLET_LIST,  # or CARD_GRID
    "sequential_steps": BlockType.STEP_LIST,
    "historical_sequence": BlockType.TIMELINE,
    "quantitative_comparison": BlockType.STATS,
    "structural_taxonomy": BlockType.CARD_GRID,
    "single_abstract_concept": BlockType.PARAGRAPH,
}


def suggest_block_type_from_content(content: Dict) -> str:
    """
    Suggest appropriate block type based on content structure.
    From slide_engine.md §11.
    """
    # Check for list-like content
    if "items" in content:
        items = content["items"]
        item_count = len(items)

        # Check if items are sequential/numbered
        if any(str(i + 1) in str(items[i])[:5] for i in range(min(3, item_count))):
            return BlockType.STEP_LIST.value

        # 3-4 parallel items
        if 3 <= item_count <= 4:
            return BlockType.BULLET_LIST.value

        # More items suggest card grid
        if item_count > 4:
            return BlockType.CARD_GRID.value

    # Check for timeline content
    if "events" in content or "years" in content:
        return BlockType.TIMELINE.value

    # Check for stats
    if "stats" in content or "numbers" in content:
        return BlockType.STATS.value

    # Default to paragraph
    return BlockType.PARAGRAPH.value


# =============================================================================
# INTENT-BASED BLOCK SELECTION
# =============================================================================

# Updated for new intents from llm_content_schema.md
INTENT_PREFERRED_BLOCKS: Dict[Intent, List[str]] = {
    Intent.INTRODUCE: [
        BlockType.HEADING.value,
        BlockType.PARAGRAPH.value,
        BlockType.IMAGE.value,
    ],
    Intent.EXPLAIN: [
        BlockType.PARAGRAPH.value,
        BlockType.CARD_GRID.value,
        BlockType.DEFINITION.value,
    ],
    Intent.NARRATE: [
        BlockType.TIMELINE.value,
        BlockType.STEP_LIST.value,
        BlockType.PARAGRAPH.value,
    ],
    Intent.COMPARE: [
        BlockType.COMPARISON.value,
        BlockType.TABLE.value,
        BlockType.STATS.value,
    ],
    Intent.LIST: [
        BlockType.BULLET_LIST.value,
        BlockType.STEP_LIST.value,
        BlockType.CARD_GRID.value,
    ],
    Intent.PROVE: [
        BlockType.STATS.value,
        BlockType.QUOTE.value,
        BlockType.CALLOUT.value,
    ],
    Intent.SUMMARIZE: [
        BlockType.BULLET_LIST.value,
        BlockType.TAKEAWAY.value,
        BlockType.CARD_GRID.value,
    ],
    Intent.TEACH: [
        BlockType.DEFINITION.value,
        BlockType.CODE.value,
        BlockType.DIAGRAM.value,
    ],
    Intent.DEMO: [
        BlockType.CODE.value,
        BlockType.STEP_LIST.value,
        BlockType.DIAGRAM.value,
    ],
}


def get_preferred_blocks_for_intent(intent: Intent) -> List[str]:
    """Get preferred block types for a given intent."""
    return INTENT_PREFERRED_BLOCKS.get(intent, [BlockType.PARAGRAPH.value])
