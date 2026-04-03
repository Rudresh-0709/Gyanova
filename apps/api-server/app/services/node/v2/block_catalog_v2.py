from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class BlockSpec:
    family: str
    variant: str
    width_class: str
    has_content_image: bool = False
    implies_content_image: bool = False
    density_ok: Tuple[str, ...] = ()
    is_primary_candidate: bool = True
    # For smart_layout blocks: the variant name passed to GyML renderer
    smart_layout_variant: str = ""
    # Pedagogical intents this block fits best
    intent_fit: Tuple[str, ...] = ()


BLOCK_CATALOG: Dict[Tuple[str, str], BlockSpec] = {
    # ── Title / Overview ─────────────────────────────────────────────────────
    ("title", "normal"): BlockSpec(
        family="title",
        variant="normal",
        width_class="wide",
        density_ok=("ultra_sparse", "sparse", "balanced", "standard"),
        is_primary_candidate=True,
        intent_fit=("introduce",),
    ),
    ("overview", "normal"): BlockSpec(
        family="overview",
        variant="normal",
        width_class="wide",
        density_ok=("ultra_sparse", "sparse", "balanced", "standard"),
        is_primary_candidate=True,
        intent_fit=("explain", "introduce", "list"),
    ),
    ("overview", "wide"): BlockSpec(
        family="overview",
        variant="wide",
        width_class="wide",
        density_ok=("ultra_sparse", "sparse", "balanced", "standard"),
        is_primary_candidate=True,
        intent_fit=("explain", "introduce"),
    ),
    # ── Definition ───────────────────────────────────────────────────────────
    ("definition", "normal"): BlockSpec(
        family="definition",
        variant="normal",
        width_class="wide",
        density_ok=("ultra_sparse", "sparse", "balanced"),
        is_primary_candidate=True,
        intent_fit=("explain", "introduce"),
    ),
    # ── Formula ──────────────────────────────────────────────────────────────
    ("formula", "normal"): BlockSpec(
        family="formula",
        variant="normal",
        width_class="normal",
        density_ok=("sparse", "balanced", "standard"),
        is_primary_candidate=True,
        intent_fit=("prove", "teach"),
    ),
    # ── Recap / Summary ──────────────────────────────────────────────────────
    ("recap", "normal"): BlockSpec(
        family="recap",
        variant="normal",
        width_class="normal",
        density_ok=("ultra_sparse", "sparse", "balanced"),
        is_primary_candidate=True,
        intent_fit=("summarize", "list"),
    ),
    # ── smart_layout: Bullet variants ────────────────────────────────────────
    ("smart_layout", "bigBullets"): BlockSpec(
        family="smart_layout",
        variant="bigBullets",
        width_class="wide",
        density_ok=("ultra_sparse", "sparse", "balanced", "standard"),
        is_primary_candidate=True,
        smart_layout_variant="bigBullets",
        intent_fit=("explain", "list", "introduce", "summarize"),
    ),
    ("smart_layout", "bulletIcon"): BlockSpec(
        family="smart_layout",
        variant="bulletIcon",
        width_class="wide",
        density_ok=("sparse", "balanced", "standard"),
        is_primary_candidate=True,
        smart_layout_variant="bulletIcon",
        intent_fit=("explain", "list"),
    ),
    ("smart_layout", "bulletCheck"): BlockSpec(
        family="smart_layout",
        variant="bulletCheck",
        width_class="wide",
        density_ok=("sparse", "balanced", "standard"),
        is_primary_candidate=True,
        smart_layout_variant="bulletCheck",
        intent_fit=("list", "summarize"),
    ),
    # ── smart_layout: Timeline variants ──────────────────────────────────────
    ("smart_layout", "timeline"): BlockSpec(
        family="smart_layout",
        variant="timeline",
        width_class="wide",
        density_ok=("sparse", "balanced", "standard", "dense"),
        is_primary_candidate=True,
        smart_layout_variant="timeline",
        intent_fit=("narrate", "teach", "explain"),
    ),
    ("smart_layout", "timelineIcon"): BlockSpec(
        family="smart_layout",
        variant="timelineIcon",
        width_class="wide",
        density_ok=("sparse", "balanced", "standard"),
        is_primary_candidate=True,
        smart_layout_variant="timelineIcon",
        intent_fit=("narrate", "teach"),
    ),
    ("smart_layout", "timelineHorizontal"): BlockSpec(
        family="smart_layout",
        variant="timelineHorizontal",
        width_class="wide",
        density_ok=("sparse", "balanced", "standard"),
        is_primary_candidate=True,
        smart_layout_variant="timelineHorizontal",
        intent_fit=("narrate", "explain"),
    ),
    ("smart_layout", "timelineSequential"): BlockSpec(
        family="smart_layout",
        variant="timelineSequential",
        width_class="wide",
        density_ok=("balanced", "standard", "dense"),
        is_primary_candidate=True,
        smart_layout_variant="timelineSequential",
        intent_fit=("teach", "explain"),
    ),
    # ── smart_layout: Card Grid variants ────────────────────────────────────
    ("smart_layout", "cardGrid"): BlockSpec(
        family="smart_layout",
        variant="cardGrid",
        width_class="wide",
        density_ok=("sparse", "balanced", "standard"),
        is_primary_candidate=True,
        smart_layout_variant="cardGrid",
        intent_fit=("explain", "list"),
    ),
    ("smart_layout", "cardGridIcon"): BlockSpec(
        family="smart_layout",
        variant="cardGridIcon",
        width_class="wide",
        density_ok=("sparse", "balanced", "standard"),
        is_primary_candidate=True,
        smart_layout_variant="cardGridIcon",
        intent_fit=("explain", "list", "introduce"),
    ),
    ("smart_layout", "cardGridSimple"): BlockSpec(
        family="smart_layout",
        variant="cardGridSimple",
        width_class="wide",
        density_ok=("ultra_sparse", "sparse", "balanced"),
        is_primary_candidate=True,
        smart_layout_variant="cardGridSimple",
        intent_fit=("introduce", "explain"),
    ),
    ("smart_layout", "cardGridImage"): BlockSpec(
        family="smart_layout",
        variant="cardGridImage",
        width_class="wide",
        has_content_image=True,
        implies_content_image=True,
        density_ok=("ultra_sparse", "sparse", "balanced"),
        is_primary_candidate=True,
        smart_layout_variant="cardGridImage",
        intent_fit=("introduce", "explain"),
    ),
    # ── smart_layout: Process / Steps variants ───────────────────────────────
    ("smart_layout", "processSteps"): BlockSpec(
        family="smart_layout",
        variant="processSteps",
        width_class="wide",
        density_ok=("sparse", "balanced", "standard", "dense"),
        is_primary_candidate=True,
        smart_layout_variant="processSteps",
        intent_fit=("teach", "demo", "explain"),
    ),
    ("smart_layout", "processArrow"): BlockSpec(
        family="smart_layout",
        variant="processArrow",
        width_class="wide",
        density_ok=("balanced", "standard", "dense"),
        is_primary_candidate=True,
        smart_layout_variant="processArrow",
        intent_fit=("teach", "demo"),
    ),
    ("smart_layout", "processAccordion"): BlockSpec(
        family="smart_layout",
        variant="processAccordion",
        width_class="wide",
        density_ok=("standard", "dense", "super_dense"),
        is_primary_candidate=True,
        smart_layout_variant="processAccordion",
        intent_fit=("teach", "explain"),
    ),
    # ── smart_layout: Comparison variants ───────────────────────────────────
    ("smart_layout", "comparisonProsCons"): BlockSpec(
        family="smart_layout",
        variant="comparisonProsCons",
        width_class="wide",
        density_ok=("balanced", "standard", "dense"),
        is_primary_candidate=True,
        smart_layout_variant="comparisonProsCons",
        intent_fit=("compare",),
    ),
    ("smart_layout", "comparisonBeforeAfter"): BlockSpec(
        family="smart_layout",
        variant="comparisonBeforeAfter",
        width_class="wide",
        density_ok=("balanced", "standard"),
        is_primary_candidate=True,
        smart_layout_variant="comparisonBeforeAfter",
        intent_fit=("compare",),
    ),
    # ── smart_layout: Stats variants ────────────────────────────────────────
    ("smart_layout", "stats"): BlockSpec(
        family="smart_layout",
        variant="stats",
        width_class="wide",
        density_ok=("sparse", "balanced", "standard"),
        is_primary_candidate=True,
        smart_layout_variant="stats",
        intent_fit=("prove", "explain"),
    ),
    ("smart_layout", "statsComparison"): BlockSpec(
        family="smart_layout",
        variant="statsComparison",
        width_class="wide",
        density_ok=("balanced", "standard"),
        is_primary_candidate=True,
        smart_layout_variant="statsComparison",
        intent_fit=("compare", "prove"),
    ),
    # ── Legacy family aliases (map to smart_layout internally) ────────────────
    ("process", "normal"): BlockSpec(
        family="process",
        variant="normal",
        width_class="wide",
        density_ok=("sparse", "balanced", "standard", "dense"),
        is_primary_candidate=True,
        smart_layout_variant="processSteps",
        intent_fit=("teach", "demo", "explain"),
    ),
    ("process", "wide"): BlockSpec(
        family="process",
        variant="wide",
        width_class="wide",
        density_ok=("balanced", "standard", "dense"),
        is_primary_candidate=True,
        smart_layout_variant="processArrow",
        intent_fit=("teach", "demo"),
    ),
    ("comparison", "normal"): BlockSpec(
        family="comparison",
        variant="normal",
        width_class="wide",
        density_ok=("balanced", "standard", "dense"),
        is_primary_candidate=True,
        smart_layout_variant="comparisonProsCons",
        intent_fit=("compare",),
    ),
    ("comparison", "wide"): BlockSpec(
        family="comparison",
        variant="wide",
        width_class="wide",
        density_ok=("standard", "dense"),
        is_primary_candidate=True,
        smart_layout_variant="comparisonProsCons",
        intent_fit=("compare",),
    ),
    # ── Supporting (non-primary) blocks ──────────────────────────────────────
    ("supporting_text", "normal"): BlockSpec(
        family="supporting_text",
        variant="normal",
        width_class="normal",
        density_ok=("ultra_sparse", "sparse", "balanced", "standard", "dense"),
        is_primary_candidate=False,
    ),
    ("supporting_callout", "normal"): BlockSpec(
        family="supporting_callout",
        variant="normal",
        width_class="normal",
        density_ok=("sparse", "balanced", "standard"),
        is_primary_candidate=False,
    ),
    ("supporting_image", "normal"): BlockSpec(
        family="supporting_image",
        variant="normal",
        width_class="normal",
        has_content_image=True,
        implies_content_image=True,
        density_ok=("ultra_sparse", "sparse", "balanced"),
        is_primary_candidate=False,
    ),
    ("concept_image", "normal"): BlockSpec(
        family="concept_image",
        variant="normal",
        width_class="normal",
        has_content_image=True,
        implies_content_image=True,
        density_ok=("ultra_sparse", "sparse", "balanced"),
        is_primary_candidate=True,
    ),
}

