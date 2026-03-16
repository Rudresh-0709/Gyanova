"""
GyML Type Definitions

Two distinct type families:
1. Composer IR (Intermediate Representation) - GyML-agnostic
2. GyML Node Types - Exact spec representation
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Union, Literal
from enum import Enum

from .hierarchy import VisualHierarchy
from .constants import BlockType


# =============================================================================
# COMPOSER IR TYPES (GyML-Agnostic)
# =============================================================================


class Emphasis(Enum):
    """Emphasis levels for slide elements."""

    PRIMARY = "primary"  # Heading or dominant visual
    SECONDARY = "secondary"  # Supporting blocks
    TERTIARY = "tertiary"  # Details, examples, callouts


@dataclass
class ComposedBlock:
    """
    A single block in the composed slide.
    Format-agnostic - can serialize to any output format.
    """

    type: str  # BlockType value as string
    content: Dict[str, Any]
    emphasis: Emphasis = Emphasis.SECONDARY
    role: Optional[str] = None  # Semantic role (e.g., CodeRole.PRIMARY)

    def word_count(self) -> int:
        """Count words in this block's text content."""
        # 1. Recursive check for Columns
        if self.type == "columns" and "columns" in self.content:
            total = 0
            for col in self.content["columns"]:
                for block in col.get("blocks", []):
                    if hasattr(block, "word_count"):
                        total += block.word_count()
                    elif isinstance(block, dict):
                        # Basic estimation for dict-based blocks if needed
                        text = " ".join(
                            str(v) for v in block.values() if isinstance(v, str)
                        )
                        total += len(text.split())
            return total

        # 2. Standard block counting
        text_parts = []
        if "text" in self.content:
            text_parts.append(str(self.content["text"]))

        # Handle Hierarchy Tree recursive labels
        if self.type == "hierarchy_tree" and "root" in self.content:

            def collect_labels(node):
                text = [node.get("label", "")]
                for child in node.get("children", []):
                    text.extend(collect_labels(child))
                return text

            text_parts.extend(collect_labels(self.content["root"]))

        # Handle List/Grid items
        items = self.content.get("items") or self.content.get("cards")
        if items:
            for item in items:
                if isinstance(item, dict):
                    text_parts.extend(str(v) for v in item.values() if v)
                else:
                    text_parts.append(str(item))

        full_text = " ".join(text_parts)
        return len(full_text.split()) if full_text else 0

    def item_count(self) -> int:
        """Return number of structural items (points, cards, etc.)."""
        # 1. Recursive check for Columns
        if self.type == "columns" and "columns" in self.content:
            count = 0
            for col in self.content["columns"]:
                for block in col.get("blocks", []):
                    if hasattr(block, "item_count"):
                        count += block.item_count()
                    elif isinstance(block, dict):
                        count += 1
            return max(count, 1)

        # 2. Standard block item counting
        if "items" in self.content:
            return len(self.content["items"])
        if "cards" in self.content:
            return len(self.content["cards"])

        # Recursive node counting for Hierarchy Trees
        if self.type == "hierarchy_tree" and "root" in self.content:

            def count_nodes(node):
                count = 1
                for child in node.get("children", []):
                    count += count_nodes(child)
                return count

            return count_nodes(self.content["root"])

        return 1  # Standard blocks count as 1 item


@dataclass
class ComposedSection:
    """
    A semantic section in the composed slide.
    Represents intent and relationship, not layout.
    """

    purpose: str  # "introduction", "content", "takeaway", etc.
    relationship: str = "flow"  # Relationship value
    primary_block: Optional[ComposedBlock] = None
    secondary_blocks: List[ComposedBlock] = field(default_factory=list)

    @property
    def blocks(self) -> List[ComposedBlock]:
        """Backward compatibility: return all blocks in order."""
        all_blocks = []
        if self.primary_block:
            all_blocks.append(self.primary_block)
        all_blocks.extend(self.secondary_blocks)
        return all_blocks


@dataclass
class ComposedSlide:
    """
    Output of the composer - format-agnostic intermediate representation.
    Can be serialized to GyML, JSON, or any other format.
    """

    id: str
    intent: str  # Intent value as string
    sections: List[ComposedSection] = field(default_factory=list)

    # Optional metadata
    accent_image_url: Optional[str] = None
    accent_image_alt: Optional[str] = None
    image_layout: str = "blank"  # ImageLayout value
    index: int = 0  # Slide index
    topic: Optional[str] = None
    image_prompt: Optional[str] = None
    image_style: Optional[str] = None
    slide_density: Optional[str] = None
    image_role: Optional[str] = None  # "content", "accent", or "none"

    # Visual Hierarchy Rules (Assigned by Composer)
    hierarchy: Optional[VisualHierarchy] = None

    def total_word_count(self) -> int:
        """Calculate total word count across all sections."""
        return sum(
            block.word_count() for section in self.sections for block in section.blocks
        )

    def block_count(self) -> int:
        """Count total top-level blocks."""
        return sum(len(section.blocks) for section in self.sections)

    def structural_count(self) -> int:
        """Count total structural units (items within blocks)."""
        return sum(
            block.item_count() for section in self.sections for block in section.blocks
        )

    def get_primary_emphasis_block(self) -> Optional[ComposedBlock]:
        """Find the block with primary emphasis."""
        for section in self.sections:
            if (
                section.primary_block
                and section.primary_block.emphasis == Emphasis.PRIMARY
            ):
                return section.primary_block
            for block in section.secondary_blocks:
                if block.emphasis == Emphasis.PRIMARY:
                    return block
        return None


