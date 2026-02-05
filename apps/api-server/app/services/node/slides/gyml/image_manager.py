"""
GyML Image Manager
Handles decision logic for image placement and necessity.
Decoupled from Composer to allow stricter validation rules.
"""

from dataclasses import dataclass
from typing import Optional, Literal
from gyml.definitions import ComposedSlide, GyMLImage

# Placement Types
ImagePlacementValue = Literal["right", "left", "top", "behind", "blank"]


class ImageManager:
    """
    Determines if a slide NEEDS an image, and where it should go.
    Does NOT generate images (Composer does that via tools), only decides placement.
    """

    @staticmethod
    def determine_placement(
        slide_density: float, has_user_image: bool, intent: str
    ) -> ImagePlacementValue:
        """
        Decide image layout based on density and intent.

        Rules:
        - Density < 0.5: REQUIRE image (Right or Top) to fill space.
        - Density > 0.8: AVOID large images (use 'top' or 'blank').
        - User provided image: Always respect it, optimize placement.
        """

        # 1. High Density (Avoid cramping)
        if slide_density > 0.8:
            return "top" if has_user_image else "blank"

        # 2. Low Density (Fill void)
        if slide_density < 0.5:
            # Default to split for balance
            return "right"

        # 3. Medium Density
        # If user has image, use right/left. If not, maybe blank is fine.
        if has_user_image:
            return "right"

        return "blank"

    @staticmethod
    def should_inject_placeholder(slide_density: float, has_image: bool) -> bool:
        """
        Return True if we MUST inject a placeholder to save the slide layout.
        """
        # Strict Rule: If < 50% filled and no image, slide looks broken.
        return slide_density < 0.5 and not has_image

    @staticmethod
    def get_placeholder_image() -> GyMLImage:
        """Return the standard placeholder definition."""
        return GyMLImage(
            src="placeholder", alt="Decorative background placeholder", is_accent=True
        )
