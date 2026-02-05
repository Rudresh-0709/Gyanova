"""
GyML (Gyanova Markup Language) Slide Engine

A deterministic slide generation pipeline:
    Content → Composer → IR → Serializer → GyML → Validator → Renderer → HTML

Public API:
    - SlideComposer: Compose slides from content (GyML-agnostic)
    - GyMLSerializer: Serialize IR to GyML format
    - GyMLValidator: Validate GyML structure
    - GyMLRenderer: Passively render GyML to HTML
    - Theme, THEMES: Theme configuration
"""

from .definitions import (
    # Composer IR types
    ComposedSlide,
    ComposedSection,
    ComposedBlock,
    Emphasis,
    # GyML node types
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
)

from .constants import (
    ImageLayout,
    SmartLayoutVariant,
    Intent,
    BlockType,
    Limits,
)

from .rules import (
    BLOCK_ORDER_GRAMMAR,
    NESTING_RULES,
    NESTING_FORBIDDEN,
    VarietyRules,
)

from .composer import SlideComposer
from .serializer import GyMLSerializer
from .validator import GyMLValidator, ValidationResult
from .renderer import GyMLRenderer
from .theme import Theme, THEMES, get_theme

__all__ = [
    # Composer
    "SlideComposer",
    # Serializer
    "GyMLSerializer",
    # Validator
    "GyMLValidator",
    "ValidationResult",
    # Renderer
    "GyMLRenderer",
    # Types
    "ComposedSlide",
    "ComposedSection",
    "ComposedBlock",
    "Emphasis",
    "GyMLSection",
    "GyMLBody",
    "GyMLHeading",
    "GyMLParagraph",
    "GyMLColumns",
    "GyMLColumnDiv",
    "GyMLSmartLayout",
    "GyMLSmartLayoutItem",
    "GyMLImage",
    "GyMLIcon",
    # Constants
    "ImageLayout",
    "SmartLayoutVariant",
    "Intent",
    "BlockType",
    "Limits",
    # Rules
    "BLOCK_ORDER_GRAMMAR",
    "NESTING_RULES",
    "NESTING_FORBIDDEN",
    "VarietyRules",
    # Theme
    "Theme",
    "THEMES",
    "get_theme",
]
