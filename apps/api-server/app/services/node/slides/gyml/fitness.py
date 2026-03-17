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
        total_words = slide.total_word_count()
        word_utilization = total_words / 250

        # Structural Utilization Heuristics
        BLOCK_WEIGHTS = {
            "hierarchy_tree": 0.10,
            "numbered_list": 0.08,
            "labeled_diagram": 0.18,
            "table": 0.15,
            "split_panel": 0.25,
            "formula_block": 0.10,
            "code": 0.20,
            "card_grid": 0.12,
            "smart_layout": 0.15,  
            "diagram": 0.25,       
            "hub_and_spoke": 0.55,
            "process_arrow_block": 0.30,
            "cyclic_process_block": 0.35,
            "feature_showcase_block": 0.30,
            "comparison_table": 0.20,
            "key_value_list": 0.12,
        }
        
        BASE_ITEM_WEIGHT = {
            "hierarchy_tree": 0.02,
            "numbered_list": 0.015,
            "card_grid": 0.015,
            "table": 0.01,
            "comparison_table": 0.02,
            "key_value_list": 0.015,
            "process_arrow_block": 0.03,
            "cyclic_process_block": 0.03,
            "feature_showcase_block": 0.02,
        }

        def get_block_weight(block: Any) -> float:
            """Recursive weight calculation for nested blocks."""
            weight = 0.0
            
            # Extract block type and content safely
            if isinstance(block, dict):
                # Raw JSON dictionary - check this first to avoid dict-as-object attribute errors
                b_type = block.get("type", "paragraph")
                b_content = block.get("content", block)
                # Rudimentary counts for dicts
                items = b_content.get("items") or b_content.get("cards") or b_content.get("steps") or b_content.get("events", [])
                b_item_count = len(items) if isinstance(items, list) else 1
                b_word_count = len(str(b_content).split()) # Very rough fallback
            elif hasattr(block, "type"):
                # ComposedBlock or GyML (some nodes have type)
                b_type = getattr(block, "type")
                b_content = getattr(block, "content", {})
                b_item_count = getattr(block, "item_count", lambda: 0)() if callable(getattr(block, "item_count", None)) else 0
                b_word_count = getattr(block, "word_count", lambda: 0)() if callable(getattr(block, "word_count", None)) else 0
            else:
                # Fallback for GyML nodes without .type (like GyMLHeading)
                # Identify by class name or assume neutral weight
                name = type(block).__name__.lower()
                if "heading" in name: b_type = "heading"
                elif "paragraph" in name: b_type = "paragraph"
                elif "image" in name: b_type = "image"
                else: b_type = "unknown"
                b_content = {}
                b_item_count = 0
                b_word_count = 0

            # 1. Recursive check for Columns
            if b_type == "columns":
                # Sum weights of all nested blocks
                cols = b_content.get("columns", []) if isinstance(b_content, dict) else []
                for col in cols:
                    for nested in col.get("blocks", []):
                        weight += get_block_weight(nested)
                return weight + 0.05  # Small container overhead

            # 2. Base weight
            # Enums might have been passed as values
            b_type_val = b_type.value if hasattr(b_type, "value") else str(b_type)
            weight += BLOCK_WEIGHTS.get(b_type_val, 0.08)

            # 3. Special variant bonuses for smart_layout
            if b_type_val == "smart_layout":
                variant = str(b_content.get("variant", "")).lower() if isinstance(b_content, dict) else ""
                if "diagram" in variant or "flowchart" in variant or "process" in variant:
                    weight += 0.10  # Diagrams/Flowcharts/Processes are vertically thirsty

            # 4. Extra weight for internal items with diminishing returns
            count = b_item_count
            if count > 1:
                # Calculate text density factor (avg words per item)
                words_per_item = max(1, b_word_count) / max(1, count)
                # 10 words is base, 50 words is 2x taller
                text_density_factor = min(2.0, max(1.0, words_per_item / 20.0))
                
                base_item_wt = BASE_ITEM_WEIGHT.get(b_type_val, 0.02) * text_density_factor
                
                # Diminishing returns scaling
                for i in range(1, count):
                    if i < 3:
                        weight += base_item_wt        # 1-3: full weight
                    elif i < 6:
                        weight += base_item_wt * 0.7  # 4-6: 70% weight
                    else:
                        weight += base_item_wt * 0.4  # 7+: 40% weight
                        
            return weight

        structural_score = 0
        for section in slide.sections:
            for block in section.blocks:
                structural_score += get_block_weight(block)

        # 3. Image Impact (Layout-aware)
        image_utilization = 0.0
        if slide.accent_image_url or getattr(slide, "image_role", "") == "content":
            layout = getattr(slide, "image_layout", "blank")
            if layout == "behind":
                image_utilization = 0.0  # Background doesn't take vertical space
            elif layout in ["top", "bottom"]:
                image_utilization = 0.25 # Full width block pushes text down significantly
            elif layout in ["left", "right"]:
                image_utilization = 0.15 # Split columns restrict width, implicitly pushing heights down
            else:
                image_utilization = 0.35 # Fallback

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
