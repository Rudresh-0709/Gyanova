import asyncio
import time
from typing import Dict, Any, List
import os
import sys
import re

# Ensure imports work
try:
    from app.services.node.slides.gyml.composer import SlideComposer
    from app.services.node.slides.gyml.serializer import GyMLSerializer
    from app.services.node.slides.gyml.validator import GyMLValidator
    from app.services.node.slides.gyml.renderer import GyMLRenderer
    from app.services.node.slides.gyml.theme import get_theme
    from app.services.node.slides.gyml.image_generator import ImageGenerator
    from app.services.node.slides.gyml.constants import BlockType
except ImportError:
    # Use relative imports if running as package
    try:
        from .slides.gyml.composer import SlideComposer
        from .slides.gyml.serializer import GyMLSerializer
        from .slides.gyml.validator import GyMLValidator
        from .slides.gyml.renderer import GyMLRenderer
        from .slides.gyml.theme import get_theme
        from .slides.gyml.image_generator import ImageGenerator
        from .slides.gyml.constants import BlockType
    except ImportError:
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
        from services.node.slides.gyml.composer import SlideComposer
        from services.node.slides.gyml.serializer import GyMLSerializer
        from services.node.slides.gyml.validator import GyMLValidator
        from services.node.slides.gyml.renderer import GyMLRenderer
        from services.node.slides.gyml.theme import get_theme
        from services.node.slides.gyml.image_generator import ImageGenerator
        from services.node.slides.gyml.constants import BlockType

from pathlib import Path

try:
    from app.services.node.intro_narration_node import generate_intro_image_prompt
except ImportError:
    try:
        from .intro_narration_node import generate_intro_image_prompt
    except ImportError:
        from intro_narration_node import generate_intro_image_prompt


def inject_template_variables(template_html: str, variables: Dict[str, Any]) -> str:
    """
    Simple template variable injection using Jinja2-like syntax.
    Replaces {{ variable_name }} with actual values.
    """
    result = template_html

    # Handle basic Jinja-style conditional blocks used by intro blueprints.
    # Example: {% if image_url %}...{% endif %}
    conditional_pattern = re.compile(
        r"{%\s*if\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*%}(.*?){%\s*endif\s*%}",
        re.DOTALL,
    )
    while True:
        match = conditional_pattern.search(result)
        if not match:
            break
        key = match.group(1)
        body = match.group(2)
        replacement = body if variables.get(key) else ""
        result = result[: match.start()] + replacement + result[match.end() :]

    # Replace {{ key }} and {{key}} variants with values
    for key, value in variables.items():
        rendered_value = "" if value is None else str(value)
        result = re.sub(r"{{\s*" + re.escape(key) + r"\s*}}", rendered_value, result)

    # Clean up any unreplaced placeholders/conditionals to avoid leaking template syntax.
    result = re.sub(r"{{\s*[^}]+\s*}}", "", result)
    result = re.sub(r"{%\s*[^%]+\s*%}", "", result)
    return result


async def generate_intro_html(intro_data: Dict[str, Any], intro_type: str) -> str:
    """
    Generate HTML for intro slides using blueprint templates.
    
    Args:
        intro_data: Dict with title, tagline, badge, image_url, narration_text
        intro_type: "lesson" or "subtopic"
    
    Returns:
        Rendered HTML string
    """
    try:
        # Determine blueprint path
        if intro_type == "lesson":
            blueprint_name = "intro_lesson.html"
        elif intro_type == "subtopic":
            blueprint_name = "intro_subtopic.html"
        else:
            return ""
        
        blueprint_path = Path(__file__).parent / "slides" / "blueprints" / blueprint_name
        
        # Load blueprint
        if not blueprint_path.exists():
            print(f"⚠️ Blueprint not found: {blueprint_path}")
            return ""
        
        with open(blueprint_path, "r") as f:
            template_html = f.read()
        
        # Extract variables from intro_data
        variables = {
            "title": intro_data.get("title", ""),
            "tagline": intro_data.get("tagline", ""),
            "badge": intro_data.get("badge", "LESSON" if intro_type == "lesson" else "SECTION"),
            "image_url": intro_data.get("image_url", ""),
        }
        
        # Inject variables
        html_output = inject_template_variables(template_html, variables)
        return html_output
    
    except Exception as e:
        print(f"❌ Error generating intro HTML: {e}")
        return ""


