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

    h1: str = "2.8rem"
    h2: str = "2rem"
    h3: str = "1.625rem"
    h4: str = "1.25rem"
    body: str = "1.125rem"
    small: str = "1.125rem"
    card_number: str = "1.25rem"  # Size for numbers in lists/grids
    line_height_base: float = 1.65
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
                    h1="3.0rem",
                    h2="2.2rem",
                    body="1.25rem",
                    small="1.125rem",
                    line_height_base=1.55,
                ),
                spacing=SpacingProfile(
                    section_padding="1.5rem 2.25rem",
                    block_gap="1rem",
                    card_gap="0.75rem",
                    card_padding="1.125rem",
                ),
            )

        if name == "balanced":
            return VisualHierarchy(
                name="balanced",
                typography=TypographyScale(
                    h1="3.4rem",
                    h2="2.6rem",
                    body="1.4rem",
                    small="1.25rem",
                    card_number="1.75rem",
                    line_height_base=1.65,
                ),
                spacing=SpacingProfile(
                    section_padding="2.25rem 3.25rem",
                    block_gap="1.5rem",
                    card_gap="1rem",
                    card_padding="1.25rem",
                ),
            )

        if name == "impact":
            return VisualHierarchy(
                name="impact",
                typography=TypographyScale(
                    h1="4.0rem",
                    h2="3rem",
                    body="1.6rem",
                    small="1.4rem",
                    card_number="2.2rem",
                ),
                spacing=SpacingProfile(
                    section_padding="3.25rem 4rem 4rem 4rem",
                    block_gap="2.5rem",
                    card_padding="2rem",
                    card_gap="1.5rem",
                ),
            )

        if name == "super_dense":
            return VisualHierarchy(
                name="super_dense",
                typography=TypographyScale(
                    h1="2.6rem",
                    h2="1.8rem",
                    body="1.1rem",
                    small="1.0625rem",  # Used for card text
                    card_number="1.125rem",
                    line_height_base=1.45,
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
