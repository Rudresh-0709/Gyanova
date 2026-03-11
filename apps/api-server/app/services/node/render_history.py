"""Render each history slide individually to find which one fails."""
import json, os, sys, asyncio, traceback, io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

script_dir = os.path.dirname(os.path.abspath(__file__))
api_server_root = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))
if api_server_root not in sys.path:
    sys.path.insert(0, api_server_root)

from app.services.node.slides.gyml.composer import SlideComposer
from app.services.node.slides.gyml.serializer import GyMLSerializer
from app.services.node.slides.gyml.renderer import GyMLRenderer
from app.services.node.slides.gyml.theme import get_theme

async def main():
    path = os.path.join(script_dir, "test_output_history.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    composer = SlideComposer()
    serializer = GyMLSerializer()
    renderer = GyMLRenderer(theme=get_theme("midnight"), animated=True)

    preview_dir = os.path.join(script_dir, "test_preview_v2_history")
    os.makedirs(preview_dir, exist_ok=True)
    
    slide_filenames = []
    
    for sub_id, slides in data.get("slides", {}).items():
        for i, slide in enumerate(slides):
            title = slide.get("title", "?")
            blocks = slide.get("gyml_content", {}).get("contentBlocks", [])
            variants = [b.get("variant") for b in blocks if b.get("type") == "smart_layout"]
            print(f"\nSlide {i+1}: {title}")
            print(f"  Variant: {variants}")
            
            try:
                composed = composer.compose(slide["gyml_content"])
                gyml_sections = serializer.serialize_many(composed)
                html = renderer.render_complete(gyml_sections)
                
                filename = f"slide_{sub_id}_{i+1}.html"
                with open(os.path.join(preview_dir, filename), "w", encoding="utf-8") as f:
                    f.write(html)
                slide_filenames.append(filename)
                print(f"  ✅ OK")
            except Exception as e:
                print(f"  ❌ FAILED: {e}")
                traceback.print_exc()
    
    # Create index.html
    if slide_filenames:
        iframes = ''.join(f'<div class="slide-container"><iframe src="{fn}"></iframe></div>' for fn in slide_filenames)
        index = f"""<!DOCTYPE html>
<html><head><title>HISTORY Slide Previews</title>
<style>
body {{ margin: 0; padding: 0; background: #000; }}
.slide-container {{ width: 100vw; height: 100vh; overflow: hidden; scroll-snap-align: start; }}
iframe {{ width: 100%; height: 100%; border: none; }}
html {{ scroll-snap-type: y mandatory; }}
</style></head><body>{iframes}</body></html>"""
        with open(os.path.join(preview_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(index)
        print(f"\nDONE: {len(slide_filenames)} slides -> {preview_dir}/index.html")

asyncio.run(main())
