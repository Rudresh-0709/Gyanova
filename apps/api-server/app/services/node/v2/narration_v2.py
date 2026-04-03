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


def _summarize_slide_content(enriched_slide: Dict[str, Any]) -> str:
    """
    Extract and summarize slide content for LLM narration context.
    Includes: headings, smart_layout items, comparisons, formulas, process steps.
    Target: <400 tokens
    """
    summary_parts = []

    gyml_content = enriched_slide.get("gyml_content", {})
    if not isinstance(gyml_content, dict):
        return ""

    content_blocks = gyml_content.get("contentBlocks", [])
    if not isinstance(content_blocks, list):
        return ""

    for block in content_blocks:
        if not isinstance(block, dict):
            continue

        block_type = str(block.get("type") or "").strip()

        # Heading blocks
        if block_type == "heading":
            text = str(block.get("text") or "").strip()
            if text:
                summary_parts.append(f"Heading: {text}")

        # Paragraph
        elif block_type == "paragraph":
            text = str(block.get("text") or "").strip()
            if text and len(text) < 200:
                summary_parts.append(f"Text: {text}")

        # Smart layout items (cards with titles/descriptions)
        elif block_type == "smart_layout":
            items = block.get("items", [])
            if isinstance(items, list):
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    title = str(item.get("title") or "").strip()
                    desc = str(item.get("description") or "").strip()
                    if title:
                        summary_parts.append(f"Card '{title}': {desc[:100]}")

        # Comparison table
        elif block_type == "comparison_table":
            subjects = block.get("subjects", [])
            criteria = block.get("criteria", [])
            if isinstance(subjects, list) and isinstance(criteria, list):
                subj_str = ", ".join(str(s).strip() for s in subjects[:3] if s)
                crit_str = ", ".join(str(c).strip() for c in criteria[:3] if c)
                if subj_str and crit_str:
                    summary_parts.append(f"Comparison: {subj_str} on {crit_str}")

        # Formula block
        elif block_type == "formula":
            expression = str(block.get("expression") or "").strip()
            if expression and len(expression) < 100:
                summary_parts.append(f"Formula: {expression}")

        # Number list items
        elif block_type == "numbered_list":
            items = block.get("items", [])
            if isinstance(items, list):
                for i, item in enumerate(items[:3], 1):
                    if not isinstance(item, dict):
                        continue
                    text = str(item.get("text") or "").strip()
                    if text:
                        summary_parts.append(f"Step {i}: {text[:80]}")

        # Cyclic process
        elif block_type == "cyclic_process":
            items = block.get("items", [])
            if isinstance(items, list):
                for item in items[:3]:
                    if not isinstance(item, dict):
                        continue
                    label = str(item.get("label", "") or "").strip()
                    description = str(item.get("description", "") or "").strip()
                    if label:
                        summary_parts.append(f"Phase: {label} - {description[:60]}")

        # Process arrow block
        elif block_type == "process_arrow":
            items = block.get("items", [])
            if isinstance(items, list):
                for item in items[:3]:
                    if not isinstance(item, dict):
                        continue
                    label = str(item.get("label", "") or "").strip()
                    if label:
                        summary_parts.append(f"Step: {label}")

    # Limit to ~400 tokens by truncating
    content_summary = "\n".join(summary_parts[:15])
    if len(content_summary) > 1200:
        content_summary = content_summary[:1200] + "..."

    return content_summary


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
) -> str:
    """
    Generate warm, visual-aware narration for an enriched slide.

    This function is called AFTER enrich_slide_media_sync(), so concept images
    and icons are already populated in the slide.

    Args:
        enriched_slide: Slide dict with populated media (gyml_content.contentBlocks has src/icons)
        topic: Course topic (e.g., "Photosynthesis")
        intent: Teaching intent (e.g., "explain", "compare", "assess")

    Returns:
        Narration text string with segments separated by "\n\n"
    """
    # Step 1: Detect what visuals exist on the enriched slide
    has_concept_image, concept_image_alt, has_icons = _detect_concept_visuals(enriched_slide)

    # Step 2: Build visual-awareness instructions for LLM
    visual_cues = ""
    if has_concept_image:
        visual_cues += (
            f"\nIMPORTANT: This slide contains a concept image/diagram showing "
            f"'{concept_image_alt}'. Reference it naturally in your narration "
            f"(e.g., 'As you can see in the diagram...', 'Looking at this illustration...', "
            f"'The image here shows...'). Do NOT describe the image in detail — "
            f"the student can see it. Just reference and explain."
        )
    else:
        visual_cues += "\nThis slide has no concept image. Focus narration on the text content and structure."

    if has_icons:
        visual_cues += "\nThe slide includes icons to highlight key items — reference them naturally."

    # Step 3: Summarize slide content for the LLM
    content_summary = _summarize_slide_content(enriched_slide)

    # Step 4: Attempt LLM call (prefer Groq for speed)
    slide_title = str(enriched_slide.get("title") or "the concept").strip()

    prompt = f"""You are a warm, knowledgeable teacher narrating an educational slide to a student.

TOPIC: {topic}
SLIDE TITLE: {slide_title}
TEACHING INTENT: {intent}

SLIDE CONTENT SUMMARY:
{content_summary}

{visual_cues}

INSTRUCTIONS:
1. Structure: Hook (1 sentence) → Explain (2-4 sentences with transitions) → Recap/Question (1 sentence).
2. Tone: Conversational but precise. Like a patient tutor, not a textbook.
3. Transitions: Use "First... Next... Finally..." or "Notice how... This means..."
4. Length: 80–150 words total. Split into 3–5 segments separated by double newlines.
5. Do NOT repeat the slide title verbatim. Do NOT list bullet points — explain them.
6. Each segment should map roughly to one visual element on the slide (one card, one step, etc.)

Output narration text only. No JSON. No markdown. Segments separated by double newlines (\\n\\n)."""

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

        # Ensure segments are separated by double newlines
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
