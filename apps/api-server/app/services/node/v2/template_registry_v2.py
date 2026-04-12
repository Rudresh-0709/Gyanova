from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

# Each slide appends ~2 tokens to variant_history (template + smart_layout variant).
# Window of 10 covers last ~5 slides.
_VARIANT_HISTORY_WINDOW: int = 10


@dataclass(frozen=True)
class TemplateSpec:
    name: str
    is_sparse: bool
    image_mode_capability: str
    image_mode_required: Optional[str] = None
    max_blocks: int = 4
    max_supporting_blocks: int = 2
    allowed_primary_families: Tuple[str, ...] = ()
    allowed_accent_placements: Tuple[str, ...] = ()
    allowed_layouts: Tuple[str, ...] = ("top", "bottom", "left", "right", "blank")
    supports_high_end_image: bool = False
    density_ok: Tuple[str, ...] = ()
    # Which smart_layout variants this template is designed for (empty = any)
    preferred_smart_layout_variants: Tuple[str, ...] = ()


TEMPLATE_REGISTRY: Dict[str, TemplateSpec] = {
    # ── Hero / Title ──────────────────────────────────────────────────────────
    "Title card": TemplateSpec(
        name="Title card",
        is_sparse=True,
        image_mode_capability="hero",
        image_mode_required="hero",
        max_blocks=2,
        max_supporting_blocks=1,
        allowed_primary_families=("title", "overview", "smart_layout"),
        allowed_accent_placements=("top", "bottom", "left", "right"),
        allowed_layouts=("top", "bottom", "left", "right", "blank"),
        supports_high_end_image=True,
        density_ok=("ultra_sparse", "sparse", "balanced"),
    ),
    # ── Bullets / Overview ────────────────────────────────────────────────────
    "Title with bullets": TemplateSpec(
        name="Title with bullets",
        is_sparse=False,
        image_mode_capability="accent",
        max_blocks=3,
        max_supporting_blocks=2,
        allowed_primary_families=("overview", "recap", "definition", "smart_layout"),
        allowed_accent_placements=("right", "left", "top", "bottom"),
        allowed_layouts=("right", "left", "top", "bottom", "blank"),
        density_ok=("ultra_sparse", "sparse", "balanced", "standard"),
        preferred_smart_layout_variants=("bigBullets", "bulletIcon", "bulletCheck"),
    ),
    "Title with bullets and image": TemplateSpec(
        name="Title with bullets and image",
        is_sparse=False,
        image_mode_capability="content",
        max_blocks=4,
        max_supporting_blocks=2,
        allowed_primary_families=("overview", "example", "diagram", "smart_layout"),
        allowed_accent_placements=("right", "left"),
        allowed_layouts=("right", "left", "top", "bottom", "blank"),
        density_ok=("ultra_sparse", "sparse", "balanced"),
        preferred_smart_layout_variants=("bigBullets", "cardGridSimple"),
    ),
    # ── Image + Text ──────────────────────────────────────────────────────────
    "Image and text": TemplateSpec(
        name="Image and text",
        is_sparse=False,
        image_mode_capability="content",
        max_blocks=4,
        max_supporting_blocks=2,
        allowed_primary_families=("example", "diagram", "overview", "smart_layout"),
        allowed_accent_placements=("right", "left"),
        allowed_layouts=("right", "left", "top", "bottom"),
        density_ok=("ultra_sparse", "sparse", "balanced"),
        preferred_smart_layout_variants=("bigBullets", "cardGridSimple", "cardGridImage"),
    ),
    "Text and image": TemplateSpec(
        name="Text and image",
        is_sparse=False,
        image_mode_capability="content",
        max_blocks=4,
        max_supporting_blocks=2,
        allowed_primary_families=("example", "definition", "overview", "smart_layout"),
        allowed_accent_placements=("right", "left"),
        allowed_layouts=("right", "left", "top", "bottom"),
        density_ok=("ultra_sparse", "sparse", "balanced"),
        preferred_smart_layout_variants=("bigBullets", "cardGridSimple"),
    ),
    # ── Two-Column / Comparison ───────────────────────────────────────────────
    "Two columns": TemplateSpec(
        name="Two columns",
        is_sparse=False,
        image_mode_capability="none",
        max_blocks=3,
        max_supporting_blocks=2,
        allowed_primary_families=("comparison", "contrast", "smart_layout"),
        allowed_accent_placements=(),
        allowed_layouts=("blank", "left", "right"),
        density_ok=("sparse", "balanced", "standard"),
        preferred_smart_layout_variants=("comparisonProsCons", "comparisonBeforeAfter"),
    ),
    "Comparison table": TemplateSpec(
        name="Comparison table",
        is_sparse=False,
        image_mode_capability="none",
        max_blocks=2,
        max_supporting_blocks=1,
        allowed_primary_families=("comparison", "smart_layout"),
        allowed_accent_placements=(),
        allowed_layouts=("blank", "left", "right"),
        density_ok=("balanced", "standard", "dense"),
        preferred_smart_layout_variants=("comparisonProsCons", "comparisonBeforeAfter", "statsComparison", "relationshipMap", "statsBadgeGrid", "diamondRibbon", "diamondHub"),
    ),
    # ── Timeline ──────────────────────────────────────────────────────────────
    "Timeline": TemplateSpec(
        name="Timeline",
        is_sparse=False,
        image_mode_capability="accent",
        max_blocks=4,
        max_supporting_blocks=2,
        allowed_primary_families=("process", "sequence", "smart_layout"),
        allowed_accent_placements=("top", "bottom"),
        allowed_layouts=("top", "bottom", "blank"),
        density_ok=("sparse", "balanced", "standard"),
        preferred_smart_layout_variants=("timeline", "timelineIcon", "timelineHorizontal", "timelineSequential"),
    ),
    # ── Icon / Card layouts ───────────────────────────────────────────────────
    "Icons with text": TemplateSpec(
        name="Icons with text",
        is_sparse=False,
        image_mode_capability="accent",
        max_blocks=4,
        max_supporting_blocks=3,
        allowed_primary_families=("overview", "recap", "process", "smart_layout"),
        allowed_accent_placements=("right", "left", "top", "bottom"),
        allowed_layouts=("right", "left", "top", "bottom", "blank"),
        density_ok=("ultra_sparse", "sparse", "balanced", "standard"),
        preferred_smart_layout_variants=("cardGridIcon", "bulletIcon", "processSteps", "ribbonFold", "cardGridDiamond"),
    ),
    "Card grid": TemplateSpec(
        name="Card grid",
        is_sparse=False,
        image_mode_capability="accent",
        max_blocks=4,
        max_supporting_blocks=2,
        allowed_primary_families=("overview", "example", "smart_layout"),
        allowed_accent_placements=("top", "bottom"),
        allowed_layouts=("top", "bottom", "blank"),
        density_ok=("sparse", "balanced", "standard"),
        preferred_smart_layout_variants=("cardGrid", "cardGridIcon", "cardGridSimple", "cardGridDiamond"),
    ),
    "Card grid with image": TemplateSpec(
        name="Card grid with image",
        is_sparse=False,
        image_mode_capability="content",
        max_blocks=4,
        max_supporting_blocks=2,
        allowed_primary_families=("overview", "example", "smart_layout"),
        allowed_accent_placements=("top", "bottom"),
        allowed_layouts=("top", "bottom", "blank"),
        density_ok=("ultra_sparse", "sparse", "balanced"),
        preferred_smart_layout_variants=("cardGridImage", "cardGridIcon"),
    ),
    # ── Process ───────────────────────────────────────────────────────────────
    "Process arrow block": TemplateSpec(
        name="Process arrow block",
        is_sparse=False,
        image_mode_capability="accent",
        max_blocks=4,
        max_supporting_blocks=2,
        allowed_primary_families=("process", "smart_layout"),
        allowed_accent_placements=("top", "bottom"),
        allowed_layouts=("top", "bottom", "blank"),
        density_ok=("sparse", "balanced", "standard"),
        preferred_smart_layout_variants=("processArrow", "processSteps"),
    ),
    "Process steps": TemplateSpec(
        name="Process steps",
        is_sparse=False,
        image_mode_capability="accent",
        max_blocks=4,
        max_supporting_blocks=2,
        allowed_primary_families=("process", "smart_layout"),
        allowed_accent_placements=("top", "bottom"),
        allowed_layouts=("top", "bottom", "blank"),
        density_ok=("sparse", "balanced", "standard", "dense"),
        preferred_smart_layout_variants=("processSteps", "processArrow", "processAccordion", "relationshipMap", "diamondRibbon", "diamondHub"),
    ),
    "Cyclic process block": TemplateSpec(
        name="Cyclic process block",
        is_sparse=False,
        image_mode_capability="accent",
        max_blocks=4,
        max_supporting_blocks=2,
        allowed_primary_families=("process", "smart_layout"),
        allowed_accent_placements=("top", "bottom"),
        allowed_layouts=("top", "bottom", "blank"),
        density_ok=("balanced", "standard", "dense"),
        preferred_smart_layout_variants=("processSteps",),
    ),
    # ── Lists ─────────────────────────────────────────────────────────────────
    "Large bullet list": TemplateSpec(
        name="Large bullet list",
        is_sparse=True,
        image_mode_capability="none",
        max_blocks=2,
        max_supporting_blocks=1,
        allowed_primary_families=("recap", "overview", "smart_layout"),
        allowed_accent_placements=(),
        allowed_layouts=("blank",),
        density_ok=("ultra_sparse", "sparse"),
        preferred_smart_layout_variants=("bigBullets", "bulletCheck", "bulletIcon"),
    ),
    # ── Formula ───────────────────────────────────────────────────────────────
    "Formula block": TemplateSpec(
        name="Formula block",
        is_sparse=True,
        image_mode_capability="none",
        max_blocks=2,
        max_supporting_blocks=1,
        allowed_primary_families=("formula",),
        allowed_accent_placements=(),
        allowed_layouts=("blank",),
        density_ok=("sparse", "balanced", "standard"),
    ),
    # ── Feature Showcase ──────────────────────────────────────────────────────
    "Feature showcase block": TemplateSpec(
        name="Feature showcase block",
        is_sparse=False,
        image_mode_capability="hero",
        image_mode_required="hero",
        max_blocks=4,
        max_supporting_blocks=2,
        allowed_primary_families=("overview", "example", "process", "smart_layout"),
        allowed_accent_placements=("right", "left", "top", "bottom"),
        allowed_layouts=("right", "left", "top", "bottom", "blank"),
        supports_high_end_image=True,
        density_ok=("balanced", "standard", "dense"),
        preferred_smart_layout_variants=("cardGridIcon", "processSteps", "bigBullets", "relationshipMap", "ribbonFold", "diamondRibbon", "diamondHub"),
    ),
    # ── Stats / Data ──────────────────────────────────────────────────────────
    "Stats block": TemplateSpec(
        name="Stats block",
        is_sparse=False,
        image_mode_capability="accent",
        max_blocks=3,
        max_supporting_blocks=2,
        allowed_primary_families=("smart_layout",),
        allowed_accent_placements=("top", "bottom"),
        allowed_layouts=("top", "bottom", "blank"),
        density_ok=("sparse", "balanced", "standard"),
        preferred_smart_layout_variants=("stats", "statsComparison", "statsBadgeGrid"),
    ),
}


