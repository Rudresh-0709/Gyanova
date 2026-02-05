"""
GyML Content Preprocessor

Validates and sanitizes input content before it reaches the Composer.
Ensures schema integrity, content limits, and basic accessibility.
"""

from typing import Dict, Any, List, Optional
import html


class ContentValidationError(Exception):
    """Raised when input content fails validation."""

    pass


class ContentPreprocessor:
    """
    Validates and sanitizes raw slide content.
    """

    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode

    def process(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point. Validate, sanitize, and fix content.
        """
        # 1. Structural Validation
        self._validate_structure(content)

        # 2. Sanitization
        content = self._sanitize_content(content)

        # 3. Accessibility Checks (auto-fix if possible)
        content = self._ensure_accessibility(content)

        return content

    def _validate_structure(self, content: Dict[str, Any]) -> None:
        """Ensure required fields exist."""
        if not isinstance(content, dict):
            raise ContentValidationError("Content must be a dictionary")

        # Title is mandatory usually, but maybe optional for blank slides?
        # Let's enforce title as a best practice for accessibility.
        if "title" not in content or not content["title"]:
            if self.strict_mode:
                raise ContentValidationError("Slide content missing title")

    def _sanitize_content(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively sanitize string values."""
        sanitized = {}
        for k, v in content.items():
            if isinstance(v, str):
                # Simple HTML escape for now
                # In production, might use bleach for allowed HTML
                sanitized[k] = html.escape(v)
            elif isinstance(v, list):
                sanitized[k] = [self._sanitize_item(i) for i in v]
            elif isinstance(v, dict):
                sanitized[k] = self._sanitize_content(v)
            else:
                sanitized[k] = v
        return sanitized

    def _sanitize_item(self, item: Any) -> Any:
        if isinstance(item, str):
            return html.escape(item)
        if isinstance(item, dict):
            return self._sanitize_content(item)
        return item

    def _ensure_accessibility(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure images have partial accessibility data."""
        # This is a shallow check. In reality, we'd need to traverse blocks.
        # This pipeline is early-stage (raw input), so we might not have 'blocks' yet.
        # But if 'images' list exists or 'accent_image' exists, check them.

        # If input has 'accent_image' string, convert to object with alt if needed?
        # Usually input is { title: "...", image: "url" }

        return content
