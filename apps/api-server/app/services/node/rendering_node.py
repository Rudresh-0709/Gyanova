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
    from .slides.gyml.constants import BlockType
except ImportError:
    # Use relative imports if running as package
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from services.node.slides.gyml.composer import SlideComposer
    from services.node.slides.gyml.serializer import GyMLSerializer
    from services.node.slides.gyml.validator import GyMLValidator
    from services.node.slides.gyml.renderer import GyMLRenderer
    from services.node.slides.gyml.theme import get_theme
    from services.node.slides.gyml.image_generator import ImageGenerator
    from services.node.slides.gyml.constants import BlockType


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
            # Force re-render if it should have an image but doesn't have a real one yet
            has_prompt = bool(slide.get("gyml_content", {}).get("imagePrompt"))
            has_real_image = bool(
                slide.get("accent_image_url")
                and slide.get("accent_image_url") != "placeholder"
            )
            needs_render = not slide.get("html_content") or (
                has_prompt and not has_real_image
            )

            if slide.get("gyml_content") and needs_render:
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
            print(
                f"   [Debug] Slide {s_obj.id}: layout={s_obj.image_layout}, has_prompt={bool(s_obj.image_prompt)}, url={s_obj.accent_image_url}"
            )
            if (
                s_obj.image_layout != "blank"
                and s_obj.image_prompt
                and (
                    not s_obj.accent_image_url
                    or s_obj.accent_image_url == "placeholder"
                )
            ):

                print(f"   🎨 [Rendering Node] Spawning Image Gen for {s_obj.id}")
                print(
                    f"   🐛 DEBUG image_style being passed: {repr(s_obj.image_style)}"
                )
                task = ImageGenerator.generate_accent_image(
                    prompt=s_obj.image_prompt,
                    layout=s_obj.image_layout,
                    topic=s_obj.topic or "Educational content",
                    style=s_obj.image_style,
                )
                generation_tasks.append(task)
                task_to_slide.append((s_obj, None))  # (object, optional_item_dict)

            # Block-level Multi-image (e.g., Process Arrow)
            for section in s_obj.sections:
                # Combine primary and secondary blocks
                blocks = section.secondary_blocks + (
                    [section.primary_block] if section.primary_block else []
                )
                for block in blocks:
                    if block.type in {
                        BlockType.PROCESS_ARROW_BLOCK.value,
                        BlockType.CYCLIC_PROCESS_BLOCK.value,
                    }:
                        items = block.content.get("items", [])
                        for item in items:
                            prompt = item.get("imagePrompt")
                            if prompt and (
                                not item.get("image_url")
                                or item.get("image_url") == "null"
                            ):
                                print(
                                    f"   🎨 [Rendering Node] Item Image Gen for {block.type}"
                                )
                                # Use "simple_drawing" style as requested
                                task = ImageGenerator.generate_image(
                                    prompt=prompt,
                                    width=512,
                                    height=512,
                                    style="simple_drawing",
                                )
                                generation_tasks.append(task)
                                task_to_slide.append((block, item))

    # Run image generations concurrently with a semaphore to avoid rate limits
    if generation_tasks:
        print(
            f"   🔥 [Rendering Node] Running {len(generation_tasks)} image generations SEQUENTIALLY..."
        )

        # Semaphore to limit concurrent requests (conservative to avoid Leonardo API issues)
        sem = asyncio.Semaphore(1)

        async def sem_task(task_coro):
            async with sem:
                # Add a tiny stagger
                await asyncio.sleep(0.5)
                return await task_coro

        results = await asyncio.gather(*(sem_task(t) for t in generation_tasks))

        # Map results back to ComposedSlide or Item dicts
        for (target, item), url in zip(task_to_slide, results):
            if url:
                if item:
                    # Target is a block, we update the item dict inside it
                    item["image_url"] = url
                    print(f"   ✅ Item image generated for {target.type}")
                else:
                    # Target is a ComposedSlide (accent image)
                    target.accent_image_url = url
                    target.accent_image_alt = f"Generated image for {target.topic}"
                    print(f"   ✅ Accent image generated for {target.id}")
            else:
                print(
                    f"   ⚠ Image generation failed for a target (possibly timeout or rate limit)"
                )

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
