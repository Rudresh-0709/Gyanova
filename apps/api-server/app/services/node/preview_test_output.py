"""
Preview Content-First Test Output

Renders the JSON output from content-first pipeline into visual HTML slides.
Mocks image generation with placeholders for fast preview.
"""

import json
import os
import sys
import asyncio
from pathlib import Path
from unittest.mock import MagicMock

# Force UTF-8 for Windows terminal
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# 1. Setup paths — crucial for internal imports to work
script_dir = os.path.dirname(os.path.abspath(__file__))
# node/ -> services/ -> app/ -> api-server/ (3 levels)
api_server_root = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))
if api_server_root not in sys.path:
    sys.path.insert(0, api_server_root)

# 2. Mock Image Generation - COMMENTED OUT to enable real images
# try:
#     from app.services.node.slides.gyml.image_generator import ImageGenerator
#
#     async def mock_gen_image(*args, **kwargs):
#         return "https://placehold.co/600x400?text=Mock+Generated+Image"
#
#     async def mock_gen_accent(*args, **kwargs):
#         # Return a slightly different one for accents
#         return "https://placehold.co/1024x1024?text=Mock+Accent+Image"
#
#     ImageGenerator.generate_image = mock_gen_image
#     ImageGenerator.generate_accent_image = mock_gen_accent
#     print("DONE: Leonardo AI mocked with placeholders.")
# except ImportError:
#     print(
#         "WARN: Could not mock ImageGenerator, rendering might fail if it attempts real calls."
#     )

from app.services.node.rendering_node import rendering_node


async def preview_subject(subject: str):
    print(f"--- Rendering previews for: {subject} ---")

    # Load test output
    input_path = os.path.join(script_dir, f"test_output_{subject}.json")
    if not os.path.exists(input_path):
        print(f"FAIL: Input file not found: {input_path}")
        return

    with open(input_path, "r", encoding="utf-8") as f:
        state = json.load(f)

    print(f"  Loaded state with {len(state.get('slides', {}))} subtopics.")
    for sid, slides in state.get("slides", {}).items():
        print(f"    Subtopic {sid}: {len(slides)} slides")

    # Run rendering_node (async)
    try:
        print("  Calling rendering_node...")
        state = await rendering_node(state)
        print("  rendering_node completed.")
    except Exception as e:
        print(f"  FAIL: Error in rendering_node: {e}")
        import traceback

        traceback.print_exc()
        return

    # Output directory
    preview_dir = os.path.join(script_dir, f"test_preview_v2_{subject}")
    os.makedirs(preview_dir, exist_ok=True)

    # Save each slide to a separate HTML file
    total_rendered = 0
    slide_filenames = []
    for sub_id, slides in state.get("slides", {}).items():
        for i, slide in enumerate(slides):
            html = slide.get("html_content")
            if not html:
                error = slide.get("html_error", "Unknown error")
                print(f"  FAIL: Slide {i+1} ('{slide.get('title')}') failed: {error}")
                continue

            filename = f"slide_{sub_id}_{i+1}.html"
            filepath = os.path.join(preview_dir, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html)

            slide_filenames.append(filename)
            total_rendered += 1
            print(f"  OK: Rendered Slide {i+1}: {slide.get('title')}")

    # Create an index.html for easy browsing (Vertical Scroll)
    slide_iframes = [
        f'<div class="slide-container"><iframe src="{fname}"></iframe></div>'
        for fname in slide_filenames
    ]

    index_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>{subject.upper()} Slide Previews</title>
    <style>
        body {{ margin: 0; padding: 0; background: #000; }}
        .slide-container {{ 
            width: 100vw; 
            height: 100vh; 
            overflow: hidden;
            scroll-snap-align: start;
        }}
        iframe {{
            width: 100%;
            height: 100%;
            border: none;
        }}
        html {{
            scroll-snap-type: y mandatory;
        }}
    </style>
</head>
<body>
    {"".join(slide_iframes)}
</body>
</html>
"""
    index_path = os.path.join(preview_dir, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_content)

    print(f"\nFinished! Rendered {total_rendered} slides.")
    print(f"DONE: Open index in browser: {index_path}")


if __name__ == "__main__":
    subject = sys.argv[1] if len(sys.argv) > 1 else "science"
    asyncio.run(preview_subject(subject))
