import json
import os
import sys
import asyncio

# Setup paths
script_dir = os.path.dirname(os.path.abspath(__file__))
api_server_root = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))
if api_server_root not in sys.path:
    sys.path.insert(0, api_server_root)

from app.services.node.new_slide_planner import plan_slides_for_subtopic
from app.services.node.slides.gyml.generator import GyMLContentGenerator


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
        )

        # Merge plan metadata with generated gyml
        slide_output = {
            "title": slide_plan["title"],
            "intent": slide_plan["intent"],
            "content_angle": slide_plan["content_angle"],
            "selected_template": slide_plan["selected_template"],
            "slide_density": "standard",
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
