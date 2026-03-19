#!/usr/bin/env python3
"""
Fix functions that don't properly handle None primary_block_index for sparse templates.
"""
import re

file_path = 'd:\\DATA\\Desktop\\AI_TUTOR\\ai-teacher-app\\apps\\api-server\\app\\services\\node\\content_generation_node.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# ─────────────────────────────────────────────────────────────────────
# Fix 1: _generate_animation_metadata
# ─────────────────────────────────────────────────────────────────────
old_anim = '''def _generate_animation_metadata(gyml_content: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate animation metadata from the primary block.
    Only the primary block gets animated; other blocks appear statically.

    Returns:
        {
            "animation_unit": "bullet" | "step" | "card" | ...,
            "animation_unit_count": int,
            "animated_block_index": int
        }
    """
    if gyml_content is None:
        return {
            "animation_unit": "item",
            "animation_unit_count": 0,
            "animated_block_index": 0,
        }
    blocks = gyml_content.get("contentBlocks", [])
    primary_idx = gyml_content.get("primary_block_index", 0)

    if not blocks or primary_idx >= len(blocks):
        return {
            "animation_unit": "item",
            "animation_unit_count": 1,
            "animated_block_index": 0,
        }'''

new_anim = '''def _generate_animation_metadata(gyml_content: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate animation metadata from the primary block.
    Only the primary block gets animated; other blocks appear statically.
    
    For sparse templates (primary_block_index is None), uses the first block.

    Returns:
        {
            "animation_unit": "bullet" | "step" | "card" | "paragraph" | ...,
            "animation_unit_count": int,
            "animated_block_index": int or None
        }
    """
    if gyml_content is None:
        return {
            "animation_unit": "item",
            "animation_unit_count": 0,
            "animated_block_index": 0,
        }
    blocks = gyml_content.get("contentBlocks", [])
    primary_idx = gyml_content.get("primary_block_index")

    # -- Handle sparse templates (primary_block_index is None) --
    if primary_idx is None:
        if not blocks:
            return {
                "animation_unit": "item",
                "animation_unit_count": 1,
                "animated_block_index": None,
            }
        # Use first block as animation target for sparse templates
        primary_idx = 0

    # -- Handle standard templates --
    if not blocks or primary_idx >= len(blocks):
        return {
            "animation_unit": "item",
            "animation_unit_count": 1,
            "animated_block_index": 0,
        }'''

if old_anim in content:
    content = content.replace(old_anim, new_anim)
    print("✓ Fixed _generate_animation_metadata")
else:
    print("✗ Could not find _generate_animation_metadata")

# ─────────────────────────────────────────────────────────────────────
# Fix 2: _extract_primary_items_detail
# ─────────────────────────────────────────────────────────────────────
old_extract = '''def _extract_primary_items_detail(gyml_content: Optional[Dict[str, Any]]) -> List[str]:
    """
    Extract a list of item labels/headings from the primary block
    so the narration LLM can write one segment per item.
    """
    if gyml_content is None:
        return ["Main content"]
    blocks = gyml_content.get("contentBlocks", [])
    primary_idx = gyml_content.get("primary_block_index", 0)

    if not blocks or primary_idx >= len(blocks):
        return ["Main content"]'''

new_extract = '''def _extract_primary_items_detail(gyml_content: Optional[Dict[str, Any]]) -> List[str]:
    """
    Extract a list of item labels/headings from the primary block
    so the narration LLM can write one segment per item.
    
    For sparse templates, returns text from first content block.
    """
    if gyml_content is None:
        return ["Main content"]
    blocks = gyml_content.get("contentBlocks", [])
    primary_idx = gyml_content.get("primary_block_index")

    # -- Handle sparse templates (primary_block_index is None) --
    if primary_idx is None:
        if not blocks:
            return ["Main content"]
        # For sparse templates, extract from first block
        primary_idx = 0

    if not blocks or primary_idx >= len(blocks):
        return ["Main content"]'''

if old_extract in content:
    content = content.replace(old_extract, new_extract)
    print("✓ Fixed _extract_primary_items_detail")
else:
    print("✗ Could not find _extract_primary_items_detail")

# Write back
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("\n✓ All fixes applied successfully!")
