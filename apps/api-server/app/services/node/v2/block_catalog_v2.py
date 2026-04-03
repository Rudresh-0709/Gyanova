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


BLOCK_CATALOG: Dict[Tuple[str, str], BlockSpec] = {
    ("title", "normal"): BlockSpec(
        family="title",
        variant="normal",
        width_class="wide",
        density_ok=("ultra_sparse", "sparse", "balanced", "standard"),
        is_primary_candidate=True,
    ),
    ("overview", "normal"): BlockSpec(
        family="overview",
        variant="normal",
        width_class="wide",
        density_ok=("ultra_sparse", "sparse", "balanced", "standard"),
        is_primary_candidate=True,
    ),
    ("overview", "wide"): BlockSpec(
        family="overview",
        variant="wide",
        width_class="wide",
        density_ok=("ultra_sparse", "sparse", "balanced", "standard"),
        is_primary_candidate=True,
    ),
    ("definition", "normal"): BlockSpec(
        family="definition",
        variant="normal",
        width_class="wide",
        density_ok=("ultra_sparse", "sparse", "balanced"),
        is_primary_candidate=True,
    ),
    ("process", "normal"): BlockSpec(
        family="process",
        variant="normal",
        width_class="wide",
        density_ok=("sparse", "balanced", "standard", "dense"),
        is_primary_candidate=True,
    ),
    ("process", "wide"): BlockSpec(
        family="process",
        variant="wide",
        width_class="wide",
        density_ok=("balanced", "standard", "dense"),
        is_primary_candidate=True,
    ),
    ("comparison", "normal"): BlockSpec(
        family="comparison",
        variant="normal",
        width_class="wide",
        density_ok=("balanced", "standard", "dense"),
        is_primary_candidate=True,
    ),
    ("comparison", "wide"): BlockSpec(
        family="comparison",
        variant="wide",
        width_class="wide",
        density_ok=("standard", "dense"),
        is_primary_candidate=True,
    ),
    ("formula", "normal"): BlockSpec(
        family="formula",
        variant="normal",
        width_class="normal",
        density_ok=("sparse", "balanced", "standard"),
        is_primary_candidate=True,
    ),
    ("recap", "normal"): BlockSpec(
        family="recap",
        variant="normal",
        width_class="normal",
        density_ok=("ultra_sparse", "sparse", "balanced"),
        is_primary_candidate=True,
    ),
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
}


def get_block_spec(family: str, variant: str = "normal") -> BlockSpec:
    return BLOCK_CATALOG.get((str(family).strip().lower(), str(variant).strip().lower())) or BLOCK_CATALOG[("overview", "normal")]


def select_primary_block(family: str, density: str, image_need: str) -> BlockSpec:
    family_key = str(family or "overview").strip().lower()
    density_key = str(density or "balanced").strip().lower()
    image_need_key = str(image_need or "optional").strip().lower()

    candidates = [spec for spec in BLOCK_CATALOG.values() if spec.is_primary_candidate]
    candidates = [spec for spec in candidates if spec.family == family_key or family_key in {"overview", "title"} or spec.family in {"overview", family_key}]
    candidates = [spec for spec in candidates if not spec.density_ok or density_key in spec.density_ok]

    if not candidates:
        return get_block_spec("overview", "normal")

    candidates.sort(key=lambda spec: (spec.family != family_key, spec.variant != "wide", spec.width_class != "wide", spec.family, spec.variant))

    if image_need_key == "required" and family_key in {"overview", "title"}:
        for candidate in candidates:
            if candidate.family in {"overview", "title"}:
                return candidate

    return candidates[0]


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
    }
