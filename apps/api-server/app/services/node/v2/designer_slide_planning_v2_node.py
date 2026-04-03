from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Tuple

try:
    from app.services.node.v2.block_catalog_v2 import (
        block_to_blueprint,
        select_primary_block,
        select_supporting_blocks,
    )
    from app.services.node.v2.template_registry_v2 import (
        TemplateSpec,
        candidate_templates,
        get_template_spec,
        template_allows_layout,
    )
except ImportError:
    from .block_catalog_v2 import (  # type: ignore
        block_to_blueprint,
        select_primary_block,
        select_supporting_blocks,
    )
    from .template_registry_v2 import (  # type: ignore
        TemplateSpec,
        candidate_templates,
        get_template_spec,
        template_allows_layout,
    )


VALID_DENSITIES = {"ultra_sparse", "sparse", "balanced", "standard", "dense", "super_dense"}


def _to_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"true", "yes", "1", "y"}:
        return True
    if text in {"false", "no", "0", "n"}:
        return False
    return default


def _to_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    text = str(value).strip()
    return [text] if text else []


def _normalize_density(value: Any) -> str:
    density = str(value or "balanced").strip().lower()
    if density not in VALID_DENSITIES:
        return "balanced"
    return density


def _derive_image_policy(density: str, high_end_image_required: bool) -> Tuple[str, str]:
    if high_end_image_required:
        return "required", "hero"
    if density in {"ultra_sparse", "sparse", "balanced"}:
        return "optional", "accent"
    return "forbidden", "none"


def _derive_primary_family(teacher_slide: Dict[str, Any]) -> str:
    teaching_intent = str(teacher_slide.get("teaching_intent", "explain")).strip().lower()
    coverage_scope = str(teacher_slide.get("coverage_scope", "foundation")).strip().lower()
    formulas = _to_list(teacher_slide.get("formulas"))
    if formulas:
        return "formula"
    if coverage_scope == "comparison" or teaching_intent == "compare":
        return "comparison"
    if coverage_scope == "mechanism" or teaching_intent in {"teach", "demo"}:
        return "process"
    if coverage_scope == "reinforcement" or teaching_intent == "summarize":
        return "recap"
    if coverage_scope == "application":
        return "overview"
    return "overview"


def _choose_layout(template_name: str, image_need: str, image_tier: str, density: str, index: int) -> str:
    spec = get_template_spec(template_name)
    if image_need == "forbidden" or image_tier == "none":
        return "blank" if "blank" in spec.allowed_layouts else (spec.allowed_layouts[0] if spec.allowed_layouts else "blank")

    if image_tier == "hero":
        for preferred in ("top", "bottom", "right", "left", "blank"):
            if preferred in spec.allowed_layouts:
                return preferred

    # Accent policy: keep optional images off dense slides by default.
    if density in {"dense", "super_dense"}:
        if "blank" in spec.allowed_layouts:
            return "blank"
    accent_choices = ["right", "left", "top", "bottom"]
    for preferred in accent_choices[index % len(accent_choices):] + accent_choices[: index % len(accent_choices)]:
        if preferred in spec.allowed_layouts:
            return preferred

    return "blank" if "blank" in spec.allowed_layouts else (spec.allowed_layouts[0] if spec.allowed_layouts else "blank")


def _build_designer_blueprint(
    *,
    teacher_slide: Dict[str, Any],
    selected_template: str,
    primary_family: str,
    primary_block: Dict[str, Any],
    supporting_blocks: List[Dict[str, Any]],
    image_need: str,
    image_tier: str,
    layout: str,
) -> Dict[str, Any]:
    template = get_template_spec(selected_template)
    return {
        "template": {
            "name": template.name,
            "is_sparse": template.is_sparse,
            "image_mode_capability": template.image_mode_capability,
            "image_mode_required": template.image_mode_required,
            "max_blocks": template.max_blocks,
            "max_supporting_blocks": template.max_supporting_blocks,
            "allowed_primary_families": list(template.allowed_primary_families),
            "allowed_accent_placements": list(template.allowed_accent_placements),
            "allowed_layouts": list(template.allowed_layouts),
            "supports_high_end_image": template.supports_high_end_image,
        },
        "primary_block": primary_block,
        "supporting_blocks": supporting_blocks,
        "image_need": image_need,
        "image_tier": image_tier,
        "layout": layout,
        "primary_family": primary_family,
        "notes": [
            f"Teacher intent: {teacher_slide.get('teaching_intent', 'explain')}",
            f"Coverage scope: {teacher_slide.get('coverage_scope', 'foundation')}",
        ],
    }


