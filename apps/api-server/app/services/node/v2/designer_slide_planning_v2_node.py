from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple

try:
    from app.services.node.v2.block_catalog_v2 import (
        BLOCK_CATALOG,
        BlockSpec,
        block_to_blueprint,
        get_block_spec,
        get_smart_layout_variant,
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
        pick_smart_layout_variant,
        rank_templates,
    )
    from app.services.node.v2.image_manager_adapter_v2 import determine_image_layout_v2
except ImportError:
    from .block_catalog_v2 import (  # type: ignore
        BLOCK_CATALOG,
        BlockSpec,
        block_to_blueprint,
        get_block_spec,
        get_smart_layout_variant,
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
        pick_smart_layout_variant,
        rank_templates,
    )
    from .image_manager_adapter_v2 import determine_image_layout_v2  # type: ignore


VALID_DENSITIES = {"ultra_sparse", "sparse", "balanced", "standard", "dense", "super_dense"}

# Density aliases – map coarse descriptors onto the 6-level system.
_DENSITY_ALIAS: Dict[str, str] = {
    "low": "sparse",
    "medium": "balanced",
    "high": "standard",
    "very_high": "dense",
    "max": "super_dense",
}

_COMPOSITION_STYLE_ORDER: Tuple[str, ...] = (
    "primary_only",
    "context_then_primary",
    "primary_then_callout",
    "intro_then_primary",
)


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
    raw = str(value or "balanced").strip().lower()
    # Apply alias mapping first, then validate
    density = _DENSITY_ALIAS.get(raw, raw)
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
    """Map teacher intent/scope to a primary block family."""
    teaching_intent = str(teacher_slide.get("teaching_intent", "explain")).strip().lower()
    coverage_scope = str(teacher_slide.get("coverage_scope", "foundation")).strip().lower()
    formulas = _to_list(teacher_slide.get("formulas"))

    if formulas:
        return "formula"
    if coverage_scope == "comparison" or teaching_intent == "compare":
        return "smart_layout"
    if coverage_scope in {"mechanism", "sequence"} or teaching_intent in {"teach", "demo", "narrate"}:
        return "smart_layout"
    if coverage_scope == "reinforcement" or teaching_intent == "summarize":
        return "smart_layout"
    # Default: smart_layout is the richest general-purpose primary family
    return "smart_layout"


def _available_primary_smart_layout_variants(density: str) -> List[str]:
    """Return primary-eligible smart_layout variants that support the given density."""
    density_key = str(density or "balanced").strip().lower()
    variants: List[str] = []
    for spec in BLOCK_CATALOG.values():
        if spec.family != "smart_layout" or not spec.is_primary_candidate:
            continue
        if spec.density_ok and density_key not in spec.density_ok:
            continue
        name = str(spec.smart_layout_variant or spec.variant).strip()
        if name:
            variants.append(name)
    return sorted(set(variants))


def _choose_layout(
    template_name: str,
    image_need: str,
    image_tier: str,
    density: str,
    layout_history: List[str],
    primary_spec: BlockSpec,
) -> str:
    # Delegate to determine_image_layout_v2 which now handles width-based rules
    return determine_image_layout_v2(
        engine_density=density,
        intent="explain", # intent fallback
        slide_index=len(layout_history),
        has_wide_block=(primary_spec.width_class == "wide"),
        layout_history=layout_history,
        explicit_layout=None,
        allowed_layouts=get_template_spec(template_name).allowed_layouts,
    )


def _pick_composition_style(
    *,
    style_history: List[str],
    template: TemplateSpec,
    image_need: str,
) -> str:
    """
    Pick a composition style with recency-aware rotation.

    Rules:
      - Rotate across style families to avoid repetitive 3-block patterns.
      - Sparse/image-heavy slides bias toward lighter compositions.
      - Never force intro+callout on the same slide (handled in generator too).
    """
    allowed_styles = list(_COMPOSITION_STYLE_ORDER)

    # Sparse or hero/content-image-focused slides should stay compact.
    if template.is_sparse or image_need == "required":
        allowed_styles = [
            style
            for style in allowed_styles
            if style in {"primary_only", "context_then_primary", "intro_then_primary"}
        ]

    if not allowed_styles:
        return "primary_only"

    recent_window = style_history[-4:]
    recent_set = set(recent_window)
    previous_style = style_history[-1] if style_history else ""

    scored: List[Tuple[int, int, int, str]] = []
    for order_idx, style in enumerate(allowed_styles):
        recent_count = sum(1 for token in recent_window if token == style)
        immediate_repeat = 1 if style == previous_style else 0
        not_recent_bonus = 0 if style in recent_set else -1
        scored.append((recent_count, immediate_repeat, not_recent_bonus, style))

    scored.sort(key=lambda item: (item[0], item[1], item[2], allowed_styles.index(item[3])))
    return scored[0][3]


