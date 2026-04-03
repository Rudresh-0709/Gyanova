from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Tuple

try:
    from app.services.node.v2.density_mapping_v2 import map_brief_density_to_engine
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
    from app.services.node.v2.variety_policy_v2 import (
        family_allowed_by_hard_rule,
        family_penalty,
        smart_layout_variant_penalty,
        template_allowed_by_hard_rule,
        template_penalty,
        variant_penalty,
    )
    from app.services.node.v2.block_traits_v2 import BLOCK_TRAITS
    from app.services.node.v2.template_traits_v2 import TEMPLATE_TRAITS
except ImportError:
    from .density_mapping_v2 import map_brief_density_to_engine  # type: ignore
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
    from .variety_policy_v2 import (  # type: ignore
        family_allowed_by_hard_rule,
        family_penalty,
        smart_layout_variant_penalty,
        template_allowed_by_hard_rule,
        template_penalty,
        variant_penalty,
    )
    from .block_traits_v2 import BLOCK_TRAITS  # type: ignore
    from .template_traits_v2 import TEMPLATE_TRAITS  # type: ignore


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


def _normalize_density(value: Any, slide_index: int | None = None) -> str:
    return map_brief_density_to_engine(str(value or "medium").strip().lower(), slide_index=slide_index)


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
    # Template traits override: allow side images in dense when template explicitly supports it.
    if density in {"dense", "super_dense"}:
        traits = TEMPLATE_TRAITS.get(template_name)
        if not (traits and traits.supports_side_image_in_dense):
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


def _select_template_with_variety(
    *,
    template_candidates: List[TemplateSpec],
    primary_family: str,
    image_need: str,
    layout_history: List[str],
    variant_history: List[str],
    hard_rule_no_consecutive_template: bool,
) -> TemplateSpec:
    allowed: List[TemplateSpec] = []
    for candidate in template_candidates:
        if template_allowed_by_hard_rule(
            candidate.name,
            layout_history,
            disallow_consecutive=hard_rule_no_consecutive_template,
        ):
            allowed.append(candidate)

    pool = allowed or template_candidates
    scored: List[Tuple[float, TemplateSpec]] = []
    for candidate in pool:
        penalty = 0.0
        penalty += template_penalty(candidate.name, layout_history, window=6)
        penalty += family_penalty(primary_family, variant_history, window=6)
        penalty += variant_penalty(primary_family, "normal", variant_history, window=6)

        image_mode = str(candidate.image_mode_capability or "").strip().lower()
        if image_mode in {"accent", "content", "hero"}:
            penalty += smart_layout_variant_penalty(image_mode, variant_history, window=6)

        # Keep original intent when image is required.
        if image_need == "required" and image_mode not in {"hero", "content"}:
            penalty += 1.5

        # Template traits: strongly penalize if concept image required but template doesn't support it
        traits = TEMPLATE_TRAITS.get(candidate.name)
        if traits:
            if image_need == "required" and not traits.supports_concept_image:
                penalty += 3.0
            if image_need == "required" and traits.forbidden_if_concept_image:
                penalty += 1.0

        scored.append((penalty, candidate))

    scored.sort(key=lambda item: (item[0], item[1].name))
    return scored[0][1]


def _select_primary_family_with_variety(
    *,
    requested_family: str,
    template_spec: TemplateSpec,
    variant_history: List[str],
    hard_rule_family_cap: bool,
) -> str:
    if not template_spec.allowed_primary_families:
        return requested_family

    allowed_families = [str(family).strip().lower() for family in template_spec.allowed_primary_families if str(family).strip()]
    if not allowed_families:
        return requested_family

    candidates: List[str] = []
    for family in allowed_families:
        if (not hard_rule_family_cap) or family_allowed_by_hard_rule(
            family,
            variant_history,
            max_in_window=2,
            window=4,
        ):
            candidates.append(family)

    pool = candidates or allowed_families
    scored: List[Tuple[float, str]] = []
    for family in pool:
        penalty = family_penalty(family, variant_history, window=6) + variant_penalty(family, "normal", variant_history, window=6)
        if family != str(requested_family or "").strip().lower():
            penalty += 0.5
        scored.append((penalty, family))

    scored.sort(key=lambda item: (item[0], item[1] != str(requested_family or "").strip().lower(), item[1]))
    return scored[0][1]


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

    layout_history = list(state.get("layout_history", []))
    variant_history = list(state.get("variant_history", []))
    hard_rule_no_consecutive_template = _to_bool(state.get("v2_no_consecutive_template", True), default=True)
    hard_rule_family_cap = _to_bool(state.get("v2_family_cap_last4", True), default=True)

    subtopic_name = str(wrapper.get("_teacher_subtopic_name") or next((sub.get("name") for sub in sub_topics if sub.get("id") == target_sub_id), "Subtopic")).strip()

    normalized_plans: List[Dict[str, Any]] = []
    for index, teacher_slide in enumerate(teacher_slides):
        if not isinstance(teacher_slide, dict):
            continue

        density = _normalize_density(teacher_slide.get("slide_density"), slide_index=index)
        high_end_required = _to_bool(teacher_slide.get("high_end_image_required"), default=False)
        image_need, image_tier = _derive_image_policy(density, high_end_required)
        primary_family = _derive_primary_family(teacher_slide)

        template_candidates = candidate_templates(
            primary_family=primary_family,
            image_need=image_need,
            image_tier=image_tier,
            density=density,
        )
        template_spec = _select_template_with_variety(
            template_candidates=template_candidates,
            primary_family=primary_family,
            image_need=image_need,
            layout_history=layout_history,
            variant_history=variant_history,
            hard_rule_no_consecutive_template=hard_rule_no_consecutive_template,
        )
        selected_template = template_spec.name

        if image_need == "required" and template_spec.image_mode_capability not in {"hero", "content"}:
            for candidate in template_candidates:
                if candidate.supports_high_end_image or candidate.image_mode_capability == "hero":
                    selected_template = candidate.name
                    template_spec = candidate
                    break

        primary_family = _select_primary_family_with_variety(
            requested_family=primary_family,
            template_spec=template_spec,
            variant_history=variant_history,
            hard_rule_family_cap=hard_rule_family_cap,
        )

        primary_spec = select_primary_block(primary_family, density, image_need)
        if primary_spec.family not in template_spec.allowed_primary_families and template_spec.allowed_primary_families:
            primary_family = template_spec.allowed_primary_families[0]
            primary_spec = select_primary_block(primary_family, density, image_need)

        # Look up block traits for the resolved primary block
        primary_block_traits = BLOCK_TRAITS.get((primary_spec.family, primary_spec.variant))

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
                "primary_supports_icons": primary_block_traits.supports_icons if primary_block_traits else False,
                "primary_requires_image_prompt": primary_block_traits.requires_image_prompt if primary_block_traits else False,
                "primary_tags": list(primary_block_traits.tags) if primary_block_traits else [],
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

        layout_history.append(f"{selected_template}|{layout}")
        variant_history.append(f"{primary_spec.family}:{primary_spec.variant}")

    plans[target_sub_id] = normalized_plans
    return {"plans": plans}
