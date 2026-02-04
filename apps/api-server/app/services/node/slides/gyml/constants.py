"""
GyML Constants

Static values, enums, and limits from specifications.
See: slide_engine.md, gyanova_markup_language.md
"""

from enum import Enum
from typing import Tuple


class ImageLayout(Enum):
    """
    Image layout positions for accent images.
    From gyanova_markup_language.md §3.
    """

    RIGHT = "right"
    LEFT = "left"
    TOP = "top"
    BEHIND = "behind"
    BLANK = "blank"  # No accent image


class Relationship(Enum):
    """
    Semantic relationships between content blocks.
    Determines how the serializer maps them to layout.
    """

    FLOW = "flow"  # Sequential / Stacked
    PARALLEL = "parallel"  # Coexisting / Side-by-side
    ANCHORED = "anchored"  # Primary content + Accent


class SmartLayoutVariant(Enum):
    """
    Smart layout semantic variants.
    Expanded from llm_content_schema.md.
    """

    # Timeline variants
    TIMELINE = "timeline"  # Vertical
    TIMELINE_HORIZONTAL = "timelineHorizontal"  # Alternating above/below
    TIMELINE_SEQUENTIAL = "timelineSequential"  # Numbered steps
    TIMELINE_MILESTONE = "timelineMilestone"  # Key moments

    # Card grid variants
    CARD_GRID = "cardGrid"  # Default numbered
    CARD_GRID_ICON = "cardGridIcon"  # With icons
    CARD_GRID_SIMPLE = "cardGridSimple"  # Heading + text only
    CARD_GRID_IMAGE = "cardGridImage"  # With small images

    # Stats variants
    STATS = "stats"  # Big numbers
    STATS_COMPARISON = "statsComparison"  # Before/after
    STATS_PERCENTAGE = "statsPercentage"  # Progress circles/bars

    # Bullet list variants
    BIG_BULLETS = "bigBullets"  # Large numbered bullets
    BULLET_ICON = "bulletIcon"  # With icons
    BULLET_CHECK = "bulletCheck"  # Checkmarks
    BULLET_CROSS = "bulletCross"  # X marks

    # Step list variants
    PROCESS_STEPS = "processSteps"  # Numbered vertical
    PROCESS_ARROW = "processArrow"  # Steps with arrows
    PROCESS_ACCORDION = "processAccordion"  # Expandable

    # Comparison variants
    COMPARISON = "comparison"  # Two column
    COMPARISON_PROS_CONS = "comparisonProsCons"  # Green/red
    COMPARISON_BEFORE_AFTER = "comparisonBeforeAfter"  # Before → After

    # Quote variants
    QUOTE = "quote"  # Standard quote
    QUOTE_TESTIMONIAL = "quoteTestimonial"  # With author photo
    QUOTE_CITATION = "quoteCitation"  # Academic style

    # Other variants
    SOLID_BOXES_WITH_ICONS = "solidBoxesWithIconsInside"
    DEFINITION = "definition"  # Term + definition
    CODE_SNIPPET = "codeSnippet"  # Syntax highlighted
    CODE_COMPARISON = "codeComparison"  # Before/after code
    DIAGRAM_FLOWCHART = "diagramFlowchart"
    DIAGRAM_HIERARCHY = "diagramHierarchy"
    DIAGRAM_CYCLE = "diagramCycle"
    DIAGRAM_PYRAMID = "diagramPyramid"
    TABLE = "table"  # Standard table
    TABLE_STRIPED = "tableStriped"  # Alternating rows
    TABLE_HIGHLIGHT = "tableHighlight"  # With highlighted cells


class Intent(Enum):
    """
    Slide intent types.
    Expanded from llm_content_schema.md.
    """

    INTRODUCE = "introduce"  # Title, subtitle, prominent image
    EXPLAIN = "explain"  # Concepts, card_grid
    NARRATE = "narrate"  # Timeline, events
    COMPARE = "compare"  # Side-by-side comparison
    LIST = "list"  # Bullet/step list
    PROVE = "prove"  # Stats, evidence
    SUMMARIZE = "summarize"  # Key points, conclusion
    TEACH = "teach"  # Definition, code, diagrams
    DEMO = "demo"  # Code examples, workflows


