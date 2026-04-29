import json
from typing import Any, Dict, List

# try:
#     from app.services.llm.model_loader import load_openai
# except ImportError:
#     from ..llm.model_loader import load_openai

# try:
#     from app.services.node.new_slide_planner import AVAILABLE_TEMPLATE_NAMES
# except ImportError:
#     from .new_slide_planner import AVAILABLE_TEMPLATE_NAMES

try:
    from app.services.node.blocks.shared.constraint_filter import SlideConstraints, select_block
except ImportError:
    from blocks.shared.constraint_filter import SlideConstraints, select_block


VALID_VISUAL_TYPES = {"image", "diagram", "chart", "illustration", "none"}
VALID_IMAGE_ROLES = {"content", "accent", "none"}
VALID_DENSITIES = {"ultra_sparse", "sparse", "balanced", "standard", "dense", "super_dense"}

CONSTRAINT_FIELDS = [
    "content_structure",
    "item_relationship",
    "target_density",
    "estimated_items",
    "allows_wide_layout",
    "requires_icons",
    "image_role",
]


# def _clean_json(raw: str) -> str:
#     return raw.replace("```json", "").replace("```", "").strip()


# def _normalize_template(template_name: str) -> str:
#     raw = (template_name or "").strip()
#     if raw in AVAILABLE_TEMPLATE_NAMES:
#         return raw
#
#     low = raw.lower()
#     for t in AVAILABLE_TEMPLATE_NAMES:
#         if low and low in t.lower():
#             return t
#     return "Icons with text"


def _fallback_designer_slides(teacher_slides: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    result = []
    for i, s in enumerate(teacher_slides):
        result.append(
            {
                "slide_ref": s.get("slide_id", f"slide_{i + 1}"),
                "selected_block_variant": "bigBullets",
                "content_angle": "overview" if i == 0 else "application",
                "intent": s.get("teaching_intent", "explain"),
                "purpose": "definition" if i == 0 else "reinforcement",
                "role": "Guide" if i == 0 else "Connect",
                "visual_required": True,
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

    # Step 1 — Read teacher blueprint
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

    # Step 2 — Build variant_history from state
    variant_history = list(state.get("variant_history", []))

    # Fallback if teacher_slides is empty
    if not teacher_slides:
        plans[sub_id] = _fallback_designer_slides(teacher_slides)
        return {
            "plans": plans,
            "variant_history": variant_history,
        }

    # Step 3 — For each teacher slide, call select_block
    merged_plans = []
    for i, teacher_slide in enumerate(teacher_slides):
        slide_id = teacher_slide.get("slide_id", f"slide_{i + 1}")

        # Warn on missing constraint fields
        for field in CONSTRAINT_FIELDS:
            if field not in teacher_slide:
                print(
                    f"[designer_slide_planning_node] WARNING: slide '{slide_id}' "
                    f"is missing constraint field '{field}' — using default."
                )

        # Normalize image_role first (needed for allows_wide_layout override)
        image_role = str(teacher_slide.get("image_role", "none")).strip().lower()
        if image_role not in VALID_IMAGE_ROLES:
            image_role = "none"

        # Normalize target_density
        density = str(teacher_slide.get("target_density", "balanced")).strip().lower()
        if density not in VALID_DENSITIES:
            density = "balanced"

        # Normalize estimated_items
        try:
            estimated_items = int(teacher_slide.get("estimated_items", 4))
            estimated_items = max(1, min(8, estimated_items))
        except (TypeError, ValueError):
            estimated_items = 4

        # Normalize allows_wide_layout; override if image_role is "content"
        allows_wide_layout = bool(teacher_slide.get("allows_wide_layout", True))
        if image_role == "content":
            allows_wide_layout = False

        # Normalize requires_icons
        requires_icons = bool(teacher_slide.get("requires_icons", False))

        constraints = SlideConstraints(
            content_structure=str(teacher_slide.get("content_structure", "list")).strip(),
            item_relationship=str(teacher_slide.get("item_relationship", "parallel")).strip(),
            target_density=density,
            estimated_items=estimated_items,
            allows_wide_layout=allows_wide_layout,
            requires_icons=requires_icons,
            image_role=image_role,
            variant_history=list(variant_history),  # pass a copy
        )

        variant_name, block_spec, profile = select_block(constraints)
        variant_history.append(variant_name)  # update history after each slide

        # Normalize visual_type
        visual_type = str(teacher_slide.get("visual_type", "image")).strip().lower()
        if visual_type not in VALID_VISUAL_TYPES:
            visual_type = "image"

        # Step 4 — Build merged plan item
        plan_item = {
            "slide_id": f"{sub_id}_s{i + 1}",
            "sequence_index": i,
            "title": teacher_slide.get("title") or f"{subtopic_name} - Slide {i + 1}",
            "goal": teacher_slide.get("objective", "Teach the concept clearly."),
            "intent": str(teacher_slide.get("intent", "concept")).strip().lower(),
            "purpose": str(teacher_slide.get("purpose", "definition")).strip().lower(),
            "role": str(teacher_slide.get("role", "Guide")).strip(),
            "content_angle": str(teacher_slide.get("content_angle", "overview")).strip().lower(),
            # Teacher constraint fields (copied directly)
            "content_structure": str(teacher_slide.get("content_structure", "list")).strip(),
            "item_relationship": str(teacher_slide.get("item_relationship", "parallel")).strip(),
            "estimated_items": estimated_items,
            "allows_wide_layout": allows_wide_layout,
            "requires_icons": requires_icons,
            # Visual fields
            "visual_required": bool(teacher_slide.get("visual_required", True)),
            "visual_type": visual_type,
            "image_role": image_role,
            "target_density": density,
            "reasoning": str(teacher_slide.get("design_reason", "Designed to fit teaching objective.")).strip(),
            # Block selection output (replaces selected_template)
            "selected_block_variant": variant_name,
            "block_constraints": {
                "item_min": profile.item_range[0],
                "item_max": profile.item_range[1],
                "requires_icons": block_spec.requires_icons,
                "width_class": profile.width_class,
                "layout_variant": profile.layout_variant,
                "height_class": profile.height_class,
                "supported_layouts": list(profile.supported_layouts),
                "combinable": profile.combinable,
            },
        }
        merged_plans.append(plan_item)

    # Step 5 — Return updated state
    plans[sub_id] = merged_plans
    return {
        "plans": plans,
        "variant_history": variant_history,
    }