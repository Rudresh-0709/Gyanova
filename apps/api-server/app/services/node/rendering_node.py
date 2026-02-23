from typing import Dict, Any
import os
import sys

# Ensure imports work
try:
    from .slides.gyml.composer import SlideComposer
    from .slides.gyml.serializer import GyMLSerializer
    from .slides.gyml.validator import GyMLValidator
    from .slides.gyml.renderer import GyMLRenderer
    from .slides.gyml.theme import get_theme
except ImportError:
    # Use relative imports if running as package
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from services.node.slides.gyml.composer import SlideComposer
    from services.node.slides.gyml.serializer import GyMLSerializer
    from services.node.slides.gyml.validator import GyMLValidator
    from services.node.slides.gyml.renderer import GyMLRenderer
    from services.node.slides.gyml.theme import get_theme


def rendering_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Incremental Rendering Node (Slide-level).
    Renders any slides that have gyml_content but no html_content yet.
    """
    slides = state.get("slides", {})

    # Initialize pipeline once
    composer = SlideComposer()
    serializer = GyMLSerializer()
    renderer = GyMLRenderer(theme=get_theme("midnight"), animated=True)

    rendered_count = 0
    for sid, slide_list in slides.items():
        for slide in slide_list:
            slide_id = slide.get("slide_id", "unknown")
            gyml_content = slide.get("gyml_content")

            # Skip if no content or already rendered
            if not gyml_content or slide.get("html_content"):
                continue

            try:
                # 1. Compose
                composed_slides = composer.compose(gyml_content)
                if not composed_slides:
                    continue

                # 2. Serialize
                gyml_sections = serializer.serialize_many(composed_slides)

                # 3. Render
                html_output = renderer.render_complete(gyml_sections)

                slide["html_content"] = html_output
                rendered_count += 1
                print(f"   ✅ Rendered {slide_id}")

            except Exception as e:
                print(f"   ❌ Rendering failed for {slide_id}: {e}")
                slide["html_error"] = str(e)

    if rendered_count == 0:
        print("🎨 [Rendering Node] No new slides to render.")
    else:
        print(f"🎨 [Rendering Node] Rendered {rendered_count} slide(s).")

    return state
