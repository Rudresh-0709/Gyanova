"""
GyML Responsive Constraints & Rules
Defines the authoritative limits for layout validation and responsive behavior.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class Breakpoint:
    width: int
    name: str


class Breakpoints:
    MOBILE = Breakpoint(480, "mobile")
    TABLET = Breakpoint(768, "tablet")
    DESKTOP = Breakpoint(1024, "desktop")


@dataclass
class LayoutLimits:
    min_items: int = 1
    max_items: int = 6
    min_words_per_item: int = 0
    max_words_per_item: int = 100
    requires_image: bool = False

    # "Hard" limits (Fitness Gate Failure)
    min_density_score: float = 0.4  # Reject if below this
    max_density_score: float = 1.5  # Reject if above this


class ConstraintRules:
    """
    Singleton-like definition of constraints per Smart Layout variant.
    Used by Validator and Composer.
    """

    # Global Limits
    MAX_SLIDE_WORDS = 180
    MIN_SLIDE_WORDS = 20

    LAYOUTS: Dict[str, LayoutLimits] = {
        "timeline": LayoutLimits(
            min_items=2,
            max_items=12,  # Increased to allow splitting (will auto-paginate)
            max_words_per_item=40,
            min_density_score=0.25,
        ),
        "comparison": LayoutLimits(min_items=2, max_items=3, max_words_per_item=60),
        "stats": LayoutLimits(
            min_items=2,
            max_items=4,
            max_words_per_item=15,
        ),
        "processSteps": LayoutLimits(min_items=3, max_items=12, max_words_per_item=50),
        "bigBullets": LayoutLimits(min_items=1, max_items=8, max_words_per_item=30),
        "cardGrid": LayoutLimits(min_items=2, max_items=12, max_words_per_item=25),
        "solidBoxesWithIconsInside": LayoutLimits(
            min_items=2, max_items=4, max_words_per_item=20
        ),
        "hub_and_spoke": LayoutLimits(min_items=4, max_items=6, max_words_per_item=80),
    }

    @classmethod
    def get_limits(cls, layout_variant: str) -> LayoutLimits:
        """Get constraints for a specific layout variant."""
        return cls.LAYOUTS.get(layout_variant, LayoutLimits())
