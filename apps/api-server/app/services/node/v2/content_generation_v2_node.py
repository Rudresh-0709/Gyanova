from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List

try:
    from app.services.node.v2.gyml_generator_v2 import generate_gyml_v2
    from app.services.node.v2.research_context_v2 import build_research_context
    from app.services.node.v2.hallucination_guard_v2 import check_slide
    from app.services.node.v2.media_enricher_v2 import enrich_slide_media_sync
    from app.services.node.v2.narration_v2 import generate_narration_v2
except ImportError:
    from .gyml_generator_v2 import generate_gyml_v2
    from .research_context_v2 import build_research_context
    from .hallucination_guard_v2 import check_slide
    from .media_enricher_v2 import enrich_slide_media_sync
    from .narration_v2 import generate_narration_v2
import json
import time


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

    # Count the actual items that will receive data-segment attributes in the
    # renderer.  Only items inside animated block types (smart_layout, process
    # arrows, hub-and-spoke, etc.) are stamped — NOT headings or paragraphs.
    # This count MUST match the number of data-segment elements the renderer
    # produces, otherwise getRevealIndexForSegment's proportional mapping will
    # skip or double-up cards.
    ANIMATED_BLOCK_TYPES = {
        "smart_layout",
        "hub_and_spoke",
        "process_arrow_block",
        "cyclic_process_block",
        "cyclic_block",
        "feature_showcase_block",
        "sequential_output",
    }

    item_count = 0
    for block in blocks:
        if not isinstance(block, dict):
            continue
        block_type = str(block.get("type") or "").strip().lower()
        # smart_layout routes some variants to dedicated GyML classes that
        # also produce data-segment — count their items too.
        variant = str(block.get("variant") or "").strip().lower()
        items = block.get("items", [])
        n_items = len(items) if isinstance(items, list) else 0

        if block_type == "smart_layout" and variant in {
            "hubandspoke", "featureshowcase", "cyclicblock", "sequentialoutput",
        }:
            item_count += n_items
            print(f"  [ANIM] Counted {n_items} items from {block_type} (variant={variant})")
        elif block_type in ANIMATED_BLOCK_TYPES:
            item_count += n_items
            print(f"  [ANIM] Counted {n_items} items from {block_type} (variant={variant})")
        else:
            print(f"  [ANIM] Skipped block type={block_type} variant={variant} (not animated)")

    final_count = max(1, item_count)
    print(f"  [ANIM] Final animation_unit_count={final_count} (raw item_count={item_count})")

    return {
        "animation_unit": "item",
        "animation_unit_count": final_count,
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

    # Build global research context once per node invocation (bounded to 8,000 chars).
    global_research_context = build_research_context(state)
    global_grounding_mode = "soft_grounded" if global_research_context else "general_knowledge"

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

        # Inject global research context when the per-slide planner did not provide one.
        # Shallow copy is safe here: research_context is always a string (immutable).
        concept = dict(concept)  # avoid mutating shared plan dicts
        if not concept.get("research_context"):
            concept["research_context"] = global_research_context
        slide_grounding_mode = "soft_grounded" if concept.get("research_context") else global_grounding_mode
        concept["grounding_mode"] = slide_grounding_mode

        t_gyml_start = time.time()
        slide_payload = generate_gyml_v2(concept)
        t_gyml = time.time() - t_gyml_start

        # Apply hallucination guard in general_knowledge mode (non-destructive flag scan).
        if slide_grounding_mode == "general_knowledge":
            slide_payload = check_slide(slide_payload, redact=False)

        layout = slide_payload.get("layout") or slide_payload.get("image_layout") or "blank"
        slide_obj = {
            **concept,
            "subtopic_name": subtopic_name,
            "narration_text": "",
            "narration_format": "points",
            "gyml_content": slide_payload,
            "visual_content": slide_payload,
            "layout": layout,
            "image_layout": slide_payload.get("image_layout") or layout,
            "primary_block_index": slide_payload.get("primary_block_index", 0),
            "slide_density": concept.get("slide_density", "balanced"),
            "animation_unit": "block",
            "animation_unit_count": 1,
            "animated_block_index": 0,
            # Grounding / research debug fields
            "grounding_mode": slide_grounding_mode,
            "had_research_context": bool(concept.get("research_context")),
            "hallucination_risk_score": slide_payload.get("hallucination_risk_score", 0),
        }

        # Mirror v1-style icon robustness by enriching media/icons after generation.
        # This fills missing icon_name values and keeps GyML/visual payloads synchronized.
        t_media_start = time.time()
        try:
            slide_obj = enrich_slide_media_sync(
                slide_obj,
                topic=str(state.get("topic") or state.get("user_input") or subtopic_name),
                image_layout=str(slide_obj.get("image_layout") or layout),
            )
        except Exception:
            # Never block slide generation on enrichment errors.
            pass
        t_media = time.time() - t_media_start

        slide_obj["_perf"] = {
            "gyml": round(t_gyml, 2),
            "media": round(t_media, 2)
        }

        enriched_payload = slide_obj.get("gyml_content", slide_payload)
        
        # LLM Narration V2
        try:
            narration_raw = generate_narration_v2(
                enriched_slide=slide_obj,
                topic=str(state.get("topic") or state.get("user_input") or subtopic_name),
                intent=str(concept.get("teaching_intent", "explain")),
                mentalModel=str(state.get("preferred_method") or state.get("narration_style") or "").strip(),
                slide_index=index + 1
            )
            narration_data = json.loads(narration_raw)
            segments = narration_data.get("narration_segments", [])
            if not isinstance(segments, list) or not segments:
                raise ValueError("narration_segments missing or empty")
            slide_obj["narration_text"] = "\n\n".join(segments)
        except Exception as e:
            # Fallback
            print(f"[content_generation_v2] Narration JSON parse failed: {e}")
            fallback_text = _build_narration_text(concept, enriched_payload)
            slide_obj["narration_text"] = fallback_text

        animation_meta = _animation_metadata(enriched_payload)
        slide_obj["animation_unit"] = animation_meta["animation_unit"]
        slide_obj["animation_unit_count"] = animation_meta["animation_unit_count"]
        slide_obj["animated_block_index"] = animation_meta["animated_block_index"]
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

        # Break after one slide to yield state back to LangGraph, enabling slide-by-slide streaming!
        break


    return {
        "slides": slides_state,
        "layout_history": layout_history,
        "angle_history": angle_history,
        "composition_history": composition_history,
        "variant_history": variant_history,
    }