# =============================================================================
# GYML NODE TYPES (Spec-Compliant)
# =============================================================================


@dataclass
class GyMLCyclicItem:
    """Item for CyclicBlock."""

    label: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None


@dataclass
class GyMLCyclicBlock:
    """
    Cyclic visualization element.
    """

    items: List[GyMLCyclicItem]
    hub_label: Optional[str] = None
    variant: str = "chevron"
    type: str = BlockType.CYCLIC_BLOCK


@dataclass
class GyMLProcessArrowItem:
    """Item for horizontal interlocking process arrow."""

    label: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    color: Optional[str] = None


@dataclass
class GyMLProcessArrowBlock:
    """
    Horizontal process visualization with interlocking arrows
    and images above each step.
    """

    items: List[GyMLProcessArrowItem]
    type: str = BlockType.PROCESS_ARROW_BLOCK
    variant: str = "default"


@dataclass
class GyMLCyclicProcessItem:
    label: str
    description: Optional[str] = None
    image_url: Optional[str] = None


@dataclass
class GyMLCyclicProcessBlock:
    items: List[GyMLCyclicProcessItem]
    type: str = BlockType.CYCLIC_PROCESS_BLOCK


GyMLNode = Union[
    "GyMLHeading",
    "GyMLParagraph",
    "GyMLColumns",
    "GyMLSmartLayout",
    "GyMLImage",
    "GyMLDivider",
    "GyMLTable",
    "GyMLCode",
    "GyMLComparisonTable",
    "GyMLKeyValueList",
    "GyMLRichText",
    "GyMLNumberedList",
    "GyMLLabeledDiagram",
    "GyMLHierarchyTree",
    "GyMLSplitPanel",
    "GyMLFormulaBlock",
    "GyMLHubAndSpoke",
    "GyMLCyclicBlock",
    "GyMLProcessArrowBlock",
    "GyMLSequentialOutput",
    "GyMLCyclicProcessBlock",
    "GyMLFeatureShowcaseBlock",
]


@dataclass
class GyMLIcon:
    """Icon element inside smart-layout-item."""

    alt: str  # Icon identifier (e.g., "atom", "ri-check-line")


@dataclass
class GyMLHeading:
    """Text heading element (h1-h4)."""

    level: int  # 1-4
    text: str

    def __post_init__(self):
        if not 1 <= self.level <= 4:
            raise ValueError(f"Heading level must be 1-4, got {self.level}")


@dataclass
class GyMLParagraph:
    """Paragraph text element."""

    text: str
    variant: Optional[str] = None  # semantic type (e.g., "caption", "intro")


@dataclass
class GyMLImage:
    """Image element - can be accent or inline."""

    src: str
    alt: str = ""
    is_accent: bool = False  # True if accent image (sibling of body)


@dataclass
class GyMLDivider:
    """Horizontal divider element."""

    pass


@dataclass
class GyMLSmartLayoutItem:
    """
    Item inside a smart-layout.
    Contains icon and content div.
    """

    icon: Optional[GyMLIcon] = None
    heading: Optional[str] = None
    description: Optional[str] = None
    points: Optional[List[str]] = None

    # For timeline variant
    year: Optional[str] = None

    # For stats variant
    value: Optional[str] = None
    label: Optional[str] = None


@dataclass
class GyMLSmartLayout:
    """
    Smart layout container - grid-based structural pattern.

    From gyanova_markup_language.md §8:
    - Explicit tag, not inferred
    - variant encodes semantic intent
    - Items are equal peers
    - Renderer decides grid structure
    """

    variant: str  # SmartLayoutVariant value
    items: List[GyMLSmartLayoutItem] = field(default_factory=list)
    cellsize: int = 15  # Cell size hint for renderer


@dataclass
class LayoutConstraints:
    """Constraints for a specific smart layout variant."""

    min_items: int = 1
    max_items: int = 6
    max_words_per_item: int = 100
    requires_image: bool = False
    min_density_score: float = 0.3


@dataclass
class GyMLColumnDiv:
    """A single column container."""

    children: List[GyMLNode] = field(default_factory=list)


@dataclass
class GyMLColumns:
    """
    Columns layout container - flex-based parallel layout.

    From gyanova_markup_language.md §7:
    - Creates horizontal layout
    - colwidths is a hard constraint
    - Children must be div (GyMLColumnDiv)
    - On mobile, columns stack vertically
    """

    colwidths: List[int]  # e.g., [50, 50] or [60, 40]
    columns: List[GyMLColumnDiv] = field(default_factory=list)

    def __post_init__(self):
        if len(self.colwidths) != len(self.columns):
            # Allow empty columns to be filled later
            if len(self.columns) == 0:
                self.columns = [GyMLColumnDiv() for _ in self.colwidths]


