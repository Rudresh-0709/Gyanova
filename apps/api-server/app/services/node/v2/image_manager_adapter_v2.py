from __future__ import annotations

try:
    from app.services.node.slides.gyml.image_manager import ImageManager
except ImportError:
    from ..slides.gyml.image_manager import ImageManager  # type: ignore


_DENSITY_TO_FLOAT = {
    "ultra_sparse": 0.25,
    "sparse": 0.45,
    "balanced": 0.65,
    "standard": 0.90,
    "dense": 1.05,
    "super_dense": 1.25,
}


def _normalize_history_layout(token: str) -> str:
    value = str(token or "").strip().lower()
    if not value:
        return ""
    if "|" in value:
        parts = value.split("|", 1)
        return str(parts[1]).strip().lower()
    return value


def determine_image_layout_v2(
    engine_density: str,
    intent: str,
    slide_index: int,
    has_wide_block: bool,
    block_spec=None,
    layout_history: list[str] | None = None,
    explicit_layout: str | None = None,
    allowed_layouts: list[str] | tuple[str, ...] | None = None,
) -> str:
    density_key = str(engine_density or "balanced").strip().lower()
    mapped_float = _DENSITY_TO_FLOAT.get(density_key, _DENSITY_TO_FLOAT["balanced"])

    # Tier 1: Use block's explicit supported_layouts if populated
    if block_spec and block_spec.supported_layouts:
        width_allowed = list(block_spec.supported_layouts)
    # Tier 2: Fall back to width_class heuristic for un-audited blocks  
    elif has_wide_block:
        width_allowed = ["top", "bottom", "blank"]
    # Tier 3: No width constraint
    else:
        width_allowed = ["left", "right", "top", "bottom", "blank"]

    # Intersect with template constraints if provided
    effective_allowed = width_allowed
    if allowed_layouts:
        template_allowed = [str(l).strip().lower() for l in allowed_layouts]
        intersection = [ly for ly in width_allowed if ly in template_allowed]
        if intersection:
            effective_allowed = intersection
        else:
            # If intersection is empty (mismatch between template and width rule),
            # default to the width-based rule as the primary visual constraint.
            effective_allowed = width_allowed

    raw_result = ImageManager.determine_placement(
        slide_density=mapped_float,
        has_user_image=False,
        intent=intent,
        explicit_layout=explicit_layout,
        slide_index=slide_index,
        has_wide_block=has_wide_block,
    )

    raw_result = str(raw_result or "blank").strip().lower()

    # Apply history-based variety/flipping
    normalized_history = [
        _normalize_history_layout(item)
        for item in list(layout_history or [])
        if str(item or "").strip()
    ]
    if normalized_history:
        last_layout = normalized_history[-1]
        if raw_result == last_layout:
            flip_map = {
                "left": "right",
                "right": "left",
                "top": "bottom",
                "bottom": "top",
                "blank": "left" if not has_wide_block else "top",
            }
            raw_result = flip_map.get(raw_result, raw_result)

    # Final enforcement of effective_allowed
    if raw_result not in effective_allowed:
        # Fallback strategy: try to find a similar one in effective_allowed
        if raw_result in ("left", "right"):
            for fb in ["top", "bottom", "blank"]:
                if fb in effective_allowed:
                    return fb
        elif raw_result in ("top", "bottom"):
            for fb in ["left", "right", "blank"]:
                if fb in effective_allowed:
                    return fb
        
        return effective_allowed[0]

    return raw_result