def designer_slide_planning_v2_node(state: Dict[str, Any]) -> Dict[str, Any]:
    plans = deepcopy(state.get("plans", {}))
    sub_topics = state.get("sub_topics", [])

    target_sub_id = None
    wrapper = None
    for sub in sub_topics:
        sub_id = sub.get("id")
        current = plans.get(sub_id)
        if (
            isinstance(current, list)
            and len(current) == 1
            and isinstance(current[0], dict)
            and "_teacher_blueprint" in current[0]
        ):
            target_sub_id = sub_id
            wrapper = current[0]
            break

    if not target_sub_id or not wrapper:
        return {"plans": plans}

    teacher_slides = wrapper.get("_teacher_blueprint", [])
    if not isinstance(teacher_slides, list):
        return {"plans": plans}

    subtopic_name = str(wrapper.get("_teacher_subtopic_name") or next((sub.get("name") for sub in sub_topics if sub.get("id") == target_sub_id), "Subtopic")).strip()

    normalized_plans: List[Dict[str, Any]] = []
    for index, teacher_slide in enumerate(teacher_slides):
        if not isinstance(teacher_slide, dict):
            continue

        density = _normalize_density(teacher_slide.get("slide_density"))
        high_end_required = _to_bool(teacher_slide.get("high_end_image_required"), default=False)
        image_need, image_tier = _derive_image_policy(density, high_end_required)
        primary_family = _derive_primary_family(teacher_slide)

        template_candidates = candidate_templates(
            primary_family=primary_family,
            image_need=image_need,
            image_tier=image_tier,
            density=density,
        )
        selected_template = template_candidates[0].name
        template_spec = get_template_spec(selected_template)

        if image_need == "required" and template_spec.image_mode_capability not in {"hero", "content"}:
            for candidate in template_candidates:
                if candidate.supports_high_end_image or candidate.image_mode_capability == "hero":
                    selected_template = candidate.name
                    template_spec = candidate
                    break

        primary_spec = select_primary_block(primary_family, density, image_need)
        if primary_spec.family not in template_spec.allowed_primary_families and template_spec.allowed_primary_families:
            primary_family = template_spec.allowed_primary_families[0]
            primary_spec = select_primary_block(primary_family, density, image_need)

        supporting_specs = select_supporting_blocks(
            family=primary_family,
            density=density,
            max_supporting_blocks=template_spec.max_supporting_blocks,
        )
        if template_spec.is_sparse:
            supporting_specs = supporting_specs[:1]

        if image_need == "forbidden":
            supporting_specs = [spec for spec in supporting_specs if not spec.has_content_image]
        elif image_tier == "hero":
            supporting_specs = [spec for spec in supporting_specs if not spec.has_content_image]

        if image_need != "forbidden" and not template_allows_layout(selected_template, "blank"):
            layout = next((layout_name for layout_name in template_spec.allowed_layouts if layout_name != "blank"), "blank")
        else:
            layout = _choose_layout(selected_template, image_need, image_tier, density, index)

        # Avoid content-image/supporting-image collision by design.
        if image_tier in {"hero", "accent"}:
            supporting_specs = [spec for spec in supporting_specs if not spec.implies_content_image]

        teacher_slide_ref = str(teacher_slide.get("slide_id") or f"{target_sub_id}_t{index + 1}")
        normalized_plans.append(
            {
                "slide_id": teacher_slide_ref,
                "teacher_slide_ref": teacher_slide_ref,
                "sequence_index": index,
                "title": str(teacher_slide.get("title") or f"{subtopic_name} - Slide {index + 1}").strip(),
                "objective": str(teacher_slide.get("objective") or "Explain the concept clearly.").strip(),
                "teaching_intent": str(teacher_slide.get("teaching_intent") or "explain").strip().lower(),
                "coverage_scope": str(teacher_slide.get("coverage_scope") or "foundation").strip().lower(),
                "slide_density": density,
                "must_cover": _to_list(teacher_slide.get("must_cover")),
                "key_facts": _to_list(teacher_slide.get("key_facts")),
                "formulas": _to_list(teacher_slide.get("formulas")),
                "assessment_prompt": str(teacher_slide.get("assessment_prompt") or "").strip(),
                "research_evidence": _to_list(teacher_slide.get("research_evidence")),
                "research_raw_text": str(teacher_slide.get("research_raw_text") or "").strip(),
                "factual_confidence": str(teacher_slide.get("factual_confidence") or "low").strip().lower(),
                "high_end_image_required": high_end_required,
                "image_need": image_need,
                "image_tier": image_tier,
                "selected_template": selected_template,
                "selected_layout": layout,
                "designer_blueprint": _build_designer_blueprint(
                    teacher_slide=teacher_slide,
                    selected_template=selected_template,
                    primary_family=primary_spec.family,
                    primary_block=block_to_blueprint(primary_spec),
                    supporting_blocks=[block_to_blueprint(spec) for spec in supporting_specs],
                    image_need=image_need,
                    image_tier=image_tier,
                    layout=layout,
                ),
            }
        )

    plans[target_sub_id] = normalized_plans
    return {"plans": plans}
