"""
GyML Responsive Behavior System

Defines constraints for responsive behavior, allowing programmable generation
of media queries and layout adaptations.
"""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class ResponsiveConstraints:
    """
    Defines how the slide should behave at different viewports.
    Used by the Renderer to generate @media queries.
    """

    # Breakpoints (max-width in px)
    # e.g., {'mobile': 480, 'tablet': 768, 'desktop': 1024}
    breakpoints: Dict[str, int] = field(
        default_factory=lambda: {"mobile": 480, "tablet": 768, "desktop": 1024}
    )

    # Layout Fallbacks
    # Maps specific layout constructs to their mobile/fallback behavior
    # e.g. {'columns': 'stack'}
    layout_fallbacks: Dict[str, str] = field(
        default_factory=lambda: {
            "columns": "stack",
            "image_layout": "stack",  # right/left becomes top
        }
    )

    # Viewport Padding
    # Maps breakpoint names to padding values
    viewport_padding: Dict[str, str] = field(
        default_factory=lambda: {
            "mobile": "1rem",
            "tablet": "2rem",
            "default": "3rem",  # Desktop/Default
        }
    )

    # Typography Scaling Factors
    # Scale base font size relative to default at breakpoints
    typography_scale: Dict[str, float] = field(
        default_factory=lambda: {"mobile": 0.85, "tablet": 0.9, "default": 1.0}
    )

    @staticmethod
    def default() -> "ResponsiveConstraints":
        """Standard Gamma-style responsive behaviors."""
        return ResponsiveConstraints()
