from __future__ import annotations

from typing import Any, Dict, List, Tuple

try:
    from app.services.llm.model_loader import load_openai, load_groq
except ImportError:
    try:
        from ...llm.model_loader import load_openai, load_groq  # type: ignore
    except ImportError:
        # Fallback: define stubs
        def load_openai(*args, **kwargs):  # type: ignore
            raise ImportError("Could not load OpenAI")

        def load_groq(*args, **kwargs):  # type: ignore
            raise ImportError("Could not load Groq")


def _detect_concept_visuals(enriched_slide: Dict[str, Any]) -> Tuple[bool, str, bool]:
    """
    Detect what visuals exist on the enriched slide.

    Returns:
        (has_concept_image, concept_image_alt, has_icons)
    """
    has_concept_image = False
    concept_image_alt = ""
    has_icons = False

    gyml_content = enriched_slide.get("gyml_content", {})
    if not isinstance(gyml_content, dict):
        return has_concept_image, concept_image_alt, has_icons

    content_blocks = gyml_content.get("contentBlocks", [])
    if not isinstance(content_blocks, list):
        return has_concept_image, concept_image_alt, has_icons

    # Detect concept image (non-accent image with src != placeholder)
    for block in content_blocks:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "image" and not block.get("is_accent", False):
            src = block.get("src", "")
            if src and src != "placeholder":
                has_concept_image = True
                concept_image_alt = block.get("alt", "the diagram")
                break

    # Detect icons in list items / smart layout items
    for block in content_blocks:
        if not isinstance(block, dict):
            continue
        items = block.get("items", [])
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            icon_name = item.get("icon_name", "")
            if icon_name and icon_name != "auto":
                has_icons = True
                break
        if has_icons:
            break

    return has_concept_image, concept_image_alt, has_icons


def _summarize_slide_content(enriched_slide: Dict[str, Any]) -> Tuple[str, int]:
    """
    Extract and summarize slide content for LLM narration context.
    Returns: (content_summary, item_count)
    """
    summary_parts = []
    item_count = 0

    gyml_content = enriched_slide.get("gyml_content", {})
    if not isinstance(gyml_content, dict):
        return "", 0

    content_blocks = gyml_content.get("contentBlocks", [])
    if not isinstance(content_blocks, list) or not content_blocks:
        return "", 0

    # Include Slide Header for context
    slide_title = str(enriched_slide.get("title") or "").strip()
    if slide_title:
        summary_parts.append(f"SLIDE TITLE: {slide_title}")

    try:
        primary_idx = int(enriched_slide.get("primary_block_index", 0))
    except (ValueError, TypeError):
        primary_idx = 0
        
    if 0 <= primary_idx < len(content_blocks):
        primary_block = content_blocks[primary_idx]
    else:
        primary_block = content_blocks[0]

    if not isinstance(primary_block, dict):
        return "\n".join(summary_parts), 0

    block_type = str(primary_block.get("type") or "").strip()
    summary_parts.append(f"PRIMARY BLOCK TYPE: {block_type}")

    # Extract items and count them
    items = primary_block.get("items", [])
    if not isinstance(items, list):
        items = []

    if block_type == "smart_layout":
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or item.get("heading") or "").strip()
            desc = str(item.get("description") or "").strip()
            if title:
                item_count += 1
                summary_parts.append(f"ITEM {item_count} (Title: {title}): {desc}")
    
    elif block_type == "comparison_table":
        # Each row (excluding header) could be a segment
        rows = primary_block.get("rows", [])
        if isinstance(rows, list):
            for row in rows:
                if isinstance(row, list):
                    item_count += 1
                    summary_parts.append(f"Comparison Row {item_count}: {' | '.join(map(str, row))}")

    elif block_type in ["numbered_list", "cyclic_process", "process_arrow"]:
        for item in items:
            if not isinstance(item, dict):
                continue
            label = str(item.get("label") or item.get("text") or item.get("title") or "").strip()
            desc = str(item.get("description") or "").strip()
            if label:
                item_count += 1
                summary_parts.append(f"STEP {item_count} ({label}): {desc}")
    
    else:
        # Fallback for simple blocks like paragraph
        text = str(primary_block.get("text") or "").strip()
        if text:
            summary_parts.append(f"Content: {text}")
            item_count = 0 # Let generate_narration_v2 handle the default

    content_summary = "\n".join(summary_parts)
    return content_summary, item_count


def _build_fallback_narration(
    enriched_slide: Dict[str, Any],
    topic: str,
    intent: str,
    has_concept_image: bool,
    concept_image_alt: str,
) -> str:
    """
    Fallback template-based narration when LLM call fails.
    Acknowledges concept image if present.
    """
    title = str(enriched_slide.get("title") or "this slide").strip()
    must_cover = enriched_slide.get("must_cover", [])
    key_facts = enriched_slide.get("key_facts", [])
    formulas = enriched_slide.get("formulas", [])
    assessment = enriched_slide.get("assessment_prompt", "")

    segments = [f"Let's look at {title}."]

    if has_concept_image:
        segments.append(f"Take a look at {concept_image_alt} shown on the slide.")

    if must_cover:
        must_cover_text = ", ".join(str(v).strip() for v in must_cover[:3] if str(v).strip())
        if must_cover_text:
            segments.append(f"Focus on {must_cover_text}.")

    if key_facts:
        key_facts_text = ", ".join(str(v).strip() for v in key_facts[:2] if str(v).strip())
        if key_facts_text:
            segments.append(f"Key facts: {key_facts_text}.")

    if formulas:
        formulas_text = ", ".join(str(v).strip() for v in formulas[:2] if str(v).strip())
        if formulas_text:
            segments.append(f"Relevant formulas: {formulas_text}.")

    if assessment:
        assessment_text = str(assessment).strip()
        if assessment_text:
            segments.append(f"Think about: {assessment_text}")

    segments.append("Connect this to the visual — it ties all these ideas together.")

    return "\n\n".join(segments)