async def rendering_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Incremental Rendering Node (Slide-level).
    Renders any slides that have gyml_content but no html_content yet.
    Also generates HTML for intro slides (lesson + subtopic intros).
    Handles Leonardo AI image resolution in parallel.
    
    CRITICAL ARCHITECTURE NOTE:
    - ComposedSlide objects (from composer.compose()) are TRANSIENT and NOT JSON serializable
    - These objects are kept ONLY in the local `composed_by_slide` dict
    - They are NEVER written to state or persisted to tasks.json
    - Image generation results update the local ComposedSlide objects
    - Final HTML is serialized from ComposedSlide and written to state as html_content
    - This ensures tasks_db remains JSON-serializable throughout the workflow
    """
    # ═══════════════════════════════════════════════════════════════════════════
    # CANCELLATION CHECK: Exit early if task has been cancelled
    # ═══════════════════════════════════════════════════════════════════════════
    task_status = state.get("_task_status", "processing")
    if task_status == "cancelled":
        print("⚠️ [Rendering Node] Task marked as cancelled, skipping slide rendering")
        return {}
    
    slides_map = state.get("slides", {})
    image_concurrency = max(1, int(os.getenv("IMAGE_GEN_CONCURRENCY", "3")))

    # Initialize pipeline once
    composer = SlideComposer()
    serializer = GyMLSerializer()
    renderer = GyMLRenderer(theme=get_theme("midnight"), animated=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # PROCESS INTRO SLIDES (NEW)
    # ═══════════════════════════════════════════════════════════════════════════
    
    # Collect intro image generation tasks
    intro_image_tasks = []
    intro_task_mapping = []
    
    # Process Lesson Intro
    lesson_intro = state.get("lesson_intro_narration")
    if lesson_intro and not lesson_intro.get("image_url"):
        print("🎨 [Rendering Node] Generating lesson intro image...")
        prompt = generate_intro_image_prompt("lesson", lesson_intro.get("title", "Lesson"))
        print(f"   📝 Image prompt: {prompt[:60]}...")
        task = ImageGenerator.generate_image(
            prompt=prompt,
            width=1024,
            height=576,
            style="dynamic"
        )
        intro_image_tasks.append(task)
        intro_task_mapping.append(("lesson", lesson_intro))
    
    # Note: Subtopic intros are no longer generated per user request
    
    # Run intro image generation concurrently
    if intro_image_tasks:
        print(
            f"🔥 [Rendering Node] Running {len(intro_image_tasks)} intro image generation(s) with concurrency={image_concurrency}..."
        )
        sem = asyncio.Semaphore(image_concurrency)
        
        async def sem_task(task_coro):
            async with sem:
                return await task_coro
        
        image_results = await asyncio.gather(*(sem_task(t) for t in intro_image_tasks))
        
        # Map results back
        for (intro_kind, intro_obj), image_url in zip(intro_task_mapping, image_results):
            if image_url:
                intro_obj["image_url"] = image_url
                print(f"✅ {intro_kind.title()} intro image generated")
            else:
                # Use a local SVG fallback so intro slides always keep visual structure.
                intro_title = intro_obj.get("title") or ("Lesson" if intro_kind == "lesson" else "Section")
                intro_tagline = intro_obj.get("tagline") or ""
                intro_obj["image_url"] = ImageGenerator.build_svg_fallback_data_url(
                    title=intro_title,
                    subtitle=intro_tagline,
                )
                print(f"⚠️ {intro_kind.title()} intro image generation failed; using local SVG fallback")
    
    # Now generate HTML for intros (with images if available)
    lesson_intro = state.get("lesson_intro_narration")
    lesson_html = (lesson_intro or {}).get("html_doc", "") or ""
    lesson_needs_refresh = (
        lesson_intro
        and (
            not lesson_html
            or (
                lesson_intro.get("image_url")
                and "class=\"background-image\"" not in lesson_html
            )
        )
    )
    if lesson_needs_refresh:
        print("🎬 [Rendering Node] Generating lesson intro HTML...")
        html = await generate_intro_html(lesson_intro, "lesson")
        if html:
            lesson_intro["html_doc"] = html
            print("✅ Lesson intro HTML generated")
    
    # Subtopic intros are no longer rendered since they are removed from generation
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PROCESS REGULAR CONTENT SLIDES
    # ═══════════════════════════════════════════════════════════════════════════

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
    # Keep composed objects local only. They are not JSON serializable and
    # must never be written back into the workflow state.
    composed_by_slide = {}
    for slide in pending_slides:
        try:
            gyml = slide.get("gyml_content")
            if gyml:
                composed = composer.compose(gyml)
                composed_by_slide[id(slide)] = composed
        except Exception as e:
            print(f"   ❌ Composition failed: {e}")
            slide["html_error"] = str(e)

    # 3. Step Two: Trigger Parallel Image Generation
    generation_tasks = []
    task_to_slide = []

    for slide in pending_slides:
        if "html_error" in slide:
            continue

        composed_objs = composed_by_slide.get(id(slide), [])
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
                task_to_slide.append(("accent", s_obj, None))

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
                                task_to_slide.append(("item", block, item))
                    elif block.type == BlockType.IMAGE.value:
                        # Standalone image block
                        prompt = block.content.get("imagePrompt") or block.content.get("prompt") or s_obj.image_prompt
                        url = block.content.get("url") or block.content.get("src")
                        if prompt and (not url or url == "placeholder" or "upload.wikimedia.org" in str(url)):
                            print(f"   🎨 [Rendering Node] Standalone Image Gen for {block.type} using prompt: {prompt[:30]}...")
                            
                            # Determine style based on image_role if known
                            style_to_use = s_obj.image_style
                            if s_obj.image_role == "content" and not style_to_use:
                                style_to_use = "diagrammatic, detailed, educational illustration"
                            
                            task = ImageGenerator.generate_image(
                                prompt=prompt,
                                width=1024,
                                height=768, # Landscape ratio better for content
                                style=style_to_use
                            )
                            generation_tasks.append(task)
                            task_to_slide.append(("block_image", block, None))

    # Run image generations concurrently with a semaphore to avoid rate limits
    t_images = 0
    if generation_tasks:
        t_images_start = time.time()
        print(
            f"   🔥 [Rendering Node] Running {len(generation_tasks)} image generations with concurrency={image_concurrency}..."
        )

        # Semaphore to limit concurrent requests and avoid provider rate limits.
        sem = asyncio.Semaphore(image_concurrency)

        async def sem_task(task_coro):
            async with sem:
                return await task_coro

        results = await asyncio.gather(*(sem_task(t) for t in generation_tasks))
        t_images = time.time() - t_images_start

        # Map results back to ComposedSlide or Item dicts
        for (target_kind, target, item), url in zip(task_to_slide, results):
            if url:
                if target_kind == "item" and item:
                    # Target is a block, we update the item dict inside it
                    item["image_url"] = url
                    print(f"   ✅ Item image generated for {target.type}")
                elif target_kind == "block_image":
                    target.content["url"] = url
                    print(f"   ✅ Standalone image generated for {target.type}")
                elif target_kind == "accent":
                    target.accent_image_url = url
                    target.accent_image_alt = f"Generated image for {target.topic}"
                    print(f"   ✅ Accent image generated for {target.id}")
            else:
                print(
                    f"   ⚠ Image generation failed for a target (possibly timeout or rate limit)"
                )

    # Persist generated accent images back to state-backed slide dicts.
    # Without this, only temporary composed objects carry the URL and later graph
    # iterations think the slide still has no real image, causing re-generation.
    for slide in pending_slides:
        if "html_error" in slide:
            continue

        composed_objs = composed_by_slide.get(id(slide), [])
        if not composed_objs:
            continue

        first_real_image = next(
            (
                s_obj.accent_image_url
                for s_obj in composed_objs
                if getattr(s_obj, "accent_image_url", None)
                and getattr(s_obj, "accent_image_url", None) != "placeholder"
            ),
            None,
        )

        if first_real_image:
            slide["accent_image_url"] = first_real_image
            if isinstance(slide.get("gyml_content"), dict):
                slide["gyml_content"]["accent_image_url"] = first_real_image
            if isinstance(slide.get("visual_content"), dict):
                slide["visual_content"]["accent_image_url"] = first_real_image

    # 4. Step Three: Final Serialization and Rendering
    rendered_count: int = 0
    for slide in pending_slides:
        if "html_error" in slide:
            continue

        try:
            composed_objs = composed_by_slide.get(id(slide))
            if composed_objs and isinstance(composed_objs, list) and len(composed_objs) > 0:
                t_render_start = time.time()
                # Serialize
                gyml_sections = serializer.serialize_many(composed_objs)
                # Render
                html_output = renderer.render_complete(gyml_sections)
                t_render = time.time() - t_render_start

                slide["html_content"] = html_output
                rendered_count += 1
                
                # Performance Logging
                perf = slide.get("_perf", {})
                gyml_t = perf.get("gyml", 0)
                icons_t = perf.get("media", 0)
                # "media" category includes both icon enrichment and Leonardo image generation
                total_media = round(icons_t + t_images, 2)
                
                print(f"   ✅ Rendered {slide.get('slide_id', 'unknown')}")
                print(f"   [PERF] gyml={gyml_t}s media={total_media}s render={round(t_render, 2)}s")
            elif not composed_objs:
                print(f"   ⚠️ No composed objects for {slide.get('slide_id', 'unknown')}")
        except Exception as e:
            print(f"   ❌ Serialization/Rendering failed: {e}")
            slide["html_error"] = str(e)

    print(f"🎨 [Rendering Node] Completed. Rendered {rendered_count} slide(s).")
    # Return modified fields including intro slides
    return_dict = {"slides": slides_map}
    
    # Include intro data if it was processed
    if state.get("lesson_intro_narration"):
        return_dict["lesson_intro_narration"] = state["lesson_intro_narration"]
    
    return return_dict
