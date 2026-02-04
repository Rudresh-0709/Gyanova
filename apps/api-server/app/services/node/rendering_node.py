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
    Final Rendering Node.
    Takes the structured content from content_generation_node and converts it to HTML.

    Pipeline:
    1. SlideComposer: JSON -> ComposedSlide
    2. GyMLSerializer: ComposedSlide -> GyML
    3. GyMLRenderer: GyML -> HTML
    """
    slides = state.get("slides", {})

    # Initialize pipeline
    composer = SlideComposer()
    serializer = GyMLSerializer()
    renderer = GyMLRenderer(theme=get_theme("midnight"))  # Default theme

    print("🎨 [Rendering Node] Starting GyML rendering pipeline...")

    for sub_id, slide_list in slides.items():
        for slide in slide_list:
            slide_id = slide.get("slide_id", "unknown")
            gyml_content = slide.get("gyml_content")

            if not gyml_content:
                print(f"   ⚠ No GyML content for slide {slide_id}, skipping.")
                continue

            print(f"   Processing slide: {slide_id}")

            try:
                # 1. Compose (Validation & Logic)
                composed_slides = composer.compose(gyml_content)
                if not composed_slides:
                    print(f"   ❌ Composer returned empty list for {slide_id}")
                    continue

                # We expect 1-to-1 mapping usually, but Composer can split slides
                # For this node, we'll just render them all and join them,
                # or strictly handle the first one if we want to enforce 1-slide-per-request.
                # The current architecture expects 1 slide object -> 1 HTML string.

                # 2. Serialize
                gyml_sections = serializer.serialize_many(composed_slides)

                # 3. Render
                # Note: render_complete generates full HTML page (<html>...</html>)
                # If we need fragments, we should add a render_fragment method or strip tags.
                # For now, we assume the frontend wants a full compliant HTML string.
                html_output = renderer.render_complete(gyml_sections)

                # Store output
                slide["html_content"] = html_output
                print(f"   ✅ Rendered {len(html_output)} chars")

            except Exception as e:
                print(f"   ❌ Rendering failed for {slide_id}: {e}")
                slide["html_error"] = str(e)
                # Maintain fallback behavior if needed or leave empty

    state["slides"] = slides
    return state
