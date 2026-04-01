from copy import deepcopy
from typing import Any, Dict, List

try:
    from app.services.node.content_generation_node import content_generation_node
except ImportError:
    from .content_generation_node import content_generation_node


def _join_limited(values: List[str], max_items: int = 4) -> str:
    cleaned = [str(v).strip() for v in values if str(v).strip()]
    return "; ".join(cleaned[:max_items])


def _enrich_goal(plan_item: Dict[str, Any]) -> str:
    base_goal = str(plan_item.get("goal", "Explain the concept clearly.")).strip()
    teacher = plan_item.get("teacher", {})
    teaching_intent = str(teacher.get("teaching_intent", "explain")).strip().lower()
    coverage_scope = str(teacher.get("coverage_scope", "foundation")).strip().lower()
    assessment_prompt = str(teacher.get("assessment_prompt", "")).strip()

    must_cover = _join_limited(teacher.get("must_cover", []), max_items=5)
    facts = _join_limited(teacher.get("key_facts", []), max_items=3)
    formulas = _join_limited(teacher.get("formulas", []), max_items=3)
    examples = _join_limited(teacher.get("examples", []), max_items=2)
    misconceptions = _join_limited(teacher.get("misconceptions", []), max_items=1)

    parts = [
        base_goal,
        f"Teaching intent: {teaching_intent}.",
        f"Coverage scope: {coverage_scope}.",
        "Stay within this slide's teaching scope and avoid repeating prior-slide content unless required for brief recap.",
    ]
    if must_cover:
        parts.append(f"Must cover: {must_cover}.")
    if facts:
        parts.append(f"Important facts: {facts}.")
    if formulas:
        parts.append(f"Include formulas when relevant: {formulas}.")
    if examples:
        parts.append(f"Include examples: {examples}.")
    if misconceptions:
        parts.append(f"Address misconception: {misconceptions}.")
    if assessment_prompt:
        parts.append(f"Comprehension check to support: {assessment_prompt}.")
    parts.append("Write content in teacher voice: clear, accurate, student-friendly, and instructionally progressive.")

    enriched = " ".join(parts)
    return enriched[:1200]


def content_generation_v2_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Experimental v2 content generation wrapper.
    - Preserves existing output contract.
    - Enriches per-slide goal text using teacher blueprint metadata.
    - Delegates final generation to stable v1 content generation node.
    """
    local_state = deepcopy(state)

    plans = local_state.get("plans", {})
    for sub_id, slide_plans in plans.items():
        for plan_item in slide_plans:
            if isinstance(plan_item, dict):
                plan_item["goal"] = _enrich_goal(plan_item)

    local_state["plans"] = plans
    return content_generation_node(local_state)