# Preferred smart_layout variant per (teaching_intent, coverage_scope) pair.
# Used by the planner to pick a good default when the family is "smart_layout".
_INTENT_SCOPE_TO_VARIANT: Dict[Tuple[str, str], str] = {
    ("narrate", "sequence"): "timeline",
    ("narrate", "mechanism"): "timelineSequential",
    ("narrate", "foundation"): "timeline",
    ("teach", "mechanism"): "processSteps",
    ("teach", "sequence"): "processSteps",
    ("teach", "application"): "processArrow",
    ("demo", "mechanism"): "processArrow",
    ("demo", "application"): "processAccordion",
    ("compare", "comparison"): "comparisonProsCons",
    ("compare", "foundation"): "comparisonBeforeAfter",
    ("explain", "foundation"): "bigBullets",
    ("explain", "overview"): "cardGridIcon",
    ("explain", "application"): "cardGrid",
    ("list", "foundation"): "bigBullets",
    ("list", "overview"): "bulletIcon",
    ("introduce", "foundation"): "cardGridSimple",
    ("introduce", "overview"): "cardGridIcon",
    ("summarize", "reinforcement"): "bulletCheck",
    ("summarize", "foundation"): "bigBullets",
    ("prove", "data"): "stats",
    ("prove", "comparison"): "statsComparison",
}

