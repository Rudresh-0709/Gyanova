"""
Media enrichment service stub for debug harness testing.

This service takes slides and enriches them with media assets:
- Concept images (populates src URLs)
- Icons (marks items with icon names)
- Accent images (decorative)

For testing purposes, this stub generates realistic-looking URLs and icon assignments.
"""

from __future__ import annotations

from typing import Any, Dict, List


def _get_concept_image_url(topic: str, layout: str, brief_id: str = "") -> str:
    """Generate a realistic concept image URL based on topic and layout."""
    # Stub: return a mock URL that indicates enrichment occurred
    safe_topic = topic.lower().replace(" ", "_")
    return f"https://example.com/concepts/{safe_topic}_{layout}_{brief_id}.png"


def _get_icon_name(index: int, block_type: str = "list") -> str:
    """Generate icon names for list items."""
    icon_pool = [
        "check-circle",
        "lightbulb",
        "arrow-right",
        "target",
        "star",
        "zap",
        "link",
        "folder",
        "users",
        "settings",
    ]
    return icon_pool[index % len(icon_pool)]


def enrich_slide_media_sync(
    slide: Dict[str, Any],
    topic: str = "",
    image_layout: str = "top",
) -> None:
    """
    Synchronously enrich a slide with media assets.

    This function modifies the slide IN-PLACE:
    - Populates concept image URLs in image blocks
    - Assigns icon names to list items
    - Marks accent images

    Args:
        slide: Slide dict with gyml_content that has contentBlocks
        topic: Course topic for context-aware image selection
        image_layout: Layout type (top, bottom, left, right, none)
    """
    if not isinstance(slide, dict):
        return

    gyml_content = slide.get("gyml_content", {})
    if not isinstance(gyml_content, dict):
        return

    content_blocks = gyml_content.get("contentBlocks", [])
    if not isinstance(content_blocks, list):
        return

    brief_id = slide.get("id", "unknown")
    concept_image_added = False

    for block in content_blocks:
        if not isinstance(block, dict):
            continue

        block_type = str(block.get("type") or "").strip()

        # Enrich image blocks with URLs
        if block_type == "image":
            is_accent = block.get("is_accent", False)
            if not is_accent and not concept_image_added:
                # This is a concept image placeholder - populate it
                block["src"] = _get_concept_image_url(topic, image_layout, brief_id)
                concept_image_added = True
            else:
                # Accent or secondary image
                block["is_accent"] = True
                block["src"] = f"https://example.com/accents/accent_{brief_id}.png"

        # Enrich list items with icons
        elif block_type in ("numbered_list", "key_value_list", "smart_layout"):
            items = block.get("items", [])
            if isinstance(items, list):
                for i, item in enumerate(items):
                    if isinstance(item, dict) and not item.get("icon_name"):
                        item["icon_name"] = _get_icon_name(i, block_type)

        # Enrich process blocks with icons/labels
        elif block_type in ("cyclic_process", "process_arrow"):
            items = block.get("items", [])
            if isinstance(items, list):
                for i, item in enumerate(items):
                    if isinstance(item, dict) and not item.get("icon_name"):
                        item["icon_name"] = _get_icon_name(i, block_type)

    # Ensure at least one concept image exists if layout requires it
    if image_layout != "none" and not concept_image_added:
        # Add a default concept image block
        concept_image_block = {
            "type": "image",
            "src": _get_concept_image_url(topic, image_layout, brief_id),
            "alt": f"Concept image for {topic}",
            "is_accent": False,
        }
        content_blocks.insert(0, concept_image_block)
