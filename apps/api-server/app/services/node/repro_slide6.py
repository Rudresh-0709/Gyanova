import json
import os
import sys
import asyncio
from pathlib import Path

# Setup paths
script_dir = os.path.dirname(os.path.abspath(__file__))
api_server_root = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))
if api_server_root not in sys.path:
    sys.path.insert(0, api_server_root)

from app.services.node.rendering_node import rendering_node


async def test_slide_6():
    input_path = os.path.join(script_dir, "test_output_history.json")
    with open(input_path, "r", encoding="utf-8") as f:
        state = json.load(f)

    # Isolate slide 6
    subtopic_id = list(state["slides"].keys())[0]
    slide_6 = state["slides"][subtopic_id][5]
    print(f"Testing Slide: {slide_6['title']} (Subtopic: {subtopic_id})")

    test_state = {"topic": state["topic"], "slides": {subtopic_id: [slide_6]}}

    try:
        result = await rendering_node(test_state)
        rendered_slide = result["slides"][subtopic_id][0]
        if rendered_slide.get("html_content"):
            print("✅ Success!")
        else:
            print(f"❌ Failed: {rendered_slide.get('html_error')}")
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_slide_6())
