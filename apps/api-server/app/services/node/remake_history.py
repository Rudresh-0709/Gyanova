import json
import os
import sys
import asyncio
from typing import Dict, Any, List

# Setup paths
script_dir = os.path.dirname(os.path.abspath(__file__))
api_server_root = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))
if api_server_root not in sys.path:
    sys.path.insert(0, api_server_root)

from app.services.node.new_slide_planner import plan_slides_for_subtopic
from app.services.node.slides.gyml.generator import GyMLContentGenerator


def _classify_density(
    block_count: int, primary_item_count: int = 0, text_length: int = 0
) -> str:
    """Classify slide density based on block count, primary items, and total text."""
    # More aggressive thresholds to match renderer's SlideFitnessGate
    if block_count >= 3 and primary_item_count >= 3:
        return "dense"
    if block_count >= 4 or primary_item_count >= 4 or text_length > 600:
        return "dense"
    elif block_count <= 1 and primary_item_count <= 2 and text_length < 200:
        return "compact"
    else:
        return "medium"


def _count_primary_items(gyml_content: Dict[str, Any]) -> int:
    """Count items in the primary block (simplified)."""
    blocks = gyml_content.get("contentBlocks", [])
    primary_idx = gyml_content.get("primary_block_index", 0)

    if not blocks or primary_idx >= len(blocks):
        return 1

    primary = blocks[primary_idx]
    block_type = primary.get("type", "")

    if block_type == "smart_layout":
        return len(primary.get("items", []))
    elif block_type == "comparison_table":
        return len(primary.get("rows", []))
    elif block_type in ("key_value_list", "numbered_list", "bullet_list", "step_list"):
        return len(primary.get("items", []))
    return 1


def remake_history():
    print("📜 Planning new History slides for 'The French Revolution'...")
    subtopic = {
        "name": "The French Revolution",
        "difficulty": "Intermediate",
        "id": "hist_fr_001",
    }

    # 1. Plan slides
    plan = plan_slides_for_subtopic(subtopic)
    print(f"✅ Planned {len(plan['slides'])} slides.")

    # 2. Generate content for each slide
    generator = GyMLContentGenerator()
    final_slides = []
    layout_history = []
    angle_history = []
    variant_history = []

    for i, slide_plan in enumerate(plan["slides"]):
        print(
            f"🚀 Generating Slide {i+1}: {slide_plan['title']} ({slide_plan['selected_template']})"
        )

        gyml = generator.generate(
            title=slide_plan["title"],
            goal=slide_plan["goal"],
            purpose=slide_plan["purpose"],
            subtopic=subtopic["name"],
            content_angle=slide_plan["content_angle"],
            template_name=slide_plan["selected_template"],
            layout_history=layout_history,
            slide_index=i,
            variant_history=variant_history,
        )

        # Classify density dynamically
        blocks = gyml.get("contentBlocks", [])
        primary_item_count = _count_primary_items(gyml)

        # Calculate total text length for density check
        total_text = sum(len(str(b.get("text", b.get("content", "")))) for b in blocks)
        density = _classify_density(len(blocks), primary_item_count, total_text)

        # Update history for variety
        layout_history.append(gyml.get("layout", "left"))

        angle_history.append(slide_plan["content_angle"])
        if len(layout_history) > 10:
            layout_history.pop(0)

        # Track variant for variety
        # The primary block variant is stored in the content block at primary_block_index
        primary_idx = gyml.get("primary_block_index", 0)
        blocks = gyml.get("contentBlocks", [])
        if primary_idx < len(blocks):
            primary = blocks[primary_idx]
            if "variant" in primary:
                variant_history.append(primary["variant"])

        # Merge plan metadata with generated gyml
        slide_output = {
            "title": slide_plan["title"],
            "intent": slide_plan["intent"],
            "content_angle": slide_plan["content_angle"],
            "selected_template": slide_plan["selected_template"],
            "slide_density": density,
            "gyml_content": gyml,
            "primary_block_index": gyml.get("primary_block_index", 0),
        }
        final_slides.append(slide_output)

    # 3. Save as test_output_history.json
    output_data = {
        "topic": "The French Revolution",
        "slides": {"hist-fr": final_slides},
    }

    output_path = os.path.join(script_dir, "test_output_history.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    print(f"✨ Successfully remade History slides at: {output_path}")


if __name__ == "__main__":
    remake_history()
