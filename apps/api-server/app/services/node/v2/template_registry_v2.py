from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


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


TEMPLATE_REGISTRY: Dict[str, TemplateSpec] = {
    "Title card": TemplateSpec(
        name="Title card",
        is_sparse=True,
        image_mode_capability="hero",
        image_mode_required="hero",
        max_blocks=2,
        max_supporting_blocks=1,
        allowed_primary_families=("title", "overview"),
        allowed_accent_placements=("top", "bottom", "left", "right"),
        allowed_layouts=("top", "bottom", "left", "right", "blank"),
        supports_high_end_image=True,
        density_ok=("ultra_sparse", "sparse", "balanced"),
    ),
    "Title with bullets": TemplateSpec(
        name="Title with bullets",
        is_sparse=False,
        image_mode_capability="accent",
        max_blocks=3,
        max_supporting_blocks=2,
        allowed_primary_families=("overview", "recap", "definition"),
        allowed_accent_placements=("right", "left", "top", "bottom"),
        allowed_layouts=("right", "left", "top", "bottom", "blank"),
        density_ok=("ultra_sparse", "sparse", "balanced", "standard"),
    ),
    "Title with bullets and image": TemplateSpec(
        name="Title with bullets and image",
        is_sparse=False,
        image_mode_capability="content",
        max_blocks=4,
        max_supporting_blocks=2,
        allowed_primary_families=("overview", "example", "diagram"),
        allowed_accent_placements=("right", "left"),
        allowed_layouts=("right", "left", "top", "bottom", "blank"),
        density_ok=("ultra_sparse", "sparse", "balanced"),
    ),
    "Image and text": TemplateSpec(
        name="Image and text",
        is_sparse=False,
        image_mode_capability="content",
        max_blocks=4,
        max_supporting_blocks=2,
        allowed_primary_families=("example", "diagram", "overview"),
        allowed_accent_placements=("right", "left"),
        allowed_layouts=("right", "left", "top", "bottom"),
        density_ok=("ultra_sparse", "sparse", "balanced"),
    ),
    "Text and image": TemplateSpec(
        name="Text and image",
        is_sparse=False,
        image_mode_capability="content",
        max_blocks=4,
        max_supporting_blocks=2,
        allowed_primary_families=("example", "definition", "overview"),
        allowed_accent_placements=("right", "left"),
        allowed_layouts=("right", "left", "top", "bottom"),
        density_ok=("ultra_sparse", "sparse", "balanced"),
    ),
    "Two columns": TemplateSpec(
        name="Two columns",
        is_sparse=False,
        image_mode_capability="none",
        max_blocks=3,
        max_supporting_blocks=2,
        allowed_primary_families=("comparison", "contrast"),
        allowed_accent_placements=(),
        allowed_layouts=("blank", "left", "right"),
        density_ok=("sparse", "balanced", "standard"),
    ),
    "Timeline": TemplateSpec(
        name="Timeline",
        is_sparse=False,
        image_mode_capability="accent",
        max_blocks=4,
        max_supporting_blocks=2,
        allowed_primary_families=("process", "sequence"),
        allowed_accent_placements=("top", "bottom"),
        allowed_layouts=("top", "bottom", "blank"),
        density_ok=("sparse", "balanced", "standard"),
    ),
    "Icons with text": TemplateSpec(
        name="Icons with text",
        is_sparse=False,
        image_mode_capability="accent",
        max_blocks=4,
        max_supporting_blocks=3,
        allowed_primary_families=("overview", "recap", "process"),
        allowed_accent_placements=("right", "left", "top", "bottom"),
        allowed_layouts=("right", "left", "top", "bottom", "blank"),
        density_ok=("ultra_sparse", "sparse", "balanced", "standard"),
    ),
    "Large bullet list": TemplateSpec(
        name="Large bullet list",
        is_sparse=True,
        image_mode_capability="none",
        max_blocks=2,
        max_supporting_blocks=1,
        allowed_primary_families=("recap", "overview"),
        allowed_accent_placements=(),
        allowed_layouts=("blank",),
        density_ok=("ultra_sparse", "sparse"),
    ),
    "Comparison table": TemplateSpec(
        name="Comparison table",
        is_sparse=False,
        image_mode_capability="none",
        max_blocks=2,
        max_supporting_blocks=1,
        allowed_primary_families=("comparison",),
        allowed_accent_placements=(),
        allowed_layouts=("blank", "left", "right"),
        density_ok=("balanced", "standard", "dense"),
    ),
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
    "Process arrow block": TemplateSpec(
        name="Process arrow block",
        is_sparse=False,
        image_mode_capability="accent",
        max_blocks=4,
        max_supporting_blocks=2,
        allowed_primary_families=("process",),
        allowed_accent_placements=("top", "bottom"),
        allowed_layouts=("top", "bottom", "blank"),
        density_ok=("sparse", "balanced", "standard"),
    ),
    "Cyclic process block": TemplateSpec(
        name="Cyclic process block",
        is_sparse=False,
        image_mode_capability="accent",
        max_blocks=4,
        max_supporting_blocks=2,
        allowed_primary_families=("process",),
        allowed_accent_placements=("top", "bottom"),
        allowed_layouts=("top", "bottom", "blank"),
        density_ok=("balanced", "standard", "dense"),
    ),
    "Feature showcase block": TemplateSpec(
        name="Feature showcase block",
        is_sparse=False,
        image_mode_capability="hero",
        image_mode_required="hero",
        max_blocks=4,
        max_supporting_blocks=2,
        allowed_primary_families=("overview", "example", "process"),
        allowed_accent_placements=("right", "left", "top", "bottom"),
        allowed_layouts=("right", "left", "top", "bottom", "blank"),
        supports_high_end_image=True,
        density_ok=("balanced", "standard", "dense"),
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
) -> List[TemplateSpec]:
    family = str(primary_family or "overview").strip().lower()
    need = str(image_need or "optional").strip().lower()
    tier = str(image_tier or "accent").strip().lower()
    density_key = str(density or "balanced").strip().lower()

    scored: List[Tuple[int, TemplateSpec]] = []
    for template in TEMPLATE_REGISTRY.values():
        if template.density_ok and density_key not in template.density_ok:
            continue
        if template.allowed_primary_families and family not in template.allowed_primary_families:
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

        scored.append((score, template))

    if not scored:
        return [TEMPLATE_REGISTRY["Title with bullets"], TEMPLATE_REGISTRY["Large bullet list"]]

    scored.sort(key=lambda item: (-item[0], item[1].name))
    return [item[1] for item in scored]


def template_allows_layout(template_name: str, layout: str) -> bool:
    spec = get_template_spec(template_name)
    return str(layout).strip().lower() in {value.lower() for value in spec.allowed_layouts}
