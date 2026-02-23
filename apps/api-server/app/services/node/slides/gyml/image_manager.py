"""
GyML Image Manager
Handles decision logic for image placement and necessity.
Decoupled from Composer to allow stricter validation rules.
"""

from dataclasses import dataclass
from typing import Optional, Literal
from .definitions import ComposedSlide, GyMLImage

# Placement Types
ImagePlacementValue = Literal["right", "left", "top", "behind", "blank"]


class ImageManager:
    """
    Determines if a slide NEEDS an image, and where it should go.
    Does NOT generate images (Composer does that via tools), only decides placement.
    """

    @staticmethod
    def determine_placement(
        slide_density: float,
        has_user_image: bool,
        intent: str,
        explicit_layout: Optional[ImagePlacementValue] = None,
        slide_index: int = 0,
    ) -> ImagePlacementValue:
        """
        Decide image layout based on density, intent, and explicit orientation.

        Rules:
        - If explicit_layout is provided, PRIORITIZE it (unless blank).
        - Density < 0.5: REQUIRE image (Right or Left) to fill space.
        - Density > 0.8: AVOID large images (use 'top' or 'blank').
        - Fallback: Alternate between 'left' and 'right' based on slide_index.
        """
        # 1. Respect Explicit Layout from LLM/Teacher
        if explicit_layout and explicit_layout != "blank":
            return explicit_layout

        # 2. High Density (Avoid cramping)
        # Relaxed threshold to 1.1 to account for larger font sizes in profiles
        if slide_density > 1.1:
            # Respect user image but keep it right aligned if dense
            if has_user_image:
                return "right"
            return "blank"

        # 3. Low & Medium Density - Alternate for Variety
        # Logic: Odd slides = left, Even slides = right
        if slide_index % 2 == 1:
            return "left"

        return "right"

    @staticmethod
    def should_inject_placeholder(slide_density: float, has_image: bool) -> bool:
        """
        Return True if we MUST inject a placeholder to save the slide layout.
        """
        # Strict Rule: If < 110% filled and no image, slide looks broken.
        # Updated to 1.1 to match determine_placement change.
        return slide_density < 1.1 and not has_image

    @staticmethod
    def get_placeholder_image() -> GyMLImage:
        """Return the standard placeholder definition."""
        return GyMLImage(
            src="placeholder", alt="Decorative background placeholder", is_accent=True
        )