def get_template_spec(template_name: str) -> TemplateSpec:
    template = TEMPLATE_REGISTRY.get(str(template_name).strip())
    if template is not None:
        return template
    return TEMPLATE_REGISTRY["Title with bullets"]


def candidate_templates(
    *,
    primary_family: str,
    image_need: str,
    image_tier: str,
    density: str,
    variant_history: Optional[List[str]] = None,
    smart_layout_variant: str = "",
) -> List[TemplateSpec]:
    family = str(primary_family or "smart_layout").strip().lower()
    need = str(image_need or "optional").strip().lower()
    tier = str(image_tier or "accent").strip().lower()
    density_key = str(density or "balanced").strip().lower()
    recent_templates = set((variant_history or [])[-_VARIANT_HISTORY_WINDOW:])
    preferred_slv = str(smart_layout_variant or "").strip()

    scored: List[Tuple[int, TemplateSpec]] = []
    for template in TEMPLATE_REGISTRY.values():
        if template.density_ok and density_key not in template.density_ok:
            continue
        # Family filter: accept templates that allow the requested family OR smart_layout
        if template.allowed_primary_families:
            if family not in template.allowed_primary_families and "smart_layout" not in template.allowed_primary_families:
                continue

        score = 0
        if need == "required" and template.image_mode_capability == tier:
            score += 50
        elif need == "optional" and template.image_mode_capability in {tier, "none", "accent"}:
            score += 25
            if tier == "accent" and template.image_mode_capability == "accent":
                score += 15
            if tier == "hero" and template.image_mode_capability == "hero":
                score += 15
        elif need == "forbidden" and template.image_mode_capability == "none":
            score += 50

        if template.image_mode_required == tier:
            score += 20
        if template.is_sparse and density_key in {"ultra_sparse", "sparse"}:
            score += 10
        if not template.is_sparse and density_key in {"balanced", "standard", "dense"}:
            score += 8
        if template.supports_high_end_image and tier == "hero":
            score += 20

        # Bonus: template is specifically designed for the requested smart_layout variant
        if preferred_slv and template.preferred_smart_layout_variants and preferred_slv in template.preferred_smart_layout_variants:
            score += 30
        elif preferred_slv and template.preferred_smart_layout_variants and preferred_slv not in template.preferred_smart_layout_variants:
            # Penalty: template has a specific variant list but requested variant isn't in it
            score -= 25

        # Bonus: family explicitly listed (not just via smart_layout catch-all)
        if family in template.allowed_primary_families:
            score += 10

        # Penalty: template was recently used (variety)
        if template.name in recent_templates:
            score -= 20

        scored.append((score, template))

    if not scored:
        return [TEMPLATE_REGISTRY["Title with bullets"], TEMPLATE_REGISTRY["Large bullet list"]]

    scored.sort(key=lambda item: (-item[0], item[1].name))
    return [item[1] for item in scored]


def template_allows_layout(template_name: str, layout: str) -> bool:
    spec = get_template_spec(template_name)
    return str(layout).strip().lower() in {value.lower() for value in spec.allowed_layouts}