# Fallback variant when intent/scope combination is not found.
_DEFAULT_SMART_LAYOUT_VARIANT = "bigBullets"


def get_smart_layout_variant(teaching_intent: str, coverage_scope: str) -> str:
    """Return the preferred smart_layout variant for a given intent/scope pair."""
    intent = str(teaching_intent or "explain").strip().lower()
    scope = str(coverage_scope or "foundation").strip().lower()
    return _INTENT_SCOPE_TO_VARIANT.get((intent, scope), _DEFAULT_SMART_LAYOUT_VARIANT)


def get_block_spec(family: str, variant: str = "normal") -> BlockSpec:
    return BLOCK_CATALOG.get((str(family).strip().lower(), str(variant).strip().lower())) or BLOCK_CATALOG[("overview", "normal")]


def select_primary_block(
    family: str,
    density: str,
    image_need: str,
    variant_history: Optional[List[str]] = None,
    teaching_intent: str = "explain",
    coverage_scope: str = "foundation",
) -> BlockSpec:
    """Select the best primary BlockSpec, applying history-based anti-repetition."""
    family_key = str(family or "smart_layout").strip().lower()
    density_key = str(density or "balanced").strip().lower()
    image_need_key = str(image_need or "optional").strip().lower()
    recent_variants = set((variant_history or [])[-4:])

    # Build candidates that match density and are primary candidates
    candidates = [spec for spec in BLOCK_CATALOG.values() if spec.is_primary_candidate]
    candidates = [spec for spec in candidates if not spec.density_ok or density_key in spec.density_ok]

    # Filter by family; if family is explicitly smart_layout, prefer those entries
    if family_key == "smart_layout":
        family_candidates = [spec for spec in candidates if spec.family == "smart_layout"]
        if not family_candidates:
            family_candidates = candidates
    else:
        family_candidates = [spec for spec in candidates if spec.family == family_key]
        if not family_candidates:
            # Expand to smart_layout family as fallback
            family_candidates = [spec for spec in candidates if spec.family == "smart_layout"]
        if not family_candidates:
            family_candidates = [spec for spec in candidates if spec.family in {"overview", family_key}]
        if not family_candidates:
            family_candidates = candidates

    if not family_candidates:
        return get_block_spec("overview", "normal")

    # For smart_layout family, pick the best variant based on intent/scope
    if family_key in {"smart_layout", "process", "comparison", "recap", "overview"}:
        preferred_variant = get_smart_layout_variant(teaching_intent, coverage_scope)
        # Try preferred variant first (non-repeated)
        preferred = [
            spec for spec in family_candidates
            if spec.smart_layout_variant == preferred_variant
            and spec.smart_layout_variant not in recent_variants
        ]
        if preferred:
            return preferred[0]
        # Preferred variant was recently used – try any non-repeated smart_layout variant
        non_repeated = [
            spec for spec in family_candidates
            if spec.smart_layout_variant not in recent_variants
        ]
        if non_repeated:
            non_repeated.sort(key=lambda s: (s.family != "smart_layout", s.variant))
            return non_repeated[0]

    # If image required and family is title-like, prefer content-image-aware spec
    if image_need_key == "required" and family_key in {"overview", "title"}:
        for candidate in family_candidates:
            if candidate.family in {"overview", "title"}:
                return candidate

    # Sort: prefer smart_layout family, then preferred variant match
    family_candidates.sort(key=lambda spec: (
        spec.family != "smart_layout",
        spec.family != family_key,
        spec.variant not in {get_smart_layout_variant(teaching_intent, coverage_scope)},
        spec.family,
        spec.variant,
    ))
    return family_candidates[0]


def select_supporting_blocks(
    *,
    family: str,
    density: str,
    max_supporting_blocks: int,
) -> List[BlockSpec]:
    density_key = str(density or "balanced").strip().lower()
    candidates = [
        spec
        for spec in BLOCK_CATALOG.values()
        if not spec.is_primary_candidate and (not spec.density_ok or density_key in spec.density_ok)
    ]
    candidates.sort(key=lambda spec: (spec.family, spec.variant))
    return candidates[: max(0, int(max_supporting_blocks))]


def block_to_blueprint(block: BlockSpec) -> Dict[str, object]:
    return {
        "family": block.family,
        "variant": block.variant,
        "width_class": block.width_class,
        "has_content_image": block.has_content_image,
        "implies_content_image": block.implies_content_image,
        "density_ok": list(block.density_ok),
        "is_primary_candidate": block.is_primary_candidate,
        "smart_layout_variant": block.smart_layout_variant,
        "intent_fit": list(block.intent_fit),
    }