class BlockType(Enum):
    """
    Canonical block types.
    Expanded from llm_content_schema.md.
    """

    # Text blocks
    HEADING = "heading"
    PARAGRAPH = "paragraph"

    # Primary content blocks (only one per slide)
    TIMELINE = "timeline"
    CARD_GRID = "card_grid"
    STATS = "stats"
    BULLET_LIST = "bullet_list"
    STEP_LIST = "step_list"
    COMPARISON = "comparison"
    QUOTE = "quote"
    DEFINITION = "definition"
    CODE = "code"
    DIAGRAM = "diagram"
    TABLE = "table"

    # Supporting blocks
    CALLOUT = "callout"
    TAKEAWAY = "takeaway"
    DIVIDER = "divider"
    IMAGE = "image"

    # Layout containers
    COLUMNS = "columns"
    SMART_LAYOUT = "smart_layout"


class SectionPurpose(Enum):
    """
    Section semantic purposes.
    From slide_engine.md §2.
    """

    TITLE = "title"
    INTRODUCTION = "introduction"
    CONTENT = "content"
    EXPLANATION = "explanation"
    COMPARISON = "comparison"
    SUMMARY = "summary"
    TAKEAWAY = "takeaway"


class Limits:
    """
    Implicit limits from slide_engine.md §6.
    These are non-negotiable constraints.
    """

    # Cognitive Load
    MAX_CONCEPTS_PER_SLIDE: int = 4
    IDEAL_CONCEPTS: Tuple[int, int] = (2, 3)

    # Text Density
    TEXT_SOFT_MAX: int = 300  # words
    TEXT_HARD_MAX: int = 400  # words

    # Visual Elements
    MAX_VISUAL_ELEMENTS: int = 5  # images, icons, callouts, diagrams combined

    # Structural Complexity
    MAX_LAYOUT_CONTAINERS: int = 3
    MAX_NESTING_DEPTH: int = 3

    # Block limits
    MAX_MAIN_CONTENT_BLOCKS: int = 3

    # List limits
    MAX_BULLET_ITEMS: int = 7
    MAX_TIMELINE_EVENTS: int = 6
    MAX_CARD_COUNT: int = 6

    @classmethod
    def is_word_count_exceeded(cls, count: int) -> bool:
        """Check if word count exceeds hard limit."""
        return count > cls.TEXT_HARD_MAX

    @classmethod
    def is_word_count_warned(cls, count: int) -> bool:
        """Check if word count exceeds soft limit."""
        return count > cls.TEXT_SOFT_MAX

    @classmethod
    def should_split_slide(
        cls,
        word_count: int,
        concept_count: int,
        visual_count: int,
        container_count: int,
        main_block_count: int,
    ) -> bool:
        """
        Determine if a slide should be split.
        From slide_engine.md §13.
        """
        return (
            word_count > cls.TEXT_HARD_MAX
            or concept_count > cls.MAX_CONCEPTS_PER_SLIDE
            or visual_count > cls.MAX_VISUAL_ELEMENTS
            or container_count > cls.MAX_LAYOUT_CONTAINERS
            or main_block_count > cls.MAX_MAIN_CONTENT_BLOCKS
        )


# Intent detection keywords - maps keywords to intents
# Updated for new intents from llm_content_schema.md
INTENT_KEYWORDS = {
    Intent.INTRODUCE: ["introduction", "welcome", "overview", "about"],
    Intent.EXPLAIN: ["what is", "how does", "why", "explain", "understand", "concept"],
    Intent.NARRATE: [
        "timeline",
        "history",
        "story",
        "journey",
        "evolution",
        "when",
        "over time",
    ],
    Intent.COMPARE: [
        "vs",
        "versus",
        "compare",
        "comparison",
        "difference",
        "similarities",
    ],
    Intent.LIST: ["list", "steps", "items", "points", "features", "benefits"],
    Intent.PROVE: ["evidence", "data", "statistics", "research", "study", "fact"],
    Intent.SUMMARIZE: ["summary", "key points", "recap", "in brief", "conclusion"],
    Intent.TEACH: ["definition", "meaning", "term", "code", "example", "tutorial"],
    Intent.DEMO: ["demo", "demonstration", "walkthrough", "example", "how to"],
}
