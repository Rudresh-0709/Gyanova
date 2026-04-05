"""
Dedicated v2 slide planner module.

Orchestrates:
  1. Density tier mapping (teacher brief 3-tier to engine 6-tier)
  2. Template selection with variety penalties
  3. Primary block family/variant selection with variety penalties
  4. Supporting blocks composition per template density
  5. Image layout determination with history-aware corrections
  6. Plan output compatible with generate_gyml_v2

No modifications to existing BlockSpec, TemplateSpec, or v1 logic.
Feature-flagged behind caller's discretion.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple


_COMPOSITION_STYLES: Tuple[str, ...] = (
    "primary_only",
    "context_then_primary",
    "primary_then_callout",
    "intro_then_primary",
)

try:
    from app.services.node.v2.density_mapping_v2 import map_brief_density_to_engine
    from app.services.node.v2.block_catalog_v2 import (
        BLOCK_CATALOG,
        BlockSpec,
        block_to_blueprint,
        select_primary_block,
        select_supporting_blocks,
    )
    from app.services.node.v2.template_registry_v2 import (
        TEMPLATE_REGISTRY,
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
    from app.services.node.v2.block_traits_v2 import BLOCK_TRAITS, BlockTraitsV2
    from app.services.node.v2.template_traits_v2 import TEMPLATE_TRAITS, TemplateTraitsV2
    from app.services.node.v2.image_manager_adapter_v2 import determine_image_layout_v2
except ImportError:
    from .density_mapping_v2 import map_brief_density_to_engine  # type: ignore
    from .block_catalog_v2 import (  # type: ignore
        BLOCK_CATALOG,
        BlockSpec,
        block_to_blueprint,
        select_primary_block,
        select_supporting_blocks,
    )
    from .template_registry_v2 import (  # type: ignore
        TEMPLATE_REGISTRY,
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
    from .block_traits_v2 import BLOCK_TRAITS, BlockTraitsV2  # type: ignore
    from .template_traits_v2 import TEMPLATE_TRAITS, TemplateTraitsV2  # type: ignore
    from .image_manager_adapter_v2 import determine_image_layout_v2  # type: ignore


def _to_bool(value: Any, default: bool = False) -> bool:
    """Convert value to boolean with sensible defaults."""
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
    """Convert value to list of strings."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    text = str(value).strip()
    return [text] if text else []


def _pick_composition_style(
    *,
    slide_index: int,
    template_spec: TemplateSpec,
    image_need: str,
    composition_history: List[str],
) -> str:
    """Pick a composition style with rotation and light recency balancing."""
    allowed_styles = list(_COMPOSITION_STYLES)

    if template_spec.is_sparse or image_need == "required":
        allowed_styles = [
            style
            for style in allowed_styles
            if style in {"primary_only", "context_then_primary", "intro_then_primary"}
        ]

    if not allowed_styles:
        return "primary_only"

    recent_window = composition_history[-4:]
    previous_style = composition_history[-1] if composition_history else ""

    scored: List[Tuple[int, int, int, str]] = []
    for style in allowed_styles:
        recent_count = sum(1 for token in recent_window if token == style)
        immediate_repeat = 1 if style == previous_style else 0
        # Deterministic tie-break that still rotates by slide position.
        order_offset = (allowed_styles.index(style) - (slide_index % len(allowed_styles))) % len(allowed_styles)
        scored.append((recent_count, immediate_repeat, order_offset, style))

    scored.sort(key=lambda item: (item[0], item[1], item[2]))
    return scored[0][3]


def _derive_image_policy(
    density: str,
    concept_image_required: bool,
    high_end_image_required: bool,
) -> Tuple[str, str]:
    """
    Derive image_need and image_tier from density and requirements.

    Returns:
      (image_need: "required"|"optional"|"forbidden", image_tier: "hero"|"content"|"accent"|"none")
    """
    if high_end_image_required:
        return "required", "hero"

    if concept_image_required:
        return "required", "content"

    if density in {"ultra_sparse", "sparse", "balanced"}:
        return "optional", "accent"

    return "forbidden", "none"


def _derive_primary_family(teacher_brief: Dict[str, Any]) -> str:
    """
    Derive primary block family from teacher intent and coverage scope.

    Returns primary family name safe for BLOCK_CATALOG lookup.
    """
    teaching_intent = str(teacher_brief.get("teaching_intent", "explain")).strip().lower()
    coverage_scope = str(teacher_brief.get("coverage_scope", "foundation")).strip().lower()
    formulas = _to_list(teacher_brief.get("formulas"))

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