@dataclass
class GyMLBody:
    """
    Body container - exactly one per section.

    From gyanova_markup_language.md §4:
    - Everything visible (except accent images) lives inside body
    - Body is a vertical flow container
    """

    children: List[GyMLNode] = field(default_factory=list)


@dataclass
class GyMLSection:
    """
    Section element - the atomic slide unit.

    From gyanova_markup_language.md §3:
    - Sections stack vertically
    - Sections have no awareness of neighboring slides
    - Slides expand/shrink based on content
    - Slides are portable and reorderable
    """

    id: str
    image_layout: Literal["right", "left", "top", "bottom", "behind", "blank"] = "blank"
    accent_image: Optional[GyMLImage] = None
    image_style: Optional[str] = None
    slide_density: Optional[str] = None
    body: GyMLBody = field(default_factory=GyMLBody)

    # Hierarchy Profile - passed from Composer
    hierarchy: Optional[VisualHierarchy] = None

    # Optional annotation relocated below the accent image on dense slides
    image_caption: Optional[GyMLParagraph] = None

    def __post_init__(self):
        # Ensure body exists
        if self.body is None:
            self.body = GyMLBody()  # Fixed indentation and method definition


@dataclass
class GyMLCode:
    """Code block element."""

    code: str
    language: str = "text"
    variant: str = "snippet"  # snippet, comparison


@dataclass
class GyMLTable:
    """Table element."""

    headers: List[str]
    rows: List[List[str]]
    variant: str = "simple"  # simple, striped, highlight


@dataclass
class GyMLComparisonTable:
    """Comparison table element."""

    headers: List[str]
    rows: List[List[str]]
    caption: Optional[str] = None


@dataclass
class GyMLKeyValueItem:
    """Item for Key-Value List."""

    key: str
    value: str


@dataclass
class GyMLKeyValueList:
    """Key-Value list element."""

    items: List[GyMLKeyValueItem]


@dataclass
class GyMLRichText:
    """Rich text element with multiple paragraphs."""

    paragraphs: List[str]


@dataclass
class GyMLNumberedListItem:
    """Item for Numbered List."""

    title: str
    description: str


@dataclass
class GyMLNumberedList:
    """Numbered sequence element."""

    items: List[GyMLNumberedListItem]


@dataclass
class GyMLDiagramLabel:
    """Label for Labeled Diagram."""

    text: str
    x: float
    y: float


@dataclass
class GyMLLabeledDiagram:
    """Diagram with positioned labels."""

    image_url: Optional[str]
    labels: List[GyMLDiagramLabel]


@dataclass
class GyMLTreeNode:
    """Node for Hierarchy Tree."""

    label: str
    children: List[GyMLTreeNode] = field(default_factory=list)


@dataclass
class GyMLHierarchyTree:
    """Tree structure element."""

    root: GyMLTreeNode


@dataclass
class GyMLPanel:
    """Panel for Split Panel."""

    title: str
    content: str


@dataclass
class GyMLSplitPanel:
    """Two-panel independent content element."""

    left_panel: GyMLPanel
    right_panel: GyMLPanel


@dataclass
class GyMLFormulaVariable:
    """Variable definition for Formula Block."""

    name: str
    definition: str


@dataclass
class GyMLFormulaBlock:
    """Mathematical expression element."""

    expression: str
    variables: List[GyMLFormulaVariable] = field(default_factory=list)
    example: Optional[str] = None


@dataclass
class GyMLHubAndSpokeItem:
    """Item for Hub and Spoke layout."""

    label: str
    description: Optional[str] = None
    color: Optional[str] = None  # CSS color override
    icon: Optional[str] = None  # RemixIcon class


@dataclass
class GyMLHubAndSpoke:
    """
    Hub and Spoke visualization element.
    High density, circular arrangement of hexagon-style nodes.
    """

    hub_label: str
    items: List[GyMLHubAndSpokeItem]
    variant: str = "hexagon"


@dataclass
class GyMLSequentialOutput:
    """Sequential output block."""

    items: List[str]
    type: str = BlockType.SEQUENTIAL_OUTPUT


@dataclass
class GyMLFeatureShowcaseItem:
    """Item for Feature Showcase layout."""

    label: str
    description: Optional[str] = None
    icon: Optional[str] = None  # RemixIcon class (e.g. "settings", "shield-check")
    color: Optional[str] = None  # CSS color


@dataclass
class GyMLFeatureShowcaseBlock:
    """
    Feature Showcase visualization element.
    Central image flanked by sub-features with Remix Icons.
    Used for features, limitations, roles & responsibilities, etc.
    """

    title: str  # Central label (shown beneath the image)
    items: List[GyMLFeatureShowcaseItem]
    image_url: Optional[str] = None  # Leonardo-generated image URL
    image_prompt: Optional[str] = None  # Prompt for image generation
    type: str = BlockType.FEATURE_SHOWCASE_BLOCK
