from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List

try:
    from app.services.node.v2.gyml_generator_v2 import generate_gyml_v2
    from app.services.media.enrichment_service_sync import enrich_slide_media_sync
    from app.services.node.v2.narration_v2 import generate_narration_v2
except ImportError:
    from .gyml_generator_v2 import generate_gyml_v2
    from ..media.enrichment_service_sync import enrich_slide_media_sync
    from .narration_v2 import generate_narration_v2


def _build_narration_text(plan_item: Dict[str, Any], slide: Dict[str, Any]) -> str:
    title = str(slide.get("title") or plan_item.get("title") or "this slide").strip()
    must_cover = [str(v).strip() for v in plan_item.get("must_cover", []) if str(v).strip()]
    key_facts = [str(v).strip() for v in plan_item.get("key_facts", []) if str(v).strip()]
    formulas = [str(v).strip() for v in plan_item.get("formulas", []) if str(v).strip()]
    assessment = str(plan_item.get("assessment_prompt") or "").strip()

    segments = [f"We are looking at {title}."]
    if must_cover:
        segments.append(f"Focus on {', '.join(must_cover[:4])}.")
    if key_facts:
        segments.append(f"Remember these facts: {', '.join(key_facts[:3])}.")
    if formulas:
        segments.append(f"Relevant formulas include {', '.join(formulas[:2])}.")
    if assessment:
        segments.append(f"Check understanding by asking: {assessment}.")
    segments.append("Keep the explanation short, clear, and connected to the visual.")
    return "\n\n".join(segments)


def _animation_metadata(slide: Dict[str, Any]) -> Dict[str, Any]:
    blocks = slide.get("contentBlocks", []) if isinstance(slide.get("contentBlocks"), list) else []
    primary_index = int(slide.get("primary_block_index", 0) or 0)
    return {
        "animation_unit": "block",
        "animation_unit_count": max(1, len(blocks)),
        "animated_block_index": primary_index,
    }


def _smart_layout_variant_tokens(slide: Dict[str, Any]) -> List[str]:
    blocks = slide.get("contentBlocks", []) if isinstance(slide.get("contentBlocks"), list) else []
    tokens: List[str] = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        if str(block.get("type") or "").strip().lower() != "smart_layout":
            continue
        variant = str(block.get("variant") or "").strip()
        if variant:
            tokens.append(f"smart_layout:{variant}")
    return tokens


def content_generation_v2_node(state: Dict[str, Any]) -> Dict[str, Any]:
    sub_topics = state.get("sub_topics", [])
    plans = state.get("plans", {})
    slides_state = deepcopy(state.get("slides", {}))

    layout_history = list(state.get("layout_history", []))
    angle_history = list(state.get("angle_history", []))
    composition_history = list(state.get("composition_history", []))
    variant_history = list(state.get("variant_history", []))

    next_subtopic = None
    start_offset = 0
    for sub in sub_topics:
        sub_id = sub.get("id")
        planned_count = len(plans.get(sub_id, []))
        generated_count = len(slides_state.get(sub_id, [])) if isinstance(slides_state.get(sub_id, []), list) else 0
        if generated_count < planned_count:
            next_subtopic = sub
            start_offset = generated_count
            break

    if not next_subtopic:
        return {
            "slides": slides_state,
            "layout_history": layout_history,
            "angle_history": angle_history,
            "composition_history": composition_history,
            "variant_history": variant_history,
        }

    sub_id = next_subtopic.get("id")
    subtopic_name = next_subtopic.get("name", "Subtopic")
    slide_concepts = plans.get(sub_id, [])
    if sub_id not in slides_state:
        slides_state[sub_id] = []

    for index in range(start_offset, len(slide_concepts)):
        concept = slide_concepts[index]
        if not isinstance(concept, dict):
            continue

        slide_payload = generate_gyml_v2(concept)
        animation_meta = _animation_metadata(slide_payload)

        layout = slide_payload.get("layout") or slide_payload.get("image_layout") or "blank"
        slide_obj = {
            **concept,
            "subtopic_name": subtopic_name,
            "narration_text": "",  # Will be populated after enrichment
            "narration_format": "points",
            "gyml_content": slide_payload,
            "visual_content": slide_payload,
            "layout": layout,
            "image_layout": slide_payload.get("image_layout") or layout,
            "primary_block_index": slide_payload.get("primary_block_index", 0),
            "slide_density": concept.get("slide_density", "balanced"),
            "animation_unit": animation_meta["animation_unit"],
            "animation_unit_count": animation_meta["animation_unit_count"],
            "animated_block_index": animation_meta["animated_block_index"],
        }

        # Step 1: Enrich slide with media assets (images, diagrams, icons) BEFORE narration
        topic = state.get("topic", "")
        image_layout = slide_obj.get("image_layout", layout)
        enrich_slide_media_sync(slide_obj, topic=topic, image_layout=image_layout)

        # Step 2: Generate narration AFTER enrichment (narration sees populated visuals)
        intent = str(concept.get("teaching_intent", "explain")).strip()
        narration_text = generate_narration_v2(slide_obj, topic=topic, intent=intent)
        slide_obj["narration_text"] = narration_text

        # Step 3: Append enriched slide with narration to state
        slides_state[sub_id].append(slide_obj)

        template_name = str(concept.get("selected_template") or slide_payload.get("selected_template") or "Title with bullets").strip()
        image_layout = str(slide_payload.get("image_layout") or layout).strip().lower()
        layout_history.append(f"{template_name}|{image_layout}")
        angle_history.append(str(concept.get("teaching_intent", "explain")))
        composition_history.append(template_name)

        primary_block = concept.get("designer_blueprint", {}).get("primary_block", {}) if isinstance(concept.get("designer_blueprint"), dict) else {}
        family = str(primary_block.get("family") or "overview").strip()
        variant = str(primary_block.get("variant") or "normal").strip()
        variant_history.append(f"{family}:{variant}")
        variant_history.extend(_smart_layout_variant_tokens(slide_payload))

    return {
        "slides": slides_state,
        "layout_history": layout_history,
        "angle_history": angle_history,
        "composition_history": composition_history,
        "variant_history": variant_history,
    }
