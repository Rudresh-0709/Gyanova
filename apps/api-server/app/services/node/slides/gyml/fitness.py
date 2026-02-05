"""
GyML Slide Fitness Gate
Enforces strict quality control on generated slides.
Rejects content that is too sparse, too dense, or breaks layout constraints.
Separated from validator.py (structural) to focus on content heuristics.
"""

from typing import List, Any, Tuple
from gyml.definitions import ComposedSlide
from gyml.constraints import ConstraintRules


class FitnessException(Exception):
    """Raised when a slide fails fitness checks."""

    pass


class SlideFitnessGate:
    """
    Gatekeeper for slide quality.
    "If it doesn't fit, it doesn't ship."
    """

    @staticmethod
    def _calculate_estimated_height(slide: ComposedSlide) -> float:
        """
        Estimate content height percentage (0.0 - 1.0+).
        Based on word count, block count, and image presence.
        """
        # Base capacity: ~180 words fills a slide
        word_utilization = slide.total_word_count() / ConstraintRules.MAX_SLIDE_WORDS

        # Block overhead (padding/margins)
        block_utilization = slide.block_count() * 0.1

        # Image impact
        image_utilization = 0.4 if slide.accent_image_url else 0.0

        return min(word_utilization + block_utilization + image_utilization, 1.2)

    @classmethod
    def validate_density(cls, slide: ComposedSlide) -> Tuple[bool, str]:
        """
        Check if slide meets minimum visual density requirements.
        Returns: (is_valid, reason)
        """
        height = cls._calculate_estimated_height(slide)

        # 1. CRITICAL FAILURE: Way too empty
        # Even with an image, < 30% is just a title and empty space.
        if height < 0.25:  # Slightly lenient for very succinct slides
            return (
                False,
                f"Slide too sparse (Density: {height:.2f}). Needs more content.",
            )

        # 2. SOFT FAILURE: Needs visual aid
        # If < 50% and no image, it's valid ONLY if we can inject an image later.
        if height < 0.5 and not slide.accent_image_url:
            return True, "Sparse but salvageable with image injection."

        return True, "Density OK"

    @classmethod
    def validate_constraints(
        cls, slide: ComposedSlide, layout_name: str, items: List[Any]
    ) -> None:
        """
        Validate content against specific Smart Layout constraints.
        Raises FitnessException if invalid.
        """
        limits = ConstraintRules.get_limits(layout_name)

        # Check Item Count
        count = len(items)
        if count < limits.min_items:
            raise FitnessException(
                f"Layout '{layout_name}' requires min {limits.min_items} items, got {count}."
            )
        if count > limits.max_items:
            raise FitnessException(
                f"Layout '{layout_name}' supports max {limits.max_items} items, got {count}."
            )

        # Check Word Counts per Item
        for i, item in enumerate(items):
            # rudimentary word count for dict or string
            text = str(item)
            if isinstance(item, dict):
                text = " ".join(str(v) for v in item.values())

            wc = len(text.split())
            if limits.max_words_per_item > 0 and wc > limits.max_words_per_item:
                raise FitnessException(
                    f"Item {i+1} exceeds word limit for '{layout_name}' "
                    f"({wc} > {limits.max_words_per_item})."
                )
