from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List

try:
    from app.services.node.v2.gyml_generator_v2 import generate_gyml_v2
except ImportError:
    from .gyml_generator_v2 import generate_gyml_v2


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
        narration_text = _build_narration_text(concept, slide_payload)
        animation_meta = _animation_metadata(slide_payload)

        layout = slide_payload.get("layout") or slide_payload.get("image_layout") or "blank"
        slide_obj = {
            **concept,
            "subtopic_name": subtopic_name,
            "narration_text": narration_text,
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
        slides_state[sub_id].append(slide_obj)

        layout_history.append(str(layout))
        angle_history.append(str(concept.get("teaching_intent", "explain")))
        template_name = str(concept.get("selected_template") or slide_payload.get("selected_template") or "Title with bullets")
        composition_history.append(template_name)
        variant_history.append(template_name)
        # Also track the smart_layout variant for fine-grained variety enforcement
        slv = str(concept.get("smart_layout_variant") or "")
        if slv:
            variant_history.append(slv)


    return {
        "slides": slides_state,
        "layout_history": layout_history,
        "angle_history": angle_history,
        "composition_history": composition_history,
        "variant_history": variant_history,
    }
