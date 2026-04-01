import json
from typing import Any, Dict, List

try:
    from app.services.llm.model_loader import load_openai
except ImportError:
    from ..llm.model_loader import load_openai

try:
    from app.services.node.new_slide_planner import AVAILABLE_TEMPLATE_NAMES
except ImportError:
    from .new_slide_planner import AVAILABLE_TEMPLATE_NAMES


VALID_VISUAL_TYPES = {"image", "diagram", "chart", "illustration", "none"}
VALID_IMAGE_ROLES = {"content", "accent", "none"}
VALID_DENSITIES = {"ultra_sparse", "sparse", "balanced", "standard", "dense", "super_dense"}


def _clean_json(raw: str) -> str:
    return raw.replace("```json", "").replace("```", "").strip()


def _normalize_template(template_name: str) -> str:
    raw = (template_name or "").strip()
    if raw in AVAILABLE_TEMPLATE_NAMES:
        return raw

    low = raw.lower()
    for t in AVAILABLE_TEMPLATE_NAMES:
        if low and low in t.lower():
            return t
    return "Icons with text"


def _fallback_designer_slides(teacher_slides: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    fallback_templates = [
        "Title with bullets",
        "Process arrow block",
        "Icons with text",
        "Comparison table",
        "Timeline",
    ]
    result = []
    for i, s in enumerate(teacher_slides):
        t = fallback_templates[i % len(fallback_templates)]
        result.append(
            {
                "slide_ref": s.get("slide_id", f"slide_{i + 1}"),
                "selected_template": t,
                "content_angle": "overview" if i == 0 else "application",
                "intent": s.get("teaching_intent", "explain"),
                "purpose": "definition" if i == 0 else "reinforcement",
                "role": "Guide" if i == 0 else "Connect",
                "visual_required": t not in {"Comparison table", "Formula block", "Key-Value list"},
                "visual_type": "image",
                "image_role": "accent",
                "target_density": "standard",
                "design_reason": "Fallback design mapping from teacher blueprint.",
            }
        )
    return result


def designer_slide_planning_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Turn teacher-first blueprints into visually diverse plan items for one subtopic."""
    sub_topics = state.get("sub_topics", [])
    plans = state.get("plans", {})

    target_subtopic = None
    teacher_slides = []
    for sub in sub_topics:
        sub_id = sub.get("id")
        plan_entry = plans.get(sub_id)
        if (
            isinstance(plan_entry, list)
            and len(plan_entry) == 1
            and isinstance(plan_entry[0], dict)
            and "_teacher_blueprint" in plan_entry[0]
        ):
            target_subtopic = sub
            teacher_slides = plan_entry[0].get("_teacher_blueprint", [])
            break

    if not target_subtopic:
        return {"plans": plans}

    sub_id = target_subtopic.get("id")
    subtopic_name = target_subtopic.get("name", "Subtopic")

    teacher_json = json.dumps(teacher_slides, ensure_ascii=True)
    templates_json = json.dumps(AVAILABLE_TEMPLATE_NAMES, ensure_ascii=True)

    prompt = f"""
You are a senior instructional designer converting teacher blueprints into visual planning metadata.

Subtopic: {subtopic_name}
Teacher blueprint slides (JSON):
{teacher_json}

Available templates:
{templates_json}

Design intent:
1. Preserve each teacher slide's objective and teaching intent exactly.
2. Make each slide look visually distinct from adjacent slides.
3. Choose template, density, and image role to support comprehension.
4. Keep visual flow engaging while matching the teaching progression.

Decision heuristics:
- Mechanism/process -> process-oriented or timeline-like templates.
- Comparison objectives -> comparison templates.
- Formula-heavy content -> formula or structured explanatory templates.
- Intro/foundation -> simpler and cleaner density.
- Reinforcement/recap -> summary-friendly template.

Output rules:
- Return one design record for each teacher slide_ref.
- No markdown, no prose outside JSON.
- design_reason must be short and specific.

Output JSON only:
{{
    "slides": [
        {{
            "slide_ref": "<teacher slide_id>",
            "selected_template": "...",
            "content_angle": "overview|mechanism|example|comparison|application|visualization|summary",
            "intent": "concept|definition|process|comparison|data|example|summary|intuition",
            "purpose": "definition|intuition|process|comparison|visualization|reinforcement|assessment",
            "role": "Introduce|Interpret|Guide|Contrast|Emphasize|Connect|Reinforce|Question",
            "visual_required": true,
            "visual_type": "image|diagram|chart|illustration|none",
            "image_role": "content|accent|none",
            "target_density": "ultra_sparse|sparse|balanced|standard|dense|super_dense",
            "design_reason": "short reason"
        }}
    ]
}}
"""

    slides = []
    try:
        llm = load_openai()
        resp = llm.invoke([{"role": "user", "content": prompt}])
        data = json.loads(_clean_json(resp.content))
        slides = data.get("slides", [])
    except Exception:
        slides = _fallback_designer_slides(teacher_slides)

    if not slides:
        slides = _fallback_designer_slides(teacher_slides)

    teacher_by_ref = {s.get("slide_id"): s for s in teacher_slides}
    merged_plans = []
    for i, d in enumerate(slides):
        ref = d.get("slide_ref")
        teacher = teacher_by_ref.get(ref) or teacher_slides[min(i, len(teacher_slides) - 1)]

        visual_type = str(d.get("visual_type", "image")).strip().lower()
        if visual_type not in VALID_VISUAL_TYPES:
            visual_type = "image"

        image_role = str(d.get("image_role", "accent")).strip().lower()
        if image_role not in VALID_IMAGE_ROLES:
            image_role = "accent"

        density = str(d.get("target_density", "standard")).strip().lower()
        if density not in VALID_DENSITIES:
            density = "standard"

        plan_item = {
            "slide_id": f"{sub_id}_s{i + 1}",
            "sequence_index": i,
            "title": teacher.get("title") or f"{subtopic_name} - Slide {i + 1}",
            "goal": teacher.get("objective", "Teach the concept clearly."),
            "intent": str(d.get("intent", "concept")).strip().lower(),
            "purpose": str(d.get("purpose", "definition")).strip().lower(),
            "role": str(d.get("role", "Guide")).strip(),
            "content_angle": str(d.get("content_angle", "overview")).strip().lower(),
            "selected_template": _normalize_template(str(d.get("selected_template", "Icons with text"))),
            "visual_required": bool(d.get("visual_required", True)),
            "visual_type": visual_type,
            "image_role": image_role,
            "target_density": density,
            "reasoning": str(d.get("design_reason", "Designed to fit teaching objective.")).strip(),
        }
        merged_plans.append(plan_item)

    plans[sub_id] = merged_plans
    return {"plans": plans}