def _select_template_with_variety(
    *,
    template_candidates: List[TemplateSpec],
    primary_family: str,
    image_need: str,
    image_tier: str,
    layout_history: List[str],
    variant_history: List[str],
    hard_rule_no_consecutive_template: bool,
) -> TemplateSpec:
    """
    Select best template from candidates using variety penalties.

    Steps:
      1. Filter by hard rule (disallow_consecutive if enabled)
      2. Score remaining by:
         - template_penalty (recent history)
         - family penalty
         - variant penalty
         - smart_layout_variant penalty
         - concept_image support (if content image required)
      3. Return lowest-penalty candidate
    """
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

        # Penalty for template recency
        penalty += template_penalty(candidate.name, layout_history, window=6)

        # Penalty for family recency
        penalty += family_penalty(primary_family, variant_history, window=6)

        # Penalty for variant recency
        penalty += variant_penalty(primary_family, "normal", variant_history, window=6)

        # Penalty for smart_layout variant recency
        image_mode = str(candidate.image_mode_capability or "").strip().lower()
        if image_mode in {"accent", "content", "hero"}:
            penalty += smart_layout_variant_penalty(image_mode, variant_history, window=6)

        # Penalize if image required but template doesn't support it
        if image_need == "required" and image_mode not in {"hero", "content"}:
            penalty += 1.5

        # Strong penalty if concept image required but template doesn't support it
        traits = TEMPLATE_TRAITS.get(candidate.name)
        if traits:
            if image_need == "required" and not traits.supports_concept_image:
                penalty += 3.0
            if image_need == "required" and traits.forbidden_if_concept_image:
                penalty += 1.0

        scored.append((penalty, candidate))

    # Sort by penalty, then name for determinism
    scored.sort(key=lambda item: (item[0], item[1].name))
    return scored[0][1] if scored else template_candidates[0]


def _select_primary_family_with_variety(
    *,
    requested_family: str,
    template_spec: TemplateSpec,
    variant_history: List[str],
    hard_rule_family_cap: bool,
) -> str:
    """
    Select best primary family from template's allowed families using variety penalties.

    Steps:
      1. Filter to template's allowed_primary_families
      2. If hard_rule_family_cap, apply hard rule (max 2 same family in last 4 slides)
      3. Score remaining by family_penalty + variant_penalty
      4. Prefer requested_family if tie
      5. Return best family name
    """
    if not template_spec.allowed_primary_families:
        return requested_family

    allowed_families = [
        str(family).strip().lower()
        for family in template_spec.allowed_primary_families
        if str(family).strip()
    ]
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
        penalty = family_penalty(family, variant_history, window=6)
        penalty += variant_penalty(family, "normal", variant_history, window=6)

        # Prefer requested family
        if family != str(requested_family or "").strip().lower():
            penalty += 0.5

        scored.append((penalty, family))

    scored.sort(
        key=lambda item: (
            item[0],
            item[1] != str(requested_family or "").strip().lower(),
            item[1],
        )
    )
    return scored[0][1] if scored else allowed_families[0]


def _compose_planned_blocks(
    *,
    template_spec: TemplateSpec,
    primary_family: str,
    primary_variant: str,
    density: str,
    image_need: str,
    image_tier: str,
) -> Tuple[BlockSpec, List[BlockSpec], bool]:
    """
    Compose primary block and supporting blocks respecting template constraints.

    Returns:
      (primary_spec, supporting_specs, has_wide_block)
    """
    # Get primary block
    primary_spec = select_primary_block(primary_family, density, image_need)

    # Validate against template's allowed_primary_families
    if (
        primary_spec.family not in template_spec.allowed_primary_families
        and template_spec.allowed_primary_families
    ):
        # Fallback to first allowed family
        primary_family = template_spec.allowed_primary_families[0]
        primary_spec = select_primary_block(primary_family, density, image_need)

    # Determine has_wide_block
    has_wide_block = primary_spec.width_class == "wide"

    # Get supporting blocks
    supporting_specs = select_supporting_blocks(
        family=primary_family,
        density=density,
        max_supporting_blocks=template_spec.max_supporting_blocks,
    )

    # Sparse templates allow only 1 supporting block
    if template_spec.is_sparse:
        supporting_specs = supporting_specs[:1]

    # Filter by image policy
    if image_need == "forbidden":
        supporting_specs = [spec for spec in supporting_specs if not spec.has_content_image]
    elif image_tier == "hero":
        supporting_specs = [spec for spec in supporting_specs if not spec.has_content_image]

    return primary_spec, supporting_specs, has_wide_block


