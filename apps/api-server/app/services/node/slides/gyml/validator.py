"""
GyML Validator

Validate GyML structure against spec rules.
Ensures all nesting and hierarchy constraints are met before rendering.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Set

from .types import (
    GyMLSection,
    GyMLBody,
    GyMLHeading,
    GyMLParagraph,
    GyMLColumns,
    GyMLColumnDiv,
    GyMLSmartLayout,
    GyMLSmartLayoutItem,
    GyMLImage,
    GyMLDivider,
    GyMLNode,
)
from .rules import (
    NESTING_RULES,
    NESTING_FORBIDDEN,
    MAX_RECOMMENDED_DEPTH,
    is_nesting_allowed,
    is_nesting_forbidden,
)


@dataclass
class ValidationResult:
    """Result of GyML validation."""

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add_error(self, message: str):
        """Add an error and mark as invalid."""
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str):
        """Add a warning (doesn't affect validity)."""
        self.warnings.append(message)

    def merge(self, other: "ValidationResult"):
        """Merge another validation result into this one."""
        if not other.is_valid:
            self.is_valid = False
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)


class GyMLValidator:
    """
    Validate GyML structure against spec rules.

    Checks (from gyanova_markup_language.md):
    - Hierarchy constraints (§5)
    - Nesting rules (§11)
    - Required elements (exactly one body per section)
    - Depth limits
    """

    def validate(self, section: GyMLSection) -> ValidationResult:
        """
        Validate a GyML section.

        Args:
            section: GyMLSection to validate

        Returns:
            ValidationResult with errors and warnings
        """
        result = ValidationResult(is_valid=True)

        # Check: section has exactly one body
        self._validate_section_structure(section, result)

        # Check: body contains valid children
        if section.body:
            self._validate_body(section.body, result)

        # Check: accent image is sibling of body (structural position)
        self._validate_accent_image(section, result)

        # Check: overall nesting depth
        depth = self._calculate_depth(section)
        if depth > MAX_RECOMMENDED_DEPTH:
            result.add_warning(
                f"Nesting depth {depth} exceeds recommended {MAX_RECOMMENDED_DEPTH}"
            )

        return result

    def validate_many(self, sections: List[GyMLSection]) -> ValidationResult:
        """Validate multiple sections."""
        combined = ValidationResult(is_valid=True)

        for i, section in enumerate(sections):
            result = self.validate(section)

            # Prefix errors with section index
            for error in result.errors:
                combined.add_error(f"Section {i} ({section.id}): {error}")

            for warning in result.warnings:
                combined.add_warning(f"Section {i} ({section.id}): {warning}")

        return combined

    # =========================================================================
    # SECTION VALIDATION
    # =========================================================================

    def _validate_section_structure(
        self, section: GyMLSection, result: ValidationResult
    ):
        """
        Validate section structure.
        From gyanova_markup_language.md §3-4.
        """
        # Check: exactly one body per section
        if section.body is None:
            result.add_error("Section must have exactly one body")

        # Check: valid image layout
        valid_layouts = ["right", "left", "top", "behind", "blank"]
        if section.image_layout not in valid_layouts:
            result.add_error(
                f"Invalid image-layout '{section.image_layout}', "
                f"must be one of {valid_layouts}"
            )

        # Check: section ID is present
        if not section.id:
            result.add_warning("Section missing ID")

    def _validate_accent_image(self, section: GyMLSection, result: ValidationResult):
        """
        Validate accent image positioning.
        From gyanova_markup_language.md §9.1.
        """
        if section.accent_image:
            # Accent image should be marked as accent
            if not section.accent_image.is_accent:
                result.add_warning("Accent image should have is_accent=True")

            # If image layout is 'blank', no accent image expected
            if section.image_layout == "blank":
                result.add_warning("Accent image present but image-layout is 'blank'")

    # =========================================================================
    # BODY VALIDATION
    # =========================================================================

    def _validate_body(self, body: GyMLBody, result: ValidationResult):
        """
        Validate body container and its children.
        From gyanova_markup_language.md §4, §5.
        """
        allowed_in_body = [
            "h1",
            "h2",
            "h3",
            "h4",
            "p",
            "columns",
            "smart-layout",
            "img",
            "divider",
        ]

        for child in body.children:
            child_type = self._get_node_type_name(child)

            # Check if child is allowed in body
            if child_type not in allowed_in_body:
                result.add_error(f"Element '{child_type}' not allowed directly in body")

            # Recursively validate child
            self._validate_node(child, "body", result)

    def _validate_node(
        self, node: GyMLNode, parent_type: str, result: ValidationResult
    ):
        """Validate a single node and its children."""
        node_type = self._get_node_type_name(node)

        # Check forbidden nesting
        if is_nesting_forbidden(parent_type, node_type):
            result.add_error(f"Forbidden nesting: '{node_type}' inside '{parent_type}'")

        # Validate specific node types
        if isinstance(node, GyMLHeading):
            self._validate_heading(node, result)

        elif isinstance(node, GyMLColumns):
            self._validate_columns(node, result)

        elif isinstance(node, GyMLSmartLayout):
            self._validate_smart_layout(node, result)

    def _validate_heading(self, heading: GyMLHeading, result: ValidationResult):
        """Validate heading element."""
        if not 1 <= heading.level <= 4:
            result.add_error(f"Invalid heading level {heading.level}, must be 1-4")

    def _validate_columns(self, columns: GyMLColumns, result: ValidationResult):
        """
        Validate columns layout.
        From gyanova_markup_language.md §7.
        """
        # Check: colwidths matches column count
        if len(columns.colwidths) != len(columns.columns):
            result.add_error(
                f"colwidths length ({len(columns.colwidths)}) "
                f"doesn't match column count ({len(columns.columns)})"
            )

        # Check: children must be div (GyMLColumnDiv)
        for i, col in enumerate(columns.columns):
            if not isinstance(col, GyMLColumnDiv):
                result.add_error(f"Column {i}: children must be GyMLColumnDiv")
            else:
                # Validate column children
                for child in col.children:
                    self._validate_node(child, "div", result)

                    # Check for nested columns (discouraged)
                    if isinstance(child, GyMLColumns):
                        result.add_warning(
                            f"Column {i}: nested columns are discouraged"
                        )

    def _validate_smart_layout(self, layout: GyMLSmartLayout, result: ValidationResult):
        """
        Validate smart-layout.
        From gyanova_markup_language.md §8, §11.
        """
        # Check: has items
        if not layout.items:
            result.add_warning("smart-layout has no items")

        # Check: valid variant (optional - could be custom)
        valid_variants = [
            "solidBoxesWithIconsInside",
            "timeline",
            "processSteps",
            "comparison",
            "stats",
            "bigBullets",
            "cardGrid",
        ]
        if layout.variant not in valid_variants:
            result.add_warning(f"Unrecognized smart-layout variant: '{layout.variant}'")

        # Check items
        for i, item in enumerate(layout.items):
            self._validate_smart_layout_item(item, layout.variant, i, result)

    def _validate_smart_layout_item(
        self,
        item: GyMLSmartLayoutItem,
        variant: str,
        index: int,
        result: ValidationResult,
    ):
        """Validate smart-layout-item based on variant."""
        # Variant-specific validation
        if variant == "timeline":
            if not item.year and not item.description:
                result.add_warning(
                    f"Timeline item {index}: missing year or description"
                )

        elif variant == "stats":
            if not item.value:
                result.add_warning(f"Stats item {index}: missing value")

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def _get_node_type_name(self, node: GyMLNode) -> str:
        """Get the GyML type name for a node."""
        if isinstance(node, GyMLHeading):
            return f"h{node.level}"
        elif isinstance(node, GyMLParagraph):
            return "p"
        elif isinstance(node, GyMLColumns):
            return "columns"
        elif isinstance(node, GyMLSmartLayout):
            return "smart-layout"
        elif isinstance(node, GyMLImage):
            return "img"
        elif isinstance(node, GyMLDivider):
            return "divider"
        else:
            return type(node).__name__.lower()

    def _calculate_depth(self, section: GyMLSection) -> int:
        """Calculate maximum nesting depth."""
        if not section.body:
            return 1

        return 1 + self._calculate_body_depth(section.body)

    def _calculate_body_depth(self, body: GyMLBody) -> int:
        """Calculate depth of body and its children."""
        if not body.children:
            return 1

        max_child_depth = 0
        for child in body.children:
            child_depth = self._calculate_node_depth(child)
            max_child_depth = max(max_child_depth, child_depth)

        return 1 + max_child_depth

    def _calculate_node_depth(self, node: GyMLNode) -> int:
        """Calculate depth of a node."""
        if isinstance(node, GyMLColumns):
            max_col_depth = 0
            for col in node.columns:
                for child in col.children:
                    child_depth = self._calculate_node_depth(child)
                    max_col_depth = max(max_col_depth, child_depth)
            return 1 + max_col_depth

        elif isinstance(node, GyMLSmartLayout):
            return 2  # smart-layout → smart-layout-item

        else:
            return 1
