"""
GyML Slide Fitness Gate
Enforces strict quality control on generated slides.
Rejects content that is too sparse, too dense, or breaks layout constraints.
Separated from validator.py (structural) to focus on content heuristics.
"""

from typing import List, Any, Tuple
from .definitions import ComposedSlide
from .constraints import ConstraintRules


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
        Based on word count, structural items, and image presence.
        """
        # 1. Word Utilization (250 words for 100% fill)
        word_utilization = slide.total_word_count() / 250

        # Structural Utilization Heuristics
        BLOCK_WEIGHTS = {
            "hierarchy_tree": 0.10,  # +0.02
            "numbered_list": 0.08,  # +0.02
            "labeled_diagram": 0.18,
            "table": 0.15,
            "split_panel": 0.25,
            "formula_block": 0.10,  # +0.04
            "code": 0.20,  # +0.05
            "card_grid": 0.12,
            "hub_and_spoke": 0.55,
        }
        ITEM_WEIGHTS = {
            "hierarchy_tree": 0.02,
            "numbered_list": 0.015,
            "card_grid": 0.015,
            "table": 0.01,
        }

        def get_block_weight(block: Any) -> float:
            """Recursive weight calculation for nested blocks."""
            weight = 0.0
            if block.type == "columns":
                # Sum weights of all nested blocks
                for col in block.content.get("columns", []):
                    for nested in col.get("blocks", []):
                        weight += get_block_weight(nested)
                return weight + 0.05  # Small container overhead

            # Base weight
            weight += BLOCK_WEIGHTS.get(block.type, 0.08)

            # Extra weight for internal items
            count = block.item_count()
            if count > 1:
                weight += count * ITEM_WEIGHTS.get(block.type, 0.03)
            return weight

        structural_score = 0
        for section in slide.sections:
            for block in section.blocks:
                structural_score += get_block_weight(block)

        # 3. Image Impact
        image_utilization = 0.35 if slide.accent_image_url else 0.0

        return word_utilization + structural_score + image_utilization

    @classmethod
    def validate_density(cls, slide: ComposedSlide) -> Tuple[bool, str]:
        """
        Check if slide meets minimum visual density requirements.
        Returns: (is_valid, reason)
        """
        height = cls._calculate_estimated_height(slide)

        # 1. CRITICAL FAILURE: Way too empty
        # Even with an image, < 40% is just a title and empty space.
        if height < 0.5:
            return (
                False,
                f"Slide too sparse (Density: {height:.2f}). Needs more content.",
            )

        # 2. SOFT FAILURE: Needs visual aid
        # If < 50% and no image, it's valid ONLY if we can inject an image later.
        if height < 0.6 and not slide.accent_image_url:
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