def _extract_response_text(response: Any) -> str:
    """Extract text from common LLM response shapes used in this codebase."""
    if response is None:
        return ""

    # LangChain AIMessage-style
    content = getattr(response, "content", None)
    if isinstance(content, str):
        return content.strip()

    # Dict-style fallback
    if isinstance(response, dict):
        value = response.get("content")
        if isinstance(value, str):
            return value.strip()

    return str(response).strip()


def generate_narration_v2(
    enriched_slide: Dict[str, Any],
    topic: str,
    intent: str,
    mentalModel: str = "",
    slide_index: int = 1,
) -> str:
    """
    Generate warm, visual-aware narration for an enriched slide.

    This function is called AFTER enrich_slide_media_sync(), so concept images
    and icons are already populated in the slide.

    Args:
        enriched_slide: Slide dict with populated media (gyml_content.contentBlocks has src/icons)
        topic: Course topic (e.g., "Photosynthesis")
        intent: Teaching intent (e.g., "explain", "compare", "assess")
        mentalModel: The analogy or guiding framework to use for narration
        slide_index: Index of the current slide for context

    Returns:
        JSON string containing narration segments
    """
    # Step 1: Detect what visuals exist on the enriched slide
    has_concept_image, concept_image_alt, has_icons = _detect_concept_visuals(enriched_slide)

    # Step 2: Build visual-awareness instructions for LLM
    visual_cues = "IMPORTANT: Focus purely on explaining the concepts. DO NOT explicitly reference the frontend visual elements or the screen. Never say 'as you can see', 'shown by the icon', 'in this image', 'on this slide', or similar phrases. Teach the material directly as if having a conversation."

    # Step 3: Summarize slide content for the LLM
    content_summary, item_count = _summarize_slide_content(enriched_slide)

    # Calculate expected segments
    expected_segments = item_count if item_count > 0 else 3

    # Step 4: Attempt LLM call (prefer Groq for speed)
    slide_title = str(enriched_slide.get("title") or "the concept").strip()

    prompt = f"""You are a warm, knowledgeable teacher narrating an educational slide to a student.

INPUTS:
TOPIC: {topic}
SLIDE INDEX: {slide_index}
SLIDE TITLE: {slide_title}
TEACHING INTENT: {intent}
TEACHING STYLE OR MENTAL MODEL: {mentalModel}

SLIDE CONTENT SUMMARY:
{content_summary}

{visual_cues}

INSTRUCTIONS:
1. Content Conversion: Take the facts and concepts from the SLIDE CONTENT SUMMARY and convert them into spoken narration.
2. Introduction: The VERY FIRST segment MUST start with a human, pedagogical opening.
   - Avoid generic phrases like "Welcome to the slide," "On this page," or "Now we see."
   - Never repeat the slide title verbatim as the first words.
   - Use a 'Bridge' (connecting to the previous concept), a 'Hook' (posing a high-level question), or a 'Future Frame' (stating why this knowledge is crucial).
   - Ensure the tone is warm and conversational, opening the subtopic as if in a live tutoring session.
3. Teacher Persona & Mental Model: Strictly conform to the {mentalModel} framework.
4. Smart Depth: Use your professional judgment to decide on explanation depth. If a concept is complex or crucial, explain it in more detail. If it's a simple term or auxiliary info, keep it concise. Do NOT be generic; be specific to the facts provided.
5. Exact Segmentation: You MUST output exactly {expected_segments} segments. Each segment must map cleanly to one visual item (e.g., if there are 3 cards in the summary, provide exactly 3 segments).
6. Avoid repetition: Do not read bullet points verbatim. Explain them naturally as if in a live classroom.
7. Output MUST be ONLY valid JSON:
{{
  "narration_segments": [
    "segment 1 (intro + item 1)...",
    "segment 2 (item 2)...",
    "segment {expected_segments} (item {expected_segments})..."
  ]
}}"""

    try:
        # Try Groq first (faster, cheaper)
        try:
            client = load_groq()
        except Exception:
            # Fall back to OpenAI
            client = load_openai()

        # model_loader returns LangChain chat models in this project.
        response = client.invoke([{"role": "user", "content": prompt}])
        narration_text = _extract_response_text(response)

        # Clear fences if LLM ignored instructions
        if narration_text.startswith("```"):
            import re
            match = re.search(r"\{.*\}", narration_text, re.DOTALL)
            if match:
                narration_text = match.group(0)

        if narration_text:
            return narration_text

    except Exception as e:
        # LLM call failed; log and fall back
        print(f"[narration_v2] LLM call failed: {e}")

    # Step 5: Fallback to template-based narration
    return _build_fallback_narration(
        enriched_slide,
        topic,
        intent,
        has_concept_image,
        concept_image_alt,
    )
