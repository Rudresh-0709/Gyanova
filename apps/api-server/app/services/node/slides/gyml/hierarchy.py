"""
GyML Visual Hierarchy System

Defines whitespace, typography, and contrast rules that adapt
based on content density and intent.
"""

from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class TypographyScale:
    """Defines font sizes and line heights for a specific hierarchy level."""

    h1: str = "2.25rem"
    h2: str = "2rem"
    h3: str = "1.5rem"
    h4: str = "1.125rem"
    body: str = "1rem"
    small: str = "0.875rem"
    card_number: str = "1.125rem"  # Size for numbers in lists/grids
    line_height_base: float = 1.6
    line_height_heading: float = 1.2


@dataclass
class SpacingProfile:
    """Defines spacing variables for the slide."""

    section_padding: str = "3rem"
    block_gap: str = "1.5rem"
    heading_gap: Optional[str] = (
        None  # Specific gap after headers. If None, uses block_gap.
    )
    card_gap: str = "1.25rem"
    card_padding: str = "1.5rem"
    column_gap: str = "2rem"


@dataclass
class VisualHierarchy:
    """
    Combined visual rules for a slide.
    Assigned by Composer, consumed by Renderer.
    """

    name: str  # e.g. "default", "dense", "impact"
    typography: TypographyScale
    spacing: SpacingProfile

    # Optional logic hook for contrast - implemented implementation-side if needed
    # contrast_checker: Optional[Callable[[str, str], bool]] = None

    @staticmethod
    def get_profile(name: str) -> "VisualHierarchy":
        """Factory for standard profiles."""
        if name == "dense":
            return VisualHierarchy(
                name="dense",
                typography=TypographyScale(
                    h1="2.4rem", h2="2.15rem", body="1.25rem", line_height_base=1.5
                ),
                spacing=SpacingProfile(
                    section_padding="1.5rem 2.25rem",  # Further reduced
                    block_gap="1rem",
                    card_gap="0.75rem",
                    card_padding="1.125rem",
                ),
            )

        if name == "balanced":
            return VisualHierarchy(
                name="balanced",
                typography=TypographyScale(
                    h1="3.0rem",
                    h2="2.6rem",
                    body="1.5rem",
                    card_number="2rem",
                    line_height_base=1.6,
                ),
                spacing=SpacingProfile(
                    section_padding="2.25rem 3.25rem",  # Further reduced
                    block_gap="1.5rem",
                    card_gap="1rem",
                    card_padding="1.25rem",
                ),
            )

        if name == "impact":
            return VisualHierarchy(
                name="impact",
                typography=TypographyScale(
                    h1="3.5rem", h2="3rem", body="1.7rem", card_number="2.2rem"
                ),
                spacing=SpacingProfile(
                    section_padding="3.25rem 4rem 4rem 4rem",  # Further reduced
                    block_gap="2.5rem",
                    card_padding="2rem",
                    card_gap="1.5rem",
                ),
            )

        if name == "super_dense":
            return VisualHierarchy(
                name="super_dense",
                typography=TypographyScale(
                    h1="1.85rem",
                    h2="1.5rem",
                    body="0.875rem",
                    small="0.8125rem",  # Used for card text
                    card_number="1rem",
                    line_height_base=1.35,
                ),
                spacing=SpacingProfile(
                    section_padding="1.25rem 2rem",
                    block_gap="0.5rem",
                    heading_gap="0.25rem",
                    card_gap="0.5rem",
                    card_padding="0.75rem",
                ),
            )

        # Default Gamma Style
        return VisualHierarchy(
            name="default", typography=TypographyScale(), spacing=SpacingProfile()
        )