def plan_slide_v2(
    teacher_brief: Dict[str, Any],
    state: Dict[str, Any],
    slide_index: int,
) -> Dict[str, Any]:
    """
    Plan a single v2 slide from teacher brief.

    Args:
        teacher_brief: Dict with keys:
          - density_tier: "low"|"medium"|"high" (brief teacher input)
          - concept_image_required: bool (teacher mandates concept image)
          - concept_image_prompt: str (teacher's description, optional)
          - teaching_intent: str (explain, compare, demo, etc.)
          - coverage_scope: str (foundation, mechanism, etc.)
          - title: str (slide title)
          - objective: str (slide teaching objective)
          - must_cover: List[str] (key points)
          - key_facts: List[str] (facts)
          - formulas: List[str] (formulas to show)
          - assessment_prompt: str (check understanding)
          - research_raw_text: str (research content)
          - factual_confidence: str (high/medium/low)
          - high_end_image_required: bool (require high-quality images)

        state: Dict (TutorState-like) with keys:
          - layout_history: List[str] (template|layout tokens)
          - variant_history: List[str] (family:variant + smart_layout:variant tokens)
          - v2_no_consecutive_template: bool (hard rule, default True)
          - v2_family_cap_last4: bool (hard rule, default True)

        slide_index: int (0-based position in subtopic)

    Returns:
        Dict (plan_item) compatible with generate_gyml_v2:
          - title: str
          - intent: str
          - selected_template: str
          - slide_density: str (engine token)
          - layout: str (image_layout)
          - designer_blueprint: Dict (blocks structure)
          - image_need: str
          - image_tier: str
          - primary_supports_icons: bool
          - primary_tags: List[str]
          - contentBlocks: List[Dict] (hints for generation)
          - ... (all teacher fields passed through)
    """
    # Extract histories from state
    layout_history = list(state.get("layout_history", []))
    variant_history = list(state.get("variant_history", []))
    composition_history = list(state.get("composition_history", []))
    hard_rule_no_consecutive = _to_bool(
        state.get("v2_no_consecutive_template", True), default=True
    )
    hard_rule_family_cap = _to_bool(state.get("v2_family_cap_last4", True), default=True)

    # ===== Step 1: Map density tier =====
    brief_density = str(teacher_brief.get("density_tier", "medium")).strip().lower()
    engine_density = map_brief_density_to_engine(brief_density, slide_index=slide_index)

    # ===== Step 2: Derive image policy =====
    concept_image_required = _to_bool(
        teacher_brief.get("concept_image_required"), default=False
    )
    high_end_required = _to_bool(
        teacher_brief.get("high_end_image_required"), default=False
    )
    image_need, image_tier = _derive_image_policy(
        engine_density,
        concept_image_required,
        high_end_required,
    )

    # ===== Step 3: Derive primary family from intent/scope =====
    requested_family = _derive_primary_family(teacher_brief)

    # ===== Step 4: Select template =====
    template_candidates = candidate_templates(
        primary_family=requested_family,
        image_need=image_need,
        image_tier=image_tier,
        density=engine_density,
    )

    template_spec = _select_template_with_variety(
        template_candidates=template_candidates,
        primary_family=requested_family,
        image_need=image_need,
        image_tier=image_tier,
        layout_history=layout_history,
        variant_history=variant_history,
        hard_rule_no_consecutive_template=hard_rule_no_consecutive,
    )
    selected_template = template_spec.name

    # Override if high-end required but template doesn't support
    if image_need == "required" and template_spec.image_mode_capability not in {"hero", "content"}:
        for candidate in template_candidates:
            if candidate.supports_high_end_image or candidate.image_mode_capability == "hero":
                selected_template = candidate.name
                template_spec = candidate
                break

    # ===== Step 5: Select primary family with variety =====
    primary_family = _select_primary_family_with_variety(
        requested_family=requested_family,
        template_spec=template_spec,
        variant_history=variant_history,
        hard_rule_family_cap=hard_rule_family_cap,
    )

    # ===== Step 5.5: Select composition style =====
    composition_style = _pick_composition_style(
        slide_index=slide_index,
        template_spec=template_spec,
        image_need=image_need,
        composition_history=composition_history,
    )

    # ===== Step 6: Compose primary and supporting blocks =====
    primary_spec, supporting_specs, has_wide_block = _compose_planned_blocks(
        template_spec=template_spec,
        primary_family=primary_family,
        primary_variant="normal",
        density=engine_density,
        image_need=image_need,
        image_tier=image_tier,
    )

    # Look up traits for primary block
    primary_traits = BLOCK_TRAITS.get((primary_spec.family, primary_spec.variant))
    primary_supports_icons = primary_traits.supports_icons if primary_traits else False
    primary_tags = list(primary_traits.tags) if primary_traits else []

    # ===== Step 7: Determine image layout =====
    teaching_intent = str(teacher_brief.get("teaching_intent", "explain")).strip().lower()
    image_layout = determine_image_layout_v2(
        engine_density=engine_density,
        intent=teaching_intent,
        slide_index=slide_index,
        has_wide_block=has_wide_block,
        layout_history=layout_history,
        explicit_layout=None,
    )

    # ===== Step 8: Build designer blueprint =====
    primary_blueprint = block_to_blueprint(primary_spec)
    supporting_blueprints = [block_to_blueprint(spec) for spec in supporting_specs]

    designer_blueprint = {
        "template": {
            "name": template_spec.name,
            "is_sparse": template_spec.is_sparse,
            "image_mode_capability": template_spec.image_mode_capability,
            "image_mode_required": template_spec.image_mode_required,
            "max_blocks": template_spec.max_blocks,
            "max_supporting_blocks": template_spec.max_supporting_blocks,
            "allowed_primary_families": list(template_spec.allowed_primary_families),
            "allowed_accent_placements": list(template_spec.allowed_accent_placements),
            "allowed_layouts": list(template_spec.allowed_layouts),
            "supports_high_end_image": template_spec.supports_high_end_image,
        },
        "primary_block": primary_blueprint,
        "supporting_blocks": supporting_blueprints,
        "image_need": image_need,
        "image_tier": image_tier,
        "layout": image_layout,
        "primary_family": primary_family,
        "composition_style": composition_style,
    }

    # ===== Step 9: Compose content blocks hints =====
    # Include concept_image block if required
    content_blocks_hints: List[Dict[str, Any]] = []
    if concept_image_required and concept_image_required in primary_tags:
        content_blocks_hints.append({
            "type": "image",
            "imagePrompt": str(teacher_brief.get("concept_image_prompt", "")).strip() or "Concept image for slide",
            "is_accent": False,
        })

    # ===== Step 10: Assemble plan_item output =====
    plan_item = {
        # Teacher input (pass-through)
        "title": str(teacher_brief.get("title", "Untitled Slide")).strip(),
        "objective": str(teacher_brief.get("objective", "")).strip(),
        "teaching_intent": teaching_intent,
        "coverage_scope": str(teacher_brief.get("coverage_scope", "foundation")).strip().lower(),
        "must_cover": _to_list(teacher_brief.get("must_cover")),
        "key_facts": _to_list(teacher_brief.get("key_facts")),
        "formulas": _to_list(teacher_brief.get("formulas")),
        "assessment_prompt": str(teacher_brief.get("assessment_prompt", "")).strip(),
        "research_raw_text": str(teacher_brief.get("research_raw_text", "")).strip(),
        "factual_confidence": str(teacher_brief.get("factual_confidence", "")).strip(),
        "high_end_image_required": high_end_required,
        "concept_image_required": concept_image_required,
        "concept_image_prompt": str(teacher_brief.get("concept_image_prompt", "")).strip(),
        # Planning result
        "slide_density": engine_density,
        "selected_template": selected_template,
        "layout": image_layout,
        "image_layout": image_layout,
        "intent": teaching_intent,
        "designer_blueprint": designer_blueprint,
        "composition_style": composition_style,
        "image_need": image_need,
        "image_tier": image_tier,
        "primary_supports_icons": primary_supports_icons,
        "primary_tags": primary_tags,
        "contentBlocks": content_blocks_hints,
    }

    return plan_item