def _build_designer_blueprint(
    *,
    teacher_slide: Dict[str, Any],
    selected_template: str,
    primary_family: str,
    primary_variant: str,
    smart_layout_variant: str,
    primary_block: Dict[str, Any],
    supporting_blocks: List[Dict[str, Any]],
    composition_style: str,
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
            "supports_high_end_image": template.supports_high_end_image,
        },
        "primary_block": primary_block,
        "primary_family": primary_family,
        "primary_variant": primary_variant,
        "smart_layout_variant": smart_layout_variant,
        "supporting_blocks": supporting_blocks,
        "composition_style": composition_style,
        "image_need": image_need,
        "image_tier": image_tier,
        "layout": layout,
        "notes": [
            f"Teacher intent: {teacher_slide.get('teaching_intent', 'explain')}",
            f"Coverage scope: {teacher_slide.get('coverage_scope', 'foundation')}",
            f"Planned smart_layout variant: {smart_layout_variant or 'none'}",
            f"Composition style: {composition_style}",
            f"Layout directive: {layout}"
        ],
    }


def designer_slide_planning_v2_node(state: Dict[str, Any]) -> Dict[str, Any]:
    plans = deepcopy(state.get("plans", {}))
    sub_topics = state.get("sub_topics", [])

    # Read variety histories from state
    variant_history: List[str] = list(state.get("variant_history", []))
    layout_history: List[str] = list(state.get("layout_history", []))

    # Global research text from Tavily/Wiki retrieval — used as a fallback when
    # individual teacher slides don't carry their own research_raw_text.
    global_research_raw_text: str = str(state.get("teacher_research_raw_text") or "").strip()

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

    subtopic_name = str(
        wrapper.get("_teacher_subtopic_name")
        or next((sub.get("name") for sub in sub_topics if sub.get("id") == target_sub_id), "Subtopic")
    ).strip()

    normalized_plans: List[Dict[str, Any]] = []
    # Local copies of histories so we can track intra-subtopic variety too.
    local_variant_history = list(variant_history)
    local_layout_history = list(layout_history)
    local_composition_history: List[str] = []
    local_slv_counts: Dict[str, int] = {}

    for index, teacher_slide in enumerate(teacher_slides):
        if not isinstance(teacher_slide, dict):
            continue

        # Use target_density from new v2 fields if present, fall back to slide_density
        density = _normalize_density(
            teacher_slide.get("target_density") or teacher_slide.get("slide_density")
        )
        high_end_required = _to_bool(teacher_slide.get("high_end_image_required"), default=False)
        # Override from new v2 visual fields when present
        if _to_bool(teacher_slide.get("visual_required"), default=False) and str(teacher_slide.get("image_role", "")).strip().lower() == "content":
            high_end_required = True
        image_need, image_tier = _derive_image_policy(density, high_end_required)

        teaching_intent = str(teacher_slide.get("teaching_intent", "explain")).strip().lower()
        coverage_scope = str(teacher_slide.get("coverage_scope", "foundation")).strip().lower()
        primary_family = _derive_primary_family(teacher_slide)

        # Determine the desired smart_layout variant from intent/scope
        preferred_slvs = get_smart_layout_variant(teaching_intent, coverage_scope)
        preferred_slv = preferred_slvs[0] if preferred_slvs else "solidBoxesWithIconsInside"

        # Apply variety: pick a variant that hasn't been overused recently
        template_pref_variants = []  # will be filled after template selection
        allowed_slvs = list(
            dict.fromkeys(
                preferred_slvs
                + [
                    "ribbonFold",
                    "statsBadgeGrid",
                    "timeline",
                    "processSteps",
                    "diamondRibbon",
                    "relationshipMap",
                ]
            )
        )
        smart_layout_variant = pick_smart_layout_variant(
            preferred_slvs,
            allowed_slvs,
            local_variant_history,
        )

        # Select template candidates, passing variety history and preferred variant
        template_candidates = candidate_templates(
            primary_family=primary_family,
            image_need=image_need,
            image_tier=image_tier,
            density=density,
            variant_history=local_variant_history,
            smart_layout_variant=smart_layout_variant,
        )

        # Apply variety ranking on top
        template_candidates = rank_templates(template_candidates, variant_history=local_variant_history)

        selected_template = template_candidates[0].name if template_candidates else "Title with bullets"

        # Prefer teacher-suggested template when available and valid
        teacher_template_hint = str(teacher_slide.get("selected_template", "")).strip()
        if teacher_template_hint:
            hint_spec = get_template_spec(teacher_template_hint)
            if hint_spec.name == teacher_template_hint:  # valid template
                selected_template = teacher_template_hint

        template_spec = get_template_spec(selected_template)

        # Override to hero-capable template if high-end image required
        if image_need == "required" and template_spec.image_mode_capability not in {"hero", "content"}:
            for candidate in template_candidates:
                if candidate.supports_high_end_image or candidate.image_mode_capability == "hero":
                    selected_template = candidate.name
                    template_spec = candidate
                    break

        # Refine smart_layout_variant using template's preferred list (if specified)
        if template_spec.preferred_smart_layout_variants:
            smart_layout_variant = pick_smart_layout_variant(
                preferred_slvs,
                list(template_spec.preferred_smart_layout_variants),
                local_variant_history,
            )

        # Unify variant selection: feed the scored pick into select_primary_block so it
        # becomes the single source of truth for the final smart_layout variant.
        ordered_preferences = [smart_layout_variant] + [v for v in preferred_slvs if v != smart_layout_variant]

        # Select primary block spec matching the resolved family + variant
        debug_log = []
        primary_spec = select_primary_block(
            "smart_layout",
            density,
            image_need,
            preferred_variants=ordered_preferences,
            variant_history=local_variant_history,
            teaching_intent=teaching_intent,
            coverage_scope=coverage_scope,
            debug_log=debug_log,
        )

        # Ensure primary block family is allowed by selected template
        if template_spec.allowed_primary_families and primary_spec.family not in template_spec.allowed_primary_families:
            # Fallback: let template decide the family
            fallback_family = template_spec.allowed_primary_families[0]
            primary_spec = select_primary_block(
                fallback_family,
                density,
                image_need,
                preferred_variants=ordered_preferences,
                variant_history=local_variant_history,
                teaching_intent=teaching_intent,
                coverage_scope=coverage_scope,
                debug_log=debug_log,
            )

        # For formula slides, use formula block regardless
        if primary_family == "formula":
            primary_spec = get_block_spec("formula", "normal")
            debug_log.append("Used formula block (primary_family == 'formula')")

        # Single source of truth: the chosen spec defines the final smart_layout variant.
        actual_slv = primary_spec.smart_layout_variant
        if actual_slv:
            smart_layout_variant = actual_slv

        # Hard per-subtopic guard: use each smart_layout variant at most once.
        if primary_spec.family == "smart_layout" and local_slv_counts.get(actual_slv, 0) >= 1:
            candidate_variants: List[str] = []
            seen: set[str] = set()
            for name in (
                [preferred_slv, smart_layout_variant, "ribbonFold", "statsBadgeGrid", "diamondRibbon", "relationshipMap"]
                + _available_primary_smart_layout_variants(density)
            ):
                variant_name = str(name or "").strip()
                if not variant_name or variant_name in seen:
                    continue
                seen.add(variant_name)
                if local_slv_counts.get(variant_name, 0) >= 1:
                    continue
                candidate_variants.append(variant_name)

            if candidate_variants:
                replacement_variant = pick_smart_layout_variant(
                    preferred_slvs,
                    candidate_variants,
                    local_variant_history,
                )
                replacement_spec = get_block_spec("smart_layout", replacement_variant)
                if (
                    replacement_spec.family == "smart_layout"
                    and replacement_spec.is_primary_candidate
                    and (not replacement_spec.density_ok or density in replacement_spec.density_ok)
                ):
                    primary_spec = replacement_spec
                    actual_slv = replacement_spec.smart_layout_variant
                    if actual_slv:
                        smart_layout_variant = actual_slv

        supporting_specs = select_supporting_blocks(
            family=primary_spec.family,
            density=density,
            max_supporting_blocks=template_spec.max_supporting_blocks,
        )
        if template_spec.is_sparse:
            supporting_specs = supporting_specs[:1]

        if image_need == "forbidden":
            supporting_specs = [spec for spec in supporting_specs if not spec.has_content_image]
        elif image_tier == "hero":
            supporting_specs = [spec for spec in supporting_specs if not spec.has_content_image]

        # Avoid content-image/supporting-image collision by design.
        if image_tier in {"hero", "accent"}:
            supporting_specs = [spec for spec in supporting_specs if not spec.implies_content_image]

        layout = _choose_layout(selected_template, image_need, image_tier, density, local_layout_history, primary_spec=primary_spec)
        composition_style = _pick_composition_style(
            style_history=local_composition_history,
            template=template_spec,
            image_need=image_need,
        )

        # Update local variety histories so subsequent slides in the same subtopic
        # benefit from intra-subtopic variety enforcement.
        local_variant_history.append(selected_template)
        local_layout_history.append(layout)
        if actual_slv:
            local_variant_history.append(actual_slv)
            local_slv_counts[actual_slv] = local_slv_counts.get(actual_slv, 0) + 1
        local_composition_history.append(composition_style)

        teacher_slide_ref = str(teacher_slide.get("slide_id") or f"{target_sub_id}_t{index + 1}")

        # Build research context string for soft-grounding in generator.
        # Priority: per-slide research_raw_text → per-slide research_evidence → global retrieval.
        research_evidence = _to_list(teacher_slide.get("research_evidence"))
        research_raw_text = str(teacher_slide.get("research_raw_text") or "").strip()
        research_context = (
            research_raw_text
            or "; ".join(research_evidence[:3])
            or global_research_raw_text
        )

        normalized_plans.append(
            {
                "slide_id": teacher_slide_ref,
                "teacher_slide_ref": teacher_slide_ref,
                "debug_log": debug_log,
                "sequence_index": index,
                "title": str(teacher_slide.get("title") or f"{subtopic_name} - Slide {index + 1}").strip(),
                "objective": str(teacher_slide.get("objective") or "Explain the concept clearly.").strip(),
                "summary": str(teacher_slide.get("objective") or teacher_slide.get("summary") or "Explain the concept clearly.").strip(),
                # New v2 planning fields (pass-through)
                "intent": str(teacher_slide.get("intent", "definition")).strip().lower(),
                "content_angle": str(teacher_slide.get("content_angle", "overview")).strip().lower(),
                "coverage_contract": str(teacher_slide.get("coverage_contract", "")).strip(),
                "avoid_overlap_with": _to_list(teacher_slide.get("avoid_overlap_with")),
                "role": str(teacher_slide.get("role", "Introduce")).strip(),
                "goal": str(teacher_slide.get("goal", "")).strip(),
                "reasoning": str(teacher_slide.get("reasoning", "")).strip(),
                "visual_required": _to_bool(teacher_slide.get("visual_required"), default=False),
                "visual_type": str(teacher_slide.get("visual_type", "none")).strip().lower(),
                "image_role_v2": str(teacher_slide.get("image_role", "none")).strip().lower(),
                "target_density": str(teacher_slide.get("target_density", density)).strip().lower(),
                # Legacy fields
                "teaching_intent": teaching_intent,
                "coverage_scope": coverage_scope,
                "slide_density": density,
                "must_cover": _to_list(teacher_slide.get("must_cover")),
                "key_facts": _to_list(teacher_slide.get("key_facts")),
                "formulas": _to_list(teacher_slide.get("formulas")),
                "assessment_prompt": str(teacher_slide.get("assessment_prompt") or "").strip(),
                "research_evidence": research_evidence,
                "research_raw_text": research_raw_text,
                "research_context": research_context,
                "factual_confidence": str(teacher_slide.get("factual_confidence") or "low").strip().lower(),
                "high_end_image_required": high_end_required,
                "image_need": image_need,
                "image_tier": image_tier,
                "selected_template": selected_template,
                "selected_layout": layout,
                "primary_family": primary_spec.family,
                "primary_variant": primary_spec.variant,
                "smart_layout_variant": actual_slv,
                "composition_style": composition_style,
                "designer_blueprint": _build_designer_blueprint(
                    teacher_slide=teacher_slide,
                    selected_template=selected_template,
                    primary_family=primary_spec.family,
                    primary_variant=primary_spec.variant,
                    smart_layout_variant=actual_slv,
                    primary_block=block_to_blueprint(primary_spec),
                    supporting_blocks=[block_to_blueprint(spec) for spec in supporting_specs],
                    composition_style=composition_style,
                    image_need=image_need,
                    image_tier=image_tier,
                    layout=layout,
                ),
            }
        )

    plans[target_sub_id] = normalized_plans
    return {
        "plans": plans,
        "variant_history": local_variant_history,
        "layout_history": local_layout_history,
    }
