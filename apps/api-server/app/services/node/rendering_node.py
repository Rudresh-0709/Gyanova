import asyncio
from typing import Dict, Any, List
import os
import sys

# Ensure imports work
try:
    from .slides.gyml.composer import SlideComposer
    from .slides.gyml.serializer import GyMLSerializer
    from .slides.gyml.validator import GyMLValidator
    from .slides.gyml.renderer import GyMLRenderer
    from .slides.gyml.theme import get_theme
    from .slides.gyml.image_generator import ImageGenerator
except ImportError:
    # Use relative imports if running as package
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from services.node.slides.gyml.composer import SlideComposer
    from services.node.slides.gyml.serializer import GyMLSerializer
    from services.node.slides.gyml.validator import GyMLValidator
    from services.node.slides.gyml.renderer import GyMLRenderer
    from services.node.slides.gyml.theme import get_theme
    from services.node.slides.gyml.image_generator import ImageGenerator


async def rendering_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Incremental Rendering Node (Slide-level).
    Renders any slides that have gyml_content but no html_content yet.
    Handles Leonardo AI image resolution in parallel.
    """
    slides_map = state.get("slides", {})

    # Initialize pipeline once
    composer = SlideComposer()
    serializer = GyMLSerializer()
    renderer = GyMLRenderer(theme=get_theme("midnight"), animated=True)

    # 1. Collect slides that need processing
    pending_slides = []
    for sid, slide_list in slides_map.items():
        for slide in slide_list:
            if slide.get("gyml_content") and not slide.get("html_content"):
                pending_slides.append(slide)

    if not pending_slides:
        print("🎨 [Rendering Node] No new slides to render.")
        return state

    # 2. Step One: Compose and identify image needs
    # This part is synchronous and fast
    composed_objects_list = []  # List of List[ComposedSlide]
    for slide in pending_slides:
        try:
            composed = composer.compose(slide["gyml_content"])
            slide["_composed_objs"] = composed  # Temporary storage
            composed_objects_list.append(composed)
        except Exception as e:
            print(f"   ❌ Composition failed: {e}")
            slide["html_error"] = str(e)

    # 3. Step Two: Trigger Parallel Image Generation
    generation_tasks = []
    task_to_slide = []

    for slide in pending_slides:
        if "html_error" in slide:
            continue

        composed_objs = slide["_composed_objs"]
        for s_obj in composed_objs:
            # If it has a prompt and no real URL, generate it
            if (
                s_obj.image_layout != "blank"
                and s_obj.image_prompt
                and (
                    not s_obj.accent_image_url
                    or s_obj.accent_image_url == "placeholder"
                )
            ):

                print(f"   🎨 [Rendering Node] Spawning Image Gen for {s_obj.id}")
                task = ImageGenerator.generate_accent_image(
                    prompt=s_obj.image_prompt,
                    layout=s_obj.image_layout,
                    topic=s_obj.topic or "Educational content",
                )
                generation_tasks.append(task)
                task_to_slide.append(s_obj)

    # Run image generations concurrently
    if generation_tasks:
        print(
            f"   🔥 [Rendering Node] Running {len(generation_tasks)} image generations in parallel..."
        )
        results = await asyncio.gather(*generation_tasks)

        # Map results back to ComposedSlide objects
        for s_obj, url in zip(task_to_slide, results):
            if url:
                s_obj.accent_image_url = url
                s_obj.accent_image_alt = f"Generated image for {s_obj.topic}"
                print(f"   ✅ Image generated for {s_obj.id}")
            else:
                print(f"   ⚠ Image generation failed for {s_obj.id}")

    # 4. Step Three: Final Serialization and Rendering
    rendered_count = 0
    for slide in pending_slides:
        if "html_error" in slide:
            continue

        try:
            composed_objs = slide.pop("_composed_objs")
            # Serialize
            gyml_sections = serializer.serialize_many(composed_objs)
            # Render
            html_output = renderer.render_complete(gyml_sections)

            slide["html_content"] = html_output
            rendered_count += 1
            print(f"   ✅ Rendered {slide.get('slide_id', 'unknown')}")
        except Exception as e:
            print(f"   ❌ Serialization/Rendering failed: {e}")
            slide["html_error"] = str(e)

    print(f"🎨 [Rendering Node] Completed. Rendered {rendered_count} slide(s).")
    return state
